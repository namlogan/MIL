import asyncio
import contextlib
import io
import json
import os
import tempfile
import unittest
from pathlib import Path

from apps.flange_qc_v2 import detector
from apps.flange_qc_v2.asgi import app
from apps.flange_qc_v2.detector import DetectorRequest, DetectorResult, ManifestDetectorAdapter, StubDetectorAdapter
from apps.flange_qc_v2.domain import ValidationError
from apps.flange_qc_v2.model_artifact import ModelArtifactManifest


REPO_ROOT = Path(__file__).resolve().parents[2]
DETECTOR_SCHEMA = REPO_ROOT / "contracts/flange_qc_v2/detector/detector_result.schema.json"
SHADOW_OBSERVATION_REQUEST_SCHEMA = (
    REPO_ROOT / "contracts/flange_qc_v2/detector/shadow_observation_request.schema.json"
)
SHADOW_OBSERVATION_SAMPLE = (
    REPO_ROOT / "samples/replay/flange_qc_v2/shadow_detector_observation_request.json"
)
TEMPLATE_DIR = REPO_ROOT / "templates/flange_qc_v2/artifact_intake"


def detector_request_payload(**overrides):
    payload = {
        "frame_id": "frame-detector-001",
        "source_uri": "synthetic://flange-qc-v2/phase3/frame-detector-001",
        "captured_at": "2026-06-02T00:00:00Z",
        "source_ref": "https://github.com/namlogan/MIL/issues/85",
    }
    payload.update(overrides)
    return payload


def model_manifest_payload(**overrides):
    payload = {
        "contract_version": "model.artifact.v1",
        "model_ref": "registry://flange-qc-v2/detector/punch-mark/2026-06-02",
        "artifact_version": "detector-shadow-2026-06-02",
        "model_family": "detector",
        "task": "flange_qc_v2.detector",
        "labels": ["punch_mark", "corner_mark"],
        "output_schema": "contracts/flange_qc_v2/detector/detector_result.schema.json",
        "eval_report_ref": "docs/project/flange_qc_v2/eval/detector-shadow-2026-06-02.json",
        "artifact_digest": "sha256:" + ("a" * 64),
        "approval_status": "candidate",
        "production_authority": False,
        "shadow_mode": True,
        "source_ref": "https://github.com/namlogan/MIL/issues/99",
    }
    payload.update(overrides)
    return payload


def asgi_get_json(path: str) -> dict:
    messages = []

    async def receive():
        return {"type": "http.request", "body": b"", "more_body": False}

    async def send(message):
        messages.append(message)

    asyncio.run(app({"type": "http", "method": "GET", "path": path}, receive, send))
    return {
        "status": messages[0]["status"],
        "body": json.loads(messages[1]["body"].decode("utf-8")),
    }


def asgi_post_json(path: str, payload: dict) -> dict:
    messages = []
    raw_body = json.dumps(payload).encode("utf-8")
    body_sent = False

    async def receive():
        nonlocal body_sent
        if body_sent:
            return {"type": "http.disconnect"}
        body_sent = True
        return {"type": "http.request", "body": raw_body, "more_body": False}

    async def send(message):
        messages.append(message)

    asyncio.run(app({"type": "http", "method": "POST", "path": path}, receive, send))
    return {
        "status": messages[0]["status"],
        "body": json.loads(messages[1]["body"].decode("utf-8")),
    }


