import asyncio
import json
import unittest
from pathlib import Path

from apps.flange_qc_v2.asgi import app
from apps.flange_qc_v2.domain import InspectionSnapshot
from apps.flange_qc_v2.hmi_stream import build_replay_inspection_snapshot


REPO_ROOT = Path(__file__).resolve().parents[2]
PRODUCT_SPECS = REPO_ROOT / "configs/flange_qc_v2/product_specs.bootstrap.json"
CALIBRATION_FIXTURE = REPO_ROOT / "configs/flange_qc_v2/camera_calibration.synthetic.example.json"
SAMPLE_REPLAY = REPO_ROOT / "samples/replay/flange_qc_v2/phase2_synthetic_measurements.json"


class HmiStreamSnapshotTests(unittest.TestCase):
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
        self.assertEqual(parsed.phase, "PHASE_2")
        self.assertEqual(parsed.decision, "BLOCKED")
        self.assertEqual(
            parsed.reason_codes,
            ["PRODUCT_SPEC_APPROVAL_MISSING", "CALIBRATION_MISSING"],
        )
        self.assertEqual(payload["measurements"]["diagonals"], [83.0, 83.25])
        self.assertEqual(payload["observations"], [])

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
        self.assertEqual(payload["product"]["code"], "611")
        self.assertEqual(messages[-1]["type"], "websocket.close")


if __name__ == "__main__":
    unittest.main()
