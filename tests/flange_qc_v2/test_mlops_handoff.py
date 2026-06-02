import json
import unittest
from pathlib import Path

from apps.flange_qc_v2.domain import ValidationError
from apps.flange_qc_v2.mlops_handoff import (
    DatasetHandoffManifest,
    EvaluationHandoffReport,
    validate_evaluation_against_dataset,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
DATASET_SCHEMA = REPO_ROOT / "contracts/flange_qc_v2/mlops/dataset_manifest.schema.json"
EVALUATION_SCHEMA = REPO_ROOT / "contracts/flange_qc_v2/mlops/evaluation_report.schema.json"


def dataset_payload(**overrides):
    payload = {
        "contract_version": "mlops.dataset_manifest.v1",
        "dataset_snapshot_ref": "dataset://flange-qc-v2/shadow/snapshot-2026-06-02",
        "entity_grain": "frame",
        "storage_ref": "dataset://flange-qc-v2/sanitized/snapshot-2026-06-02",
        "labels": ["punch_mark", "corner_mark"],
        "split_policy": {
            "method": "time_blocked",
            "leakage_guard": "point_in_time",
            "label_timestamp_field": "label_created_at",
            "feature_timestamp_field": "frame_captured_at",
        },
        "split_counts": {"train": 100, "validation": 25, "test": 25},
        "privacy_class": "sanitized_metadata_only",
        "contains_pii": False,
        "contains_customer_data": False,
        "raw_media_included": False,
        "approval_status": "candidate",
        "production_authority": False,
        "source_ref": "https://github.com/namlogan/MIL/issues/101",
    }
    payload.update(overrides)
    return payload


def evaluation_payload(**overrides):
    payload = {
        "contract_version": "mlops.evaluation_report.v1",
        "model_ref": "registry://flange-qc-v2/detector/punch-mark/2026-06-02",
        "dataset_snapshot_ref": "dataset://flange-qc-v2/shadow/snapshot-2026-06-02",
        "metrics": {"precision": 0.92, "recall": 0.81, "f1": 0.86},
        "slice_metrics": [
            {"slice": "punch_mark", "precision": 0.91, "recall": 0.8, "support": 100},
            {"slice": "corner_mark", "precision": 0.95, "recall": 0.84, "support": 50},
        ],
        "latency_ms_p95": 75.0,
        "latency_budget_ms_p95": 150.0,
        "approval_status": "candidate",
        "promotion_decision": "not_approved",
        "production_authority": False,
        "source_ref": "https://github.com/namlogan/MIL/issues/101",
    }
    payload.update(overrides)
    return payload


class MlopsHandoffSchemaTests(unittest.TestCase):
    def test_schemas_document_dataset_and_eval_contracts(self) -> None:
        dataset_schema = json.loads(DATASET_SCHEMA.read_text(encoding="utf-8"))
        evaluation_schema = json.loads(EVALUATION_SCHEMA.read_text(encoding="utf-8"))

        self.assertEqual(dataset_schema["title"], "FLANGE QC V2 MLOps Dataset Manifest")
        self.assertEqual(dataset_schema["properties"]["contract_version"]["const"], "mlops.dataset_manifest.v1")
        self.assertEqual(dataset_schema["properties"]["production_authority"]["const"], False)
        self.assertEqual(evaluation_schema["title"], "FLANGE QC V2 MLOps Evaluation Report")
        self.assertEqual(evaluation_schema["properties"]["contract_version"]["const"], "mlops.evaluation_report.v1")
        self.assertEqual(evaluation_schema["properties"]["production_authority"]["const"], False)


class DatasetHandoffManifestTests(unittest.TestCase):
    def test_valid_dataset_manifest_accepts_metadata_only_handoff(self) -> None:
        manifest = DatasetHandoffManifest.from_payload(dataset_payload())

        self.assertEqual(manifest.contract_version, "mlops.dataset_manifest.v1")
        self.assertEqual(manifest.dataset_snapshot_ref, "dataset://flange-qc-v2/shadow/snapshot-2026-06-02")
        self.assertEqual(manifest.labels, ("punch_mark", "corner_mark"))
        self.assertEqual(manifest.split_counts["train"], 100)
        self.assertFalse(manifest.production_authority)

    def test_dataset_manifest_rejects_raw_media_storage_path(self) -> None:
        with self.assertRaisesRegex(ValidationError, "storage_ref must use an approved dataset storage reference"):
            DatasetHandoffManifest.from_payload(dataset_payload(storage_ref="file:///factory/raw/frame-001.jpg"))

    def test_dataset_manifest_rejects_pii_or_customer_data_flags(self) -> None:
        with self.assertRaisesRegex(ValidationError, "dataset manifest cannot contain PII"):
            DatasetHandoffManifest.from_payload(dataset_payload(contains_pii=True))
        with self.assertRaisesRegex(ValidationError, "dataset manifest cannot contain customer data"):
            DatasetHandoffManifest.from_payload(dataset_payload(contains_customer_data=True))

    def test_dataset_manifest_requires_train_validation_test_counts(self) -> None:
        with self.assertRaisesRegex(ValidationError, "split_counts requires train, validation, and test"):
            DatasetHandoffManifest.from_payload(dataset_payload(split_counts={"train": 100, "test": 25}))


class EvaluationHandoffReportTests(unittest.TestCase):
    def test_valid_evaluation_report_matches_dataset_snapshot(self) -> None:
        dataset = DatasetHandoffManifest.from_payload(dataset_payload())
        report = EvaluationHandoffReport.from_payload(evaluation_payload())

        validate_evaluation_against_dataset(report, dataset)

        self.assertEqual(report.contract_version, "mlops.evaluation_report.v1")
        self.assertEqual(report.model_ref, "registry://flange-qc-v2/detector/punch-mark/2026-06-02")
        self.assertEqual(report.metrics["precision"], 0.92)
        self.assertFalse(report.production_authority)

    def test_evaluation_report_rejects_metric_outside_unit_interval(self) -> None:
        with self.assertRaisesRegex(ValidationError, "metrics.recall must be between 0 and 1"):
            EvaluationHandoffReport.from_payload(evaluation_payload(metrics={"precision": 0.9, "recall": 1.2}))

    def test_evaluation_report_rejects_latency_over_budget(self) -> None:
        with self.assertRaisesRegex(ValidationError, "latency_ms_p95 exceeds latency_budget_ms_p95"):
            EvaluationHandoffReport.from_payload(
                evaluation_payload(latency_ms_p95=175.0, latency_budget_ms_p95=150.0)
            )

    def test_evaluation_report_rejects_production_authority_or_promotion(self) -> None:
        with self.assertRaisesRegex(ValidationError, "evaluation report cannot approve production authority"):
            EvaluationHandoffReport.from_payload(evaluation_payload(production_authority=True))
        with self.assertRaisesRegex(ValidationError, "promotion_decision must remain not_approved"):
            EvaluationHandoffReport.from_payload(evaluation_payload(promotion_decision="approved"))

    def test_evaluation_report_must_match_dataset_snapshot(self) -> None:
        dataset = DatasetHandoffManifest.from_payload(dataset_payload())
        report = EvaluationHandoffReport.from_payload(
            evaluation_payload(dataset_snapshot_ref="dataset://flange-qc-v2/shadow/other")
        )

        with self.assertRaisesRegex(ValidationError, "evaluation dataset snapshot does not match"):
            validate_evaluation_against_dataset(report, dataset)


if __name__ == "__main__":
    unittest.main()