class DetectorAdapterSchemaTests(unittest.TestCase):
    def test_detector_result_schema_keeps_observations_non_authoritative(self) -> None:
        schema = json.loads(DETECTOR_SCHEMA.read_text(encoding="utf-8"))
        properties = schema["properties"]
        observation = properties["observations"]["items"]["properties"]

        self.assertEqual(schema["title"], "FLANGE QC V2 Detector Result")
        self.assertEqual(set(properties["decision"]["enum"]), {"NOT_EVALUATED", "ASSIST", "BLOCKED"})
        self.assertNotIn("PASS", properties["decision"]["enum"])
        self.assertNotIn("NG", properties["decision"]["enum"])
        self.assertEqual(observation["bbox"]["items"]["minimum"], 0)
        self.assertEqual(observation["bbox"]["items"]["maximum"], 1)
        self.assertEqual(properties["production_authority"]["const"], False)

    def test_shadow_observation_request_schema_documents_mlop_payload_contract(self) -> None:
        schema = json.loads(SHADOW_OBSERVATION_REQUEST_SCHEMA.read_text(encoding="utf-8"))
        properties = schema["properties"]
        observation = properties["observations"]["items"]["properties"]

        self.assertEqual(schema["title"], "FLANGE QC V2 Shadow Detector Observation Request")
        self.assertEqual(properties["contract_version"]["const"], "shadow_detector_observation_request.v1")
        self.assertFalse(schema["additionalProperties"])
        self.assertFalse(properties["request"]["additionalProperties"])
        self.assertFalse(properties["observations"]["items"]["additionalProperties"])
        self.assertEqual(properties["request"]["properties"]["source_uri"]["pattern"], "^(synthetic|replay)://")
        self.assertEqual(observation["bbox"]["items"]["minimum"], 0)
        self.assertEqual(observation["bbox"]["items"]["maximum"], 1)
        self.assertNotIn("artifact_intake_dir", properties)
        self.assertNotIn("manifest_path", properties)
        self.assertNotIn("model_path", properties)
        self.assertNotIn("dataset_path", properties)
        self.assertNotIn("model_ref", observation)
        self.assertNotIn("evidence_ref", observation)

    def test_validate_cli_accepts_shadow_observation_sample(self) -> None:
        from scripts.flange_qc_v2.validate_shadow_detector_observations import main as validate_main

        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            exit_code = validate_main(["--input", str(SHADOW_OBSERVATION_SAMPLE)])

        result = json.loads(stdout.getvalue())
        self.assertEqual(exit_code, 0)
        self.assertTrue(result["ok"])
        self.assertEqual(result["observation_count"], 1)
        self.assertEqual(result["errors"], [])

    def test_validate_cli_rejects_unsafe_shadow_observation_payload(self) -> None:
        from scripts.flange_qc_v2.validate_shadow_detector_observations import main as validate_main

        payload = {
            "contract_version": "shadow_detector_observation_request.v1",
            "artifact_intake_dir": "/tmp/unsafe",
            "request": detector_request_payload(source_uri="file:///factory/raw-frame.jpg"),
            "observations": [
                {
                    "label": "punch_mark",
                    "confidence": 1.2,
                    "bbox": [0.2, 0.3, 1.4, 0.1],
                    "model_ref": "registry://unsafe/request-supplied",
                }
            ],
        }
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "shadow-observations.json"
            input_path.write_text(json.dumps(payload), encoding="utf-8")

            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                exit_code = validate_main(["--input", str(input_path)])

        result = json.loads(stdout.getvalue())
        self.assertEqual(exit_code, 1)
        self.assertFalse(result["ok"])
        self.assertEqual(result["observation_count"], 1)
        self.assertIn("artifact_intake_dir", json.dumps(result["errors"]))
        self.assertIn("source_uri", json.dumps(result["errors"]))
        self.assertIn("confidence", json.dumps(result["errors"]))
        self.assertIn("bbox", json.dumps(result["errors"]))
        self.assertIn("model_ref", json.dumps(result["errors"]))

    def test_validate_cli_fails_closed_for_missing_shadow_observation_file(self) -> None:
        from scripts.flange_qc_v2.validate_shadow_detector_observations import main as validate_main

        with tempfile.TemporaryDirectory() as tmpdir:
            missing_path = Path(tmpdir) / "missing.json"

            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                exit_code = validate_main(["--input", str(missing_path)])

        result = json.loads(stdout.getvalue())
        self.assertEqual(exit_code, 1)
        self.assertFalse(result["ok"])
        self.assertIn("does not exist", result["errors"][0]["message"])


