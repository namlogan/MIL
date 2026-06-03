import json
import tempfile
import unittest
from pathlib import Path

from apps.flange_qc_v2.audit import AuditStore
from apps.flange_qc_v2.domain import BoundingBox, DetectorObservation, InspectionSnapshot
from apps.flange_qc_v2.feedback import QcFeedback
from scripts.flange_qc_v2.export_qc_feedback import main as export_main


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

            exit_code = export_main(["--audit-db", str(missing_path)])

        self.assertEqual(exit_code, 1)


if __name__ == "__main__":
    unittest.main()
