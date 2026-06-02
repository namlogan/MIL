import asyncio
import json
import os
import tempfile
import unittest
from pathlib import Path

from apps.flange_qc_v2.asgi import app
from apps.flange_qc_v2.audit import AuditStore
from apps.flange_qc_v2.domain import InspectionSnapshot
from apps.flange_qc_v2.hmi_stream import build_replay_inspection_snapshot


REPO_ROOT = Path(__file__).resolve().parents[2]
PRODUCT_SPECS = REPO_ROOT / "configs/flange_qc_v2/product_specs.bootstrap.json"
CALIBRATION_FIXTURE = REPO_ROOT / "configs/flange_qc_v2/camera_calibration.synthetic.example.json"
SAMPLE_REPLAY = REPO_ROOT / "samples/replay/flange_qc_v2/phase2_synthetic_measurements.json"
TEMPLATE_INTAKE = REPO_ROOT / "templates/flange_qc_v2/artifact_intake"
ARTIFACT_INTAKE_ENV = "FLANGE_QC_V2_ARTIFACT_INTAKE_DIR"


class HmiStreamSnapshotTests(unittest.TestCase):
    def setUp(self) -> None:
        self._previous_audit_path = os.environ.pop("FLANGE_QC_V2_AUDIT_DB_PATH", None)
        self._previous_artifact_intake = os.environ.pop(ARTIFACT_INTAKE_ENV, None)

    def tearDown(self) -> None:
        os.environ.pop("FLANGE_QC_V2_AUDIT_DB_PATH", None)
        os.environ.pop(ARTIFACT_INTAKE_ENV, None)
        if self._previous_audit_path is not None:
            os.environ["FLANGE_QC_V2_AUDIT_DB_PATH"] = self._previous_audit_path
        if self._previous_artifact_intake is not None:
            os.environ[ARTIFACT_INTAKE_ENV] = self._previous_artifact_intake

    def test_replay_snapshot_matches_inspection_websocket_contract(self) -> None:
        snapshot = build_replay_inspection_snapshot(
            manifest_path=SAMPLE_REPLAY,
            product_specs_path=PRODUCT_SPECS,
            calibration_path=CALIBRATION_FIXTURE,
        )

        payload = snapshot.to_payload()
        parsed = InspectionSnapshot.from_payload(payload)

        self.assertEqual(payload["event_type"], "inspection.snapshot")
        self.assertEqual(parsed.inspection_id, "fqv2-phase2-synthetic-001")
        self.assertEqual(parsed.product_code, "611")
        self.assertEqual(parsed.phase, "FINAL")
        self.assertEqual(parsed.decision, "BLOCKED")
        self.assertEqual(
            parsed.reason_codes,
            [
                "PRODUCT_SPEC_APPROVAL_MISSING",
                "CALIBRATION_MISSING",
                "MODEL_REVIEW_REQUIRED",
                "RULE_POST_MVP_DISABLED",
            ],
        )
        self.assertEqual(
            [phase_result["phase"] for phase_result in parsed.phase_results],
            ["PHASE_1", "PHASE_2", "PHASE_3", "PHASE_4"],
        )
        self.assertEqual(payload["measurements"]["diagonals"], [83.0, 83.25])
        self.assertEqual(payload["observations"], [])

    def test_replay_snapshot_attaches_manifest_detector_observations_when_intake_ready(self) -> None:
        os.environ[ARTIFACT_INTAKE_ENV] = str(TEMPLATE_INTAKE)

        snapshot = build_replay_inspection_snapshot(
            manifest_path=SAMPLE_REPLAY,
            product_specs_path=PRODUCT_SPECS,
            calibration_path=CALIBRATION_FIXTURE,
        )

        payload = snapshot.to_payload()
        parsed = InspectionSnapshot.from_payload(payload)

        self.assertEqual(parsed.decision, "BLOCKED")
        self.assertEqual(len(payload["observations"]), 1)
        observation = payload["observations"][0]
        self.assertEqual(observation["label"], "punch_mark")
        self.assertEqual(observation["confidence"], 0.87)
        self.assertEqual(observation["bbox"], [0.42, 0.25, 0.12, 0.08])
        self.assertEqual(observation["model_ref"], "registry://flange-qc-v2/detector/punch-mark/2026-06-02")
        self.assertEqual(observation["evidence_ref"], "templates/flange_qc_v2/artifact_intake/evaluation_report.json")

    def test_websocket_endpoint_accepts_and_sends_replay_snapshot(self) -> None:
        messages = []
        incoming = [{"type": "websocket.connect"}]

        async def receive():
            return incoming.pop(0) if incoming else {"type": "websocket.disconnect"}

        async def send(message):
            messages.append(message)

        scope = {"type": "websocket", "path": "/ws/inspection"}
        asyncio.run(app(scope, receive, send))

        self.assertEqual(messages[0]["type"], "websocket.accept")
        send_messages = [message for message in messages if message["type"] == "websocket.send"]
        self.assertEqual(len(send_messages), 1)
        payload = json.loads(send_messages[0]["text"])

        self.assertEqual(payload["event_type"], "inspection.snapshot")
        self.assertEqual(payload["decision"], "BLOCKED")
        self.assertEqual(payload["phase"], "FINAL")
        self.assertEqual(len(payload["phase_results"]), 4)
        self.assertEqual(payload["product"]["code"], "611")
        self.assertEqual(messages[-1]["type"], "websocket.close")

    def test_replay_http_endpoint_returns_current_snapshot_contract(self) -> None:
        messages = []

        async def receive():
            return {"type": "http.request", "body": b"", "more_body": False}

        async def send(message):
            messages.append(message)

        scope = {"type": "http", "method": "GET", "path": "/inspection/replay"}
        asyncio.run(app(scope, receive, send))

        start = messages[0]
        payload = json.loads(messages[1]["body"].decode("utf-8"))

        self.assertEqual(start["status"], 200)
        parsed = InspectionSnapshot.from_payload(payload)
        self.assertEqual(parsed.inspection_id, "fqv2-phase2-synthetic-001")
        self.assertEqual(parsed.decision, "BLOCKED")
        self.assertEqual(parsed.phase, "FINAL")
        self.assertIn("PRODUCT_SPEC_APPROVAL_MISSING", parsed.reason_codes)
        self.assertEqual(parsed.phase_results[2]["phase"], "PHASE_3")

    def test_replay_http_endpoint_persists_snapshot_idempotently_when_audit_db_is_configured(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            audit_path = Path(tmpdir) / "audit.sqlite"
            os.environ["FLANGE_QC_V2_AUDIT_DB_PATH"] = str(audit_path)

            first = self._call_replay_endpoint()
            second = self._call_replay_endpoint()
            store = AuditStore(audit_path)
            record = store.fetch_inspection("fqv2-phase2-synthetic-001")

        self.assertEqual(first["status"], 200)
        self.assertEqual(second["status"], 200)
        self.assertIsNotNone(record)
        assert record is not None
        self.assertEqual(record["inspection_id"], "fqv2-phase2-synthetic-001")
        self.assertEqual(record["decision"], "BLOCKED")
        self.assertEqual(record["payload"]["event_type"], "inspection.snapshot")
        self.assertEqual(len(record["payload"]["phase_results"]), 4)

    def _call_replay_endpoint(self) -> dict[str, object]:
        messages = []

        async def receive():
            return {"type": "http.request", "body": b"", "more_body": False}

        async def send(message):
            messages.append(message)

        scope = {"type": "http", "method": "GET", "path": "/inspection/replay"}
        asyncio.run(app(scope, receive, send))

        return {
            "status": messages[0]["status"],
            "body": json.loads(messages[1]["body"].decode("utf-8")),
        }


if __name__ == "__main__":
    unittest.main()