class StubDetectorAdapterTests(unittest.TestCase):
    def test_stub_detector_returns_not_evaluated_when_model_is_missing(self) -> None:
        request = DetectorRequest.from_payload(detector_request_payload())
        result = StubDetectorAdapter().detect(request)

        payload = result.to_payload()

        self.assertEqual(result.decision, "NOT_EVALUATED")
        self.assertEqual(result.reason_codes, ("MODEL_MISSING",))
        self.assertEqual(result.observations, ())
        self.assertFalse(result.production_authority)
        self.assertEqual(result.authority_blockers, ("MODEL_APPROVAL_REQUIRED", "PRODUCTION_APPROVAL_REQUIRED"))
        self.assertEqual(payload["contract_version"], "detector.result.v1")
        self.assertEqual(payload["request"]["frame_id"], "frame-detector-001")

    def test_stub_detector_returns_validated_observations_for_review_only(self) -> None:
        request = DetectorRequest.from_payload(detector_request_payload())
        adapter = StubDetectorAdapter(
            adapter_id="stub-review",
            model_ref="stub://detector/no-model",
            observations=[
                {
                    "label": "punch_mark",
                    "confidence": 0.42,
                    "bbox": [0.1, 0.2, 0.3, 0.4],
                    "model_ref": "stub://detector/no-model",
                    "evidence_ref": "synthetic://flange-qc-v2/evidence/punch-mark",
                }
            ],
        )

        result = adapter.detect(request)

        self.assertEqual(result.decision, "ASSIST")
        self.assertEqual(result.reason_codes, ("MODEL_REVIEW_REQUIRED",))
        self.assertEqual(len(result.observations), 1)
        self.assertEqual(result.observations[0].label, "punch_mark")
        self.assertFalse(result.production_authority)

    def test_stub_detector_rejects_invalid_observation_bbox(self) -> None:
        request = DetectorRequest.from_payload(detector_request_payload())
        adapter = StubDetectorAdapter(
            observations=[
                {
                    "label": "bad_bbox",
                    "confidence": 0.5,
                    "bbox": [0.1, 0.2, 1.5, 0.4],
                }
            ],
        )

        with self.assertRaisesRegex(ValidationError, "bbox values must be between 0 and 1"):
            adapter.detect(request)

    def test_detector_request_rejects_raw_media_source_uri(self) -> None:
        with self.assertRaisesRegex(ValidationError, "source_uri must use synthetic:// or replay://"):
            DetectorRequest.from_payload(
                detector_request_payload(source_uri="file:///factory/raw/frame.jpg")
            )

    def test_detector_result_cannot_emit_pass_or_ng(self) -> None:
        request = DetectorRequest.from_payload(detector_request_payload())

        with self.assertRaisesRegex(ValidationError, "detector result cannot emit decision"):
            DetectorResult(
                adapter_id="stub",
                request=request,
                decision="PASS",
                reason_codes=(),
                observations=(),
            )


class ManifestDetectorAdapterTests(unittest.TestCase):
    def test_manifest_detector_returns_review_only_observations(self) -> None:
        request = DetectorRequest.from_payload(detector_request_payload())
        manifest = ModelArtifactManifest.from_payload(model_manifest_payload())
        adapter = ManifestDetectorAdapter(
            manifest=manifest,
            observations=[
                {
                    "label": "punch_mark",
                    "confidence": 0.73,
                    "bbox": [0.1, 0.2, 0.3, 0.4],
                    "evidence_ref": "replay://flange-qc-v2/evidence/frame-detector-001",
                }
            ],
        )

        result = adapter.detect(request)

        self.assertEqual(result.decision, "ASSIST")
        self.assertEqual(result.reason_codes, ("MODEL_REVIEW_REQUIRED",))
        self.assertEqual(result.observations[0].model_ref, manifest.model_ref)
        self.assertFalse(result.production_authority)
        self.assertEqual(result.authority_blockers, ("MODEL_APPROVAL_REQUIRED", "PRODUCTION_APPROVAL_REQUIRED"))

    def test_manifest_detector_rejects_labels_not_declared_by_manifest(self) -> None:
        request = DetectorRequest.from_payload(detector_request_payload())
        manifest = ModelArtifactManifest.from_payload(model_manifest_payload(labels=["punch_mark"]))
        adapter = ManifestDetectorAdapter(
            manifest=manifest,
            observations=[
                {
                    "label": "unexpected_label",
                    "confidence": 0.73,
                    "bbox": [0.1, 0.2, 0.3, 0.4],
                }
            ],
        )

        with self.assertRaisesRegex(ValidationError, "observation label is not declared"):
            adapter.detect(request)


