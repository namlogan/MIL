import contextlib
import io
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from apps.flange_qc_v2.artifact_intake import validate_artifact_intake
from apps.flange_qc_v2.artifact_readiness import build_artifact_readiness_report
from apps.flange_qc_v2.audit import FEEDBACK_EXPORT_CONTRACT_VERSION
from tests.flange_qc_v2.test_artifact_intake import TEMPLATE_DIR

from scripts.flange_qc_v2.build_artifact_readiness_report import main as readiness_main


REPO_ROOT = Path(__file__).resolve().parents[2]
READINESS_CLI = REPO_ROOT / "scripts/flange_qc_v2/build_artifact_readiness_report.py"


class ArtifactReadinessReportTests(unittest.TestCase):
    def test_report_marks_shadow_ready_but_keeps_camera_and_production_blocked(self) -> None:
        intake_result = validate_artifact_intake(TEMPLATE_DIR, repo_root=REPO_ROOT)
        feedback_pack = self._labeling_review_pack(source_record_count=2)

        report = build_artifact_readiness_report(
            intake_result,
            labeling_review_pack=feedback_pack,
            generated_at="2026-06-03T00:00:00Z",
            source_ref="https://github.com/namlogan/MIL/issues/135",
        )

        self.assertEqual(report["contract_version"], "artifact_readiness_report.v1")
        self.assertTrue(report["lanes"]["artifact_intake"]["ok"])
        self.assertTrue(report["lanes"]["shadow_model"]["ready"])
        self.assertEqual(report["lanes"]["shadow_model"]["recommended_task"], "shadow_model_integration")
        self.assertFalse(report["lanes"]["live_camera"]["ready"])
        self.assertIn(
            "CAMERA_HARDWARE_APPROVAL_REQUIRED",
            report["lanes"]["live_camera"]["authority_blockers"],
        )
        self.assertTrue(report["lanes"]["qc_feedback"]["ready_for_labeling_review"])
        self.assertEqual(report["lanes"]["qc_feedback"]["source_record_count"], 2)
        self.assertFalse(report["lanes"]["production_release"]["ready"])
        self.assertFalse(report["production_authority"])
        self.assertIn("open_shadow_model_integration_issue", report["recommended_next_actions"])
        self.assertIn("schedule_camera_hardware_readiness", report["recommended_next_actions"])
        self.assertNotIn("payload_json", json.dumps(report))
        self.assertNotIn("records", report["lanes"]["qc_feedback"])

    def test_report_fails_closed_for_missing_artifact_intake(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            missing_dir = Path(tmpdir) / "missing"
            intake_result = validate_artifact_intake(missing_dir, repo_root=REPO_ROOT)

        report = build_artifact_readiness_report(
            intake_result,
            generated_at="2026-06-03T00:00:00Z",
            source_ref="https://github.com/namlogan/MIL/issues/135",
        )

        self.assertFalse(report["lanes"]["artifact_intake"]["ok"])
        self.assertFalse(report["lanes"]["shadow_model"]["ready"])
        self.assertFalse(report["lanes"]["live_camera"]["ready"])
        self.assertEqual(report["lanes"]["artifact_intake"]["recommended_task"], "fix_artifact_intake")
        self.assertIn("fix_artifact_intake", report["recommended_next_actions"])
        self.assertFalse(report["production_authority"])

    def test_report_rejects_malformed_labeling_review_pack(self) -> None:
        intake_result = validate_artifact_intake(TEMPLATE_DIR, repo_root=REPO_ROOT)

        with self.assertRaisesRegex(ValueError, "labeling review pack"):
            build_artifact_readiness_report(
                intake_result,
                labeling_review_pack={"contract_version": "wrong", "production_authority": True},
                generated_at="2026-06-03T00:00:00Z",
                source_ref="https://github.com/namlogan/MIL/issues/135",
            )

    def test_cli_reads_artifact_intake_and_optional_pack(self) -> None:
        feedback_pack = self._labeling_review_pack(source_record_count=1)
        with tempfile.TemporaryDirectory() as tmpdir:
            pack_path = Path(tmpdir) / "labeling_pack.json"
            output_path = Path(tmpdir) / "readiness.json"
            pack_path.write_text(json.dumps(feedback_pack, sort_keys=True), encoding="utf-8")

            exit_code = readiness_main(
                [
                    "--intake-dir",
                    str(TEMPLATE_DIR),
                    "--labeling-review-pack",
                    str(pack_path),
                    "--generated-at",
                    "2026-06-03T00:00:00Z",
                    "--source-ref",
                    "https://github.com/namlogan/MIL/issues/135",
                    "--output",
                    str(output_path),
                ]
            )

            report = json.loads(output_path.read_text(encoding="utf-8"))

        self.assertEqual(exit_code, 0)
        self.assertEqual(report["lanes"]["qc_feedback"]["source_record_count"], 1)
        self.assertTrue(report["lanes"]["shadow_model"]["ready"])
        self.assertFalse(report["production_authority"])

    def test_cli_fails_closed_for_malformed_pack_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            pack_path = Path(tmpdir) / "bad-pack.json"
            pack_path.write_text('{"contract_version":"wrong"}', encoding="utf-8")

            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                exit_code = readiness_main(
                    [
                        "--intake-dir",
                        str(TEMPLATE_DIR),
                        "--labeling-review-pack",
                        str(pack_path),
                    ]
                )

        result = json.loads(stdout.getvalue())
        self.assertEqual(exit_code, 1)
        self.assertFalse(result["ok"])
        self.assertIn("labeling review pack", result["errors"][0])

    def test_cli_file_can_run_as_script(self) -> None:
        completed = subprocess.run(
            [
                sys.executable,
                str(READINESS_CLI),
                "--intake-dir",
                str(TEMPLATE_DIR),
                "--generated-at",
                "2026-06-03T00:00:00Z",
                "--source-ref",
                "https://github.com/namlogan/MIL/issues/135",
            ],
            check=True,
            text=True,
            capture_output=True,
        )

        report = json.loads(completed.stdout)
        self.assertEqual(report["contract_version"], "artifact_readiness_report.v1")
        self.assertTrue(report["lanes"]["shadow_model"]["ready"])
        self.assertFalse(report["production_authority"])

    def _labeling_review_pack(self, *, source_record_count: int) -> dict[str, object]:
        pack = {
            "contract_version": "qc_feedback_labeling_review_pack.v1",
            "source_contract_version": FEEDBACK_EXPORT_CONTRACT_VERSION,
            "source_record_count": source_record_count,
            "product_counts": {"611": source_record_count},
            "feedback_type_counts": {"MARK_FALSE_POSITIVE": source_record_count},
            "inspection_decision_counts": {"NG": source_record_count},
            "shadow_decision_counts": {"NG": source_record_count},
            "detector_label_counts": {"punch_mark": source_record_count},
            "recommended_next_actions": ["review_false_positive_alerts"],
            "production_authority": False,
            "authority_blockers": ["PRODUCTION_APPROVAL_REQUIRED"],
        }
        return pack


if __name__ == "__main__":
    unittest.main()
