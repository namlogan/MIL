import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from apps.flange_qc_v2.artifact_intake import validate_artifact_intake


REPO_ROOT = Path(__file__).resolve().parents[2]
TEMPLATE_DIR = REPO_ROOT / "templates/flange_qc_v2/artifact_intake"
VALIDATOR = REPO_ROOT / "scripts/flange_qc_v2/validate_artifact_intake.py"


def copy_template() -> tempfile.TemporaryDirectory:
    tmp = tempfile.TemporaryDirectory()
    target = Path(tmp.name) / "artifact_intake"
    shutil.copytree(TEMPLATE_DIR, target)
    return tmp


def write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


class ArtifactIntakeTemplateTests(unittest.TestCase):
    def test_template_bundle_validates_all_required_artifacts(self) -> None:
        result = validate_artifact_intake(TEMPLATE_DIR, repo_root=REPO_ROOT)

        self.assertTrue(result["ok"], result)
        self.assertEqual(
            sorted(result["artifacts"].keys()),
            ["camera_boundary", "dataset_manifest", "evaluation_report", "model_artifact_manifest"],
        )
        self.assertTrue(result["ready"]["shadow_model_integration_issue"])
        self.assertFalse(result["ready"]["live_camera_implementation_issue"])
        self.assertEqual(result["next_issue"]["recommended_task"], "shadow_model_integration")

    def test_cli_emits_json_validation_result(self) -> None:
        completed = subprocess.run(
            [sys.executable, str(VALIDATOR), "--intake-dir", str(TEMPLATE_DIR)],
            check=True,
            text=True,
            capture_output=True,
        )

        body = json.loads(completed.stdout)
        self.assertTrue(body["ok"], body)
        self.assertEqual(body["intake_dir"], str(TEMPLATE_DIR.resolve()))


class ArtifactIntakeFailureTests(unittest.TestCase):
    def test_rejects_raw_media_model_and_secret_files_in_bundle(self) -> None:
        with copy_template() as tmp:
            intake = Path(tmp) / "artifact_intake"
            (intake / "raw-frame.jpg").write_bytes(b"not allowed")
            (intake / "detector.onnx").write_bytes(b"not allowed")
            (intake / ".env").write_text("TOKEN=not-allowed", encoding="utf-8")

            result = validate_artifact_intake(intake, repo_root=REPO_ROOT)

        self.assertFalse(result["ok"], result)
        self.assertIn("raw-frame.jpg", "\n".join(result["errors"]))
        self.assertIn("detector.onnx", "\n".join(result["errors"]))
        self.assertIn(".env", "\n".join(result["errors"]))

    def test_rejects_missing_required_artifact(self) -> None:
        with copy_template() as tmp:
            intake = Path(tmp) / "artifact_intake"
            (intake / "evaluation_report.json").unlink()

            result = validate_artifact_intake(intake, repo_root=REPO_ROOT)

        self.assertFalse(result["ok"], result)
        self.assertIn("evaluation_report.json is required", result["errors"])

    def test_rejects_model_ref_that_does_not_match_evaluation_report(self) -> None:
        with copy_template() as tmp:
            intake = Path(tmp) / "artifact_intake"
            model_path = intake / "model_artifact_manifest.json"
            payload = json.loads(model_path.read_text(encoding="utf-8"))
            payload["model_ref"] = "registry://flange-qc-v2/detector/different-model/2026-06-02"
            write_json(model_path, payload)

            result = validate_artifact_intake(intake, repo_root=REPO_ROOT)

        self.assertFalse(result["ok"], result)
        self.assertIn("model artifact model_ref does not match evaluation report", result["errors"])

    def test_rejects_model_labels_outside_dataset_labels(self) -> None:
        with copy_template() as tmp:
            intake = Path(tmp) / "artifact_intake"
            model_path = intake / "model_artifact_manifest.json"
            payload = json.loads(model_path.read_text(encoding="utf-8"))
            payload["labels"] = ["punch_mark", "unexpected_label"]
            write_json(model_path, payload)

            result = validate_artifact_intake(intake, repo_root=REPO_ROOT)

        self.assertFalse(result["ok"], result)
        self.assertIn("model artifact labels are not declared by dataset manifest", result["errors"])

    def test_rejects_live_camera_enablement(self) -> None:
        with copy_template() as tmp:
            intake = Path(tmp) / "artifact_intake"
            camera_path = intake / "camera_boundary.json"
            payload = json.loads(camera_path.read_text(encoding="utf-8"))
            payload["live_capture_enabled"] = True
            write_json(camera_path, payload)

            result = validate_artifact_intake(intake, repo_root=REPO_ROOT)

        self.assertFalse(result["ok"], result)
        self.assertIn("live capture must remain disabled", "\n".join(result["errors"]))


if __name__ == "__main__":
    unittest.main()