class ShadowDetectorBridgeTests(unittest.TestCase):
    def test_builds_shadow_detector_metadata_from_ready_artifact_intake(self) -> None:
        self.assertTrue(hasattr(detector, "build_shadow_detector_status_from_intake"))

        status = detector.build_shadow_detector_status_from_intake(TEMPLATE_DIR, repo_root=REPO_ROOT)

        self.assertTrue(status["configured"])
        self.assertTrue(status["ready"])
        self.assertIn("state", status)
        self.assertIn("next_task", status)
        self.assertEqual(status["state"], "ready_for_shadow_observation_review")
        self.assertEqual(status["next_task"], "shadow_observation_review")
        self.assertEqual(status["adapter_id"], "manifest-detector")
        self.assertEqual(status["model_ref"], "registry://flange-qc-v2/detector/punch-mark/2026-06-02")
        self.assertEqual(status["artifact_version"], "detector-shadow-2026-06-02")
        self.assertEqual(status["labels"], ["punch_mark", "corner_mark"])
        self.assertEqual(status["eval_report_ref"], "templates/flange_qc_v2/artifact_intake/evaluation_report.json")
        self.assertEqual(status["approval_status"], "candidate")
        self.assertTrue(status["shadow_mode"])
        self.assertFalse(status["production_authority"])
        self.assertEqual(status["authority_blockers"], ["MODEL_APPROVAL_REQUIRED", "PRODUCTION_APPROVAL_REQUIRED"])
        self.assertIn("recommended_next_actions", status["next_issue"])
        self.assertEqual(status["next_issue"]["recommended_task"], "shadow_observation_review")
        self.assertIn("submit_shadow_observation_payload", status["next_issue"]["recommended_next_actions"])

    def test_builds_manifest_detector_adapter_from_ready_artifact_intake(self) -> None:
        self.assertTrue(hasattr(detector, "build_manifest_detector_from_intake"))

        adapter = detector.build_manifest_detector_from_intake(TEMPLATE_DIR, repo_root=REPO_ROOT)
        request = DetectorRequest.from_payload(detector_request_payload())
        result = adapter.detect(request)

        self.assertEqual(adapter.manifest.model_ref, "registry://flange-qc-v2/detector/punch-mark/2026-06-02")
        self.assertEqual(adapter.manifest.labels, ("punch_mark", "corner_mark"))
        self.assertEqual(result.decision, "NOT_EVALUATED")
        self.assertEqual(result.reason_codes, ("MODEL_MISSING",))
        self.assertFalse(result.production_authority)

    def test_shadow_detector_status_endpoint_uses_env_only(self) -> None:
        previous = os.environ.get("FLANGE_QC_V2_ARTIFACT_INTAKE_DIR")
        os.environ["FLANGE_QC_V2_ARTIFACT_INTAKE_DIR"] = str(TEMPLATE_DIR)
        try:
            response = asgi_get_json("/detector/shadow/status")
        finally:
            if previous is None:
                os.environ.pop("FLANGE_QC_V2_ARTIFACT_INTAKE_DIR", None)
            else:
                os.environ["FLANGE_QC_V2_ARTIFACT_INTAKE_DIR"] = previous

        body = response["body"]
        self.assertEqual(response["status"], 200)
        self.assertTrue(body["configured"])
        self.assertTrue(body["ready"])
        self.assertIn("state", body)
        self.assertIn("next_task", body)
        self.assertEqual(body["state"], "ready_for_shadow_observation_review")
        self.assertEqual(body["next_task"], "shadow_observation_review")
        self.assertEqual(body["adapter_id"], "manifest-detector")
        self.assertEqual(body["model_ref"], "registry://flange-qc-v2/detector/punch-mark/2026-06-02")
        self.assertIn("recommended_next_actions", body["next_issue"])
        self.assertEqual(body["next_issue"]["recommended_task"], "shadow_observation_review")
        self.assertIn("submit_shadow_observation_payload", body["next_issue"]["recommended_next_actions"])
        self.assertFalse(body["production_authority"])

    def test_shadow_detector_status_endpoint_reports_safe_unconfigured_state(self) -> None:
        previous = os.environ.pop("FLANGE_QC_V2_ARTIFACT_INTAKE_DIR", None)
        try:
            response = asgi_get_json("/detector/shadow/status")
        finally:
            if previous is not None:
                os.environ["FLANGE_QC_V2_ARTIFACT_INTAKE_DIR"] = previous

        body = response["body"]
        self.assertEqual(response["status"], 200)
        self.assertFalse(body["configured"])
        self.assertFalse(body["ready"])
        self.assertEqual(body["next_issue"]["recommended_task"], "configure_artifact_intake")
        self.assertFalse(body["production_authority"])
        self.assertEqual(body["authority_blockers"], ["MODEL_APPROVAL_REQUIRED", "PRODUCTION_APPROVAL_REQUIRED"])

    def test_shadow_detector_observations_endpoint_uses_env_manifest_for_review_only_result(self) -> None:
        previous = os.environ.get("FLANGE_QC_V2_ARTIFACT_INTAKE_DIR")
        os.environ["FLANGE_QC_V2_ARTIFACT_INTAKE_DIR"] = str(TEMPLATE_DIR)
        try:
            response = asgi_post_json(
                "/detector/shadow/observations",
                {
                    "request": detector_request_payload(),
                    "observations": [
                        {
                            "label": "punch_mark",
                            "confidence": 0.82,
                            "bbox": [0.2, 0.3, 0.1, 0.1],
                        }
                    ],
                },
            )
        finally:
            if previous is None:
                os.environ.pop("FLANGE_QC_V2_ARTIFACT_INTAKE_DIR", None)
            else:
                os.environ["FLANGE_QC_V2_ARTIFACT_INTAKE_DIR"] = previous

        body = response["body"]
        self.assertEqual(response["status"], 200)
        self.assertEqual(body["contract_version"], "detector.result.v1")
        self.assertEqual(body["adapter_id"], "manifest-detector")
        self.assertEqual(body["decision"], "ASSIST")
        self.assertEqual(body["reason_codes"], ["MODEL_REVIEW_REQUIRED"])
        self.assertEqual(body["request"]["frame_id"], "frame-detector-001")
        self.assertEqual(body["observations"][0]["label"], "punch_mark")
        self.assertEqual(body["observations"][0]["model_ref"], "registry://flange-qc-v2/detector/punch-mark/2026-06-02")
        self.assertEqual(body["observations"][0]["evidence_ref"], "templates/flange_qc_v2/artifact_intake/evaluation_report.json")
        self.assertFalse(body["production_authority"])
        self.assertTrue(body["shadow_mode"])
        self.assertEqual(body["authority_blockers"], ["MODEL_APPROVAL_REQUIRED", "PRODUCTION_APPROVAL_REQUIRED"])

    def test_shadow_detector_observations_endpoint_returns_not_evaluated_without_observations(self) -> None:
        previous = os.environ.get("FLANGE_QC_V2_ARTIFACT_INTAKE_DIR")
        os.environ["FLANGE_QC_V2_ARTIFACT_INTAKE_DIR"] = str(TEMPLATE_DIR)
        try:
            response = asgi_post_json(
                "/detector/shadow/observations",
                {
                    "request": detector_request_payload(),
                    "observations": [],
                },
            )
        finally:
            if previous is None:
                os.environ.pop("FLANGE_QC_V2_ARTIFACT_INTAKE_DIR", None)
            else:
                os.environ["FLANGE_QC_V2_ARTIFACT_INTAKE_DIR"] = previous

        body = response["body"]
        self.assertEqual(response["status"], 200)
        self.assertEqual(body["decision"], "NOT_EVALUATED")
        self.assertEqual(body["reason_codes"], ["MODEL_MISSING"])
        self.assertEqual(body["observations"], [])
        self.assertFalse(body["production_authority"])

    def test_shadow_detector_observations_endpoint_fails_closed_without_artifact_intake_env(self) -> None:
        previous = os.environ.pop("FLANGE_QC_V2_ARTIFACT_INTAKE_DIR", None)
        try:
            response = asgi_post_json(
                "/detector/shadow/observations",
                {
                    "request": detector_request_payload(),
                    "observations": [
                        {
                            "label": "punch_mark",
                            "confidence": 0.82,
                            "bbox": [0.2, 0.3, 0.1, 0.1],
                        }
                    ],
                },
            )
        finally:
            if previous is not None:
                os.environ["FLANGE_QC_V2_ARTIFACT_INTAKE_DIR"] = previous

        self.assertEqual(response["status"], 400)
        self.assertIn("FLANGE_QC_V2_ARTIFACT_INTAKE_DIR is not configured", response["body"]["detail"])

    def test_shadow_detector_observations_endpoint_rejects_request_supplied_paths(self) -> None:
        previous = os.environ.get("FLANGE_QC_V2_ARTIFACT_INTAKE_DIR")
        os.environ["FLANGE_QC_V2_ARTIFACT_INTAKE_DIR"] = str(TEMPLATE_DIR)
        try:
            response = asgi_post_json(
                "/detector/shadow/observations",
                {
                    "artifact_intake_dir": "/tmp/unsafe",
                    "request": detector_request_payload(),
                    "observations": [
                        {
                            "label": "punch_mark",
                            "confidence": 0.82,
                            "bbox": [0.2, 0.3, 0.1, 0.1],
                        }
                    ],
                },
            )
        finally:
            if previous is None:
                os.environ.pop("FLANGE_QC_V2_ARTIFACT_INTAKE_DIR", None)
            else:
                os.environ["FLANGE_QC_V2_ARTIFACT_INTAKE_DIR"] = previous

        self.assertEqual(response["status"], 400)
        self.assertIn("artifact_intake_dir", response["body"]["detail"])

    def test_shadow_detector_observations_endpoint_rejects_request_supplied_model_refs(self) -> None:
        previous = os.environ.get("FLANGE_QC_V2_ARTIFACT_INTAKE_DIR")
        os.environ["FLANGE_QC_V2_ARTIFACT_INTAKE_DIR"] = str(TEMPLATE_DIR)
        try:
            response = asgi_post_json(
                "/detector/shadow/observations",
                {
                    "request": detector_request_payload(),
                    "observations": [
                        {
                            "label": "punch_mark",
                            "confidence": 0.82,
                            "bbox": [0.2, 0.3, 0.1, 0.1],
                            "model_ref": "registry://unsafe/request-supplied",
                        }
                    ],
                },
            )
        finally:
            if previous is None:
                os.environ.pop("FLANGE_QC_V2_ARTIFACT_INTAKE_DIR", None)
            else:
                os.environ["FLANGE_QC_V2_ARTIFACT_INTAKE_DIR"] = previous

        self.assertEqual(response["status"], 400)
        self.assertIn("model_ref", response["body"]["detail"])


if __name__ == "__main__":
    unittest.main()
