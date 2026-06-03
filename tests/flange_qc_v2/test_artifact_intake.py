import asyncio
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from apps.flange_qc_v2.artifact_intake import validate_artifact_intake
from apps.flange_qc_v2.asgi import app


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


def asgi_get_json(path: str) -> dict:
    messages = []

    async def receive():
        return {"type": "http.request", "body": b"", "more_body": False}

    async def send(message):
        messages.append(message)

    asyncio.run(app({"type": "http", "method": "GET", "path": path}, receive, send))
    body = messages[1]["body"].decode("utf-8")
    return {"status": messages[0]["status"], "body": json.loads(body)}


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
        self.assertEqual(result["next_issue"]["recommended_task"], "shadow_observation_review")
        self.assertIn("submit_shadow_observation_payload", result["next_issue"]["recommended_next_actions"])

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


class ArtifactIntakeStatusEndpointTests(unittest.TestCase):
    def test_status_endpoint_reports_safe_unconfigured_state(self) -> None:
        previous = os.environ.pop("FLANGE_QC_V2_ARTIFACT_INTAKE_DIR", None)
        try:
            response = asgi_get_json("/artifact-intake/status")
        finally:
            if previous is not None:
                os.environ["FLANGE_QC_V2_ARTIFACT_INTAKE_DIR"] = previous

        body = response["body"]
        self.assertEqual(response["status"], 200)
        self.assertFalse(body["configured"])
        self.assertFalse(body["ok"])
        self.assertIn("FLANGE_QC_V2_ARTIFACT_INTAKE_DIR is not configured", body["errors"])
        self.assertFalse(body["ready"]["shadow_model_integration_issue"])
        self.assertFalse(body["ready"]["live_camera_implementation_issue"])
        self.assertEqual(body["next_issue"]["recommended_task"], "configure_artifact_intake")
        self.assertFalse(body["production_authority"])

    def test_status_endpoint_validates_configured_intake_dir_from_env(self) -> None:
        previous = os.environ.get("FLANGE_QC_V2_ARTIFACT_INTAKE_DIR")
        os.environ["FLANGE_QC_V2_ARTIFACT_INTAKE_DIR"] = str(TEMPLATE_DIR)
        try:
            response = asgi_get_json("/artifact-intake/status")
        finally:
            if previous is None:
                os.environ.pop("FLANGE_QC_V2_ARTIFACT_INTAKE_DIR", None)
            else:
                os.environ["FLANGE_QC_V2_ARTIFACT_INTAKE_DIR"] = previous

        body = response["body"]
        self.assertEqual(response["status"], 200)
        self.assertTrue(body["configured"])
        self.assertTrue(body["ok"], body)
        self.assertEqual(
            sorted(body["artifacts"].keys()),
            ["camera_boundary", "dataset_manifest", "evaluation_report", "model_artifact_manifest"],
        )
        self.assertTrue(body["ready"]["shadow_model_integration_issue"])
        self.assertFalse(body["ready"]["live_camera_implementation_issue"])
        self.assertEqual(body["next_issue"]["recommended_task"], "shadow_observation_review")
        self.assertIn("submit_shadow_observation_payload", body["next_issue"]["recommended_next_actions"])
        self.assertFalse(body["production_authority"])


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
