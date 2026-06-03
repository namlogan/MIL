import json
import contextlib
import io
import tempfile
import unittest
from pathlib import Path

from apps.flange_qc_v2.audit import AuditStore, FEEDBACK_EXPORT_CONTRACT_VERSION
from apps.flange_qc_v2.domain import BoundingBox, DetectorObservation, InspectionSnapshot
from apps.flange_qc_v2.feedback import QcFeedback, build_labeling_review_pack
from scripts.flange_qc_v2.export_qc_feedback import main as export_main
from scripts.flange_qc_v2.build_labeling_review_pack import main as pack_main
from scripts.flange_qc_v2.validate_qc_feedback_export import main as validate_main


class QcFeedbackExportTests(unittest.TestCase):
    def test_export_feedback_metadata_records_without_raw_payloads(self) -> None:
        snapshot = InspectionSnapshot(
            inspection_id="insp-export-001",
            product_code="611",
            product_spec_version="bootstrap_replay",
            phase="PHASE_2",
            decision="NG",
            reason_codes=["MODEL_REVIEW_REQUIRED"],
            observations=[
                DetectorObservation(
                    label="punch_mark",
                    confidence=0.87,
                    bbox=BoundingBox(0.42, 0.22, 0.12, 0.05),
                    model_ref="registry://flange-qc-v2/shadow-detector@candidate",
                    evidence_ref="eval://flange-qc-v2/shadow-eval-001",
                )
            ],
            created_at="2026-06-03T00:00:00Z",
        )
        feedback = QcFeedback(
            feedback_id="fb-export-001",
            inspection_id="insp-export-001",
            feedback_type="MARK_FALSE_POSITIVE",
            reviewer_id="qc-reviewer-1",
            note="Model marked punch mark, QC confirmed false alarm.",
            shadow_decision="NG",
            source_ref="https://github.com/namlogan/MIL/issues/129",
            created_at="2026-06-03T00:01:00Z",
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            store = AuditStore(Path(tmpdir) / "audit.sqlite")
            store.initialize()
            store.append_inspection(snapshot)
            store.append_feedback(feedback)

            records = store.export_feedback_metadata_records()

        self.assertEqual(len(records), 1)
        record = records[0]
        self.assertEqual(record["contract_version"], "qc_feedback_export.v1")
        self.assertEqual(record["feedback_id"], "fb-export-001")
        self.assertEqual(record["inspection_id"], "insp-export-001")
        self.assertEqual(record["product"]["code"], "611")
        self.assertEqual(record["inspection_decision"], "NG")
        self.assertEqual(record["feedback_type"], "MARK_FALSE_POSITIVE")
        self.assertEqual(record["shadow_decision"], "NG")
        self.assertFalse(record["production_authority"])
        self.assertEqual(record["authority_blockers"], ["PRODUCTION_APPROVAL_REQUIRED"])
        self.assertEqual(record["observations"][0]["label"], "punch_mark")
        self.assertEqual(record["observations"][0]["bbox"], [0.42, 0.22, 0.12, 0.05])
        self.assertNotIn("payload", record)
        self.assertNotIn("payload_json", json.dumps(record))
        self.assertNotIn("raw_media", json.dumps(record))

    def test_cli_writes_jsonl_and_empty_export_is_valid(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            audit_path = Path(tmpdir) / "audit.sqlite"
            output_path = Path(tmpdir) / "feedback.jsonl"
            store = AuditStore(audit_path)
            store.initialize()

            exit_code = export_main(
                [
                    "--audit-db",
                    str(audit_path),
                    "--output",
                    str(output_path),
                ]
            )

            self.assertEqual(exit_code, 0)
            self.assertEqual(output_path.read_text(encoding="utf-8"), "")

    def test_cli_fails_closed_for_missing_audit_db(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            missing_path = Path(tmpdir) / "missing.sqlite"

            stderr = io.StringIO()
            with contextlib.redirect_stderr(stderr):
                exit_code = export_main(["--audit-db", str(missing_path)])

        self.assertEqual(exit_code, 1)
        self.assertIn("audit DB does not exist", stderr.getvalue())


class QcFeedbackExportValidationTests(unittest.TestCase):
    def test_feedback_export_schema_documents_sanitized_jsonl_contract(self) -> None:
        schema_path = Path("contracts/flange_qc_v2/feedback/qc_feedback_export.schema.json")

        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        properties = schema["properties"]

        self.assertEqual(schema["title"], "Flange QC V2 QC Feedback Export Record")
        self.assertIn("contract_version", schema["required"])
        self.assertIn("observations", schema["required"])
        self.assertEqual(properties["contract_version"]["const"], FEEDBACK_EXPORT_CONTRACT_VERSION)
        self.assertEqual(properties["production_authority"]["const"], False)
        self.assertFalse(properties["observations"]["items"]["additionalProperties"])
        self.assertNotIn("payload", properties)
        self.assertNotIn("payload_json", properties)

    def test_validate_cli_accepts_exported_jsonl_records(self) -> None:
        record = self._valid_record()
        with tempfile.TemporaryDirectory() as tmpdir:
            export_path = Path(tmpdir) / "feedback.jsonl"
            export_path.write_text(json.dumps(record, sort_keys=True) + "\n", encoding="utf-8")

            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                exit_code = validate_main(["--input", str(export_path)])

        result = json.loads(stdout.getvalue())
        self.assertEqual(exit_code, 0)
        self.assertTrue(result["ok"])
        self.assertEqual(result["record_count"], 1)
        self.assertEqual(result["errors"], [])

    def test_validate_cli_accepts_empty_jsonl_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            export_path = Path(tmpdir) / "feedback-empty.jsonl"
            export_path.write_text("", encoding="utf-8")

            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                exit_code = validate_main(["--input", str(export_path)])

        result = json.loads(stdout.getvalue())
        self.assertEqual(exit_code, 0)
        self.assertTrue(result["ok"])
        self.assertEqual(result["record_count"], 0)

    def test_validate_cli_rejects_unsafe_feedback_export_rows(self) -> None:
        invalid_record = self._valid_record()
        invalid_record["production_authority"] = True
        invalid_record["payload_json"] = {"raw": "full inspection payload dump"}
        invalid_record["observations"][0]["evidence_ref"] = "file:///tmp/factory-frame.png"
        invalid_record["observations"][0]["bbox"] = [1.2, 0.2, 0.1, 0.1]
        with tempfile.TemporaryDirectory() as tmpdir:
            export_path = Path(tmpdir) / "feedback-invalid.jsonl"
            export_path.write_text(json.dumps(invalid_record, sort_keys=True) + "\n", encoding="utf-8")

            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                exit_code = validate_main(["--input", str(export_path)])

        result = json.loads(stdout.getvalue())
        self.assertEqual(exit_code, 1)
        self.assertFalse(result["ok"])
        self.assertEqual(result["record_count"], 1)
        self.assertGreaterEqual(len(result["errors"]), 3)
        self.assertIn("production_authority", json.dumps(result["errors"]))
        self.assertIn("payload_json", json.dumps(result["errors"]))
        self.assertIn("bbox", json.dumps(result["errors"]))

    def test_validate_cli_fails_closed_for_missing_input_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            missing_path = Path(tmpdir) / "missing.jsonl"

            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                exit_code = validate_main(["--input", str(missing_path)])

        result = json.loads(stdout.getvalue())
        self.assertEqual(exit_code, 1)
        self.assertFalse(result["ok"])
        self.assertIn("does not exist", result["errors"][0]["message"])

    def _valid_record(self) -> dict[str, object]:
        return {
            "contract_version": FEEDBACK_EXPORT_CONTRACT_VERSION,
            "audit_feedback_id": 1,
            "feedback_id": "fb-export-validated-001",
            "inspection_id": "insp-export-validated-001",
            "product": {
                "code": "611",
                "spec_version": "bootstrap_replay",
            },
            "inspection_decision": "NG",
            "inspection_created_at": "2026-06-03T00:00:00Z",
            "feedback_type": "MARK_FALSE_POSITIVE",
            "reviewer_id": "qc-reviewer-1",
            "note": "QC confirmed this is a false alarm.",
            "shadow_decision": "NG",
            "source_ref": "https://github.com/namlogan/MIL/issues/131",
            "feedback_created_at": "2026-06-03T00:01:00Z",
            "production_authority": False,
            "authority_blockers": ["PRODUCTION_APPROVAL_REQUIRED"],
            "observations": [
                {
                    "label": "punch_mark",
                    "confidence": 0.87,
                    "bbox": [0.42, 0.22, 0.12, 0.05],
                    "model_ref": "registry://flange-qc-v2/shadow-detector@candidate",
                    "evidence_ref": "eval://flange-qc-v2/shadow-eval-001",
                }
            ],
        }


class QcFeedbackLabelingReviewPackTests(unittest.TestCase):
    def test_build_labeling_review_pack_summarizes_valid_feedback_records(self) -> None:
        false_positive = self._valid_record(
            feedback_id="fb-pack-001",
            product_code="611",
            feedback_type="MARK_FALSE_POSITIVE",
            inspection_decision="NG",
            shadow_decision="NG",
            label="punch_mark",
        )
        confirmed_alert = self._valid_record(
            feedback_id="fb-pack-002",
            product_code="445",
            feedback_type="CONFIRM_BLOCKED",
            inspection_decision="NG",
            shadow_decision="NG",
            label="broken_stitch",
        )

        pack = build_labeling_review_pack([false_positive, confirmed_alert])

        self.assertEqual(pack["contract_version"], "qc_feedback_labeling_review_pack.v1")
        self.assertEqual(pack["source_contract_version"], FEEDBACK_EXPORT_CONTRACT_VERSION)
        self.assertEqual(pack["source_record_count"], 2)
        self.assertEqual(pack["product_counts"], {"445": 1, "611": 1})
        self.assertEqual(pack["feedback_type_counts"], {"CONFIRM_BLOCKED": 1, "MARK_FALSE_POSITIVE": 1})
        self.assertEqual(pack["detector_label_counts"], {"broken_stitch": 1, "punch_mark": 1})
        self.assertFalse(pack["production_authority"])
        self.assertEqual(pack["authority_blockers"], ["PRODUCTION_APPROVAL_REQUIRED"])
        self.assertIn("review_false_positive_alerts", pack["recommended_next_actions"])
        self.assertNotIn("payload_json", json.dumps(pack))

    def test_empty_labeling_review_pack_is_valid_and_requests_more_feedback(self) -> None:
        pack = build_labeling_review_pack([])

        self.assertEqual(pack["source_record_count"], 0)
        self.assertEqual(pack["product_counts"], {})
        self.assertEqual(pack["detector_label_counts"], {})
        self.assertIn("collect_more_qc_feedback", pack["recommended_next_actions"])

    def test_labeling_review_pack_rejects_invalid_feedback_export_records(self) -> None:
        invalid_record = self._valid_record(feedback_id="fb-pack-invalid")
        invalid_record["production_authority"] = True

        with self.assertRaisesRegex(ValueError, "feedback export validation failed"):
            build_labeling_review_pack([invalid_record])

    def test_pack_cli_reads_jsonl_and_writes_summary_json(self) -> None:
        record = self._valid_record(feedback_id="fb-pack-cli")
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "feedback.jsonl"
            output_path = Path(tmpdir) / "pack.json"
            input_path.write_text(json.dumps(record, sort_keys=True) + "\n", encoding="utf-8")

            exit_code = pack_main(
                [
                    "--input",
                    str(input_path),
                    "--output",
                    str(output_path),
                ]
            )

            pack = json.loads(output_path.read_text(encoding="utf-8"))

        self.assertEqual(exit_code, 0)
        self.assertEqual(pack["source_record_count"], 1)
        self.assertEqual(pack["feedback_type_counts"], {"MARK_FALSE_POSITIVE": 1})

    def _valid_record(
        self,
        *,
        feedback_id: str,
        product_code: str = "611",
        feedback_type: str = "MARK_FALSE_POSITIVE",
        inspection_decision: str = "NG",
        shadow_decision: str = "NG",
        label: str = "punch_mark",
    ) -> dict[str, object]:
        return {
            "contract_version": FEEDBACK_EXPORT_CONTRACT_VERSION,
            "audit_feedback_id": 1,
            "feedback_id": feedback_id,
            "inspection_id": f"insp-{feedback_id}",
            "product": {
                "code": product_code,
                "spec_version": "bootstrap_replay",
            },
            "inspection_decision": inspection_decision,
            "inspection_created_at": "2026-06-03T00:00:00Z",
            "feedback_type": feedback_type,
            "reviewer_id": "qc-reviewer-1",
            "note": "QC reviewed the detector alert.",
            "shadow_decision": shadow_decision,
            "source_ref": "https://github.com/namlogan/MIL/issues/133",
            "feedback_created_at": "2026-06-03T00:01:00Z",
            "production_authority": False,
            "authority_blockers": ["PRODUCTION_APPROVAL_REQUIRED"],
            "observations": [
                {
                    "label": label,
                    "confidence": 0.87,
                    "bbox": [0.42, 0.22, 0.12, 0.05],
                    "model_ref": "registry://flange-qc-v2/shadow-detector@candidate",
                    "evidence_ref": "eval://flange-qc-v2/shadow-eval-001",
                }
            ],
        }


if __name__ == "__main__":
    unittest.main()
