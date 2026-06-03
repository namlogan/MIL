import asyncio
import json
import os
import tempfile
import unittest
from pathlib import Path

from apps.flange_qc_v2.asgi import app
from apps.flange_qc_v2.audit import AuditStore
from apps.flange_qc_v2.domain import InspectionSnapshot


REPO_ROOT = Path(__file__).resolve().parents[2]
PRODUCT_SPECS_ENV = "FLANGE_QC_V2_PRODUCT_SPECS_PATH"
CALIBRATION_ENV = "FLANGE_QC_V2_CALIBRATION_PATH"
AUDIT_ENV = "FLANGE_QC_V2_AUDIT_DB_PATH"
PRODUCT_SPECS = REPO_ROOT / "configs/flange_qc_v2/product_specs.bootstrap.json"
CALIBRATION_FIXTURE = REPO_ROOT / "configs/flange_qc_v2/camera_calibration.synthetic.example.json"
INTAKE_SCHEMA = REPO_ROOT / "contracts/flange_qc_v2/events/inspection_intake.schema.json"


class InspectionIntakeEndpointTests(unittest.TestCase):
    def setUp(self) -> None:
        self._previous_env = {
            PRODUCT_SPECS_ENV: os.environ.pop(PRODUCT_SPECS_ENV, None),
            CALIBRATION_ENV: os.environ.pop(CALIBRATION_ENV, None),
            AUDIT_ENV: os.environ.pop(AUDIT_ENV, None),
        }
        os.environ[PRODUCT_SPECS_ENV] = str(PRODUCT_SPECS)
        os.environ[CALIBRATION_ENV] = str(CALIBRATION_FIXTURE)

    def tearDown(self) -> None:
        for key in (PRODUCT_SPECS_ENV, CALIBRATION_ENV, AUDIT_ENV):
            os.environ.pop(key, None)
            previous = self._previous_env[key]
            if previous is not None:
                os.environ[key] = previous

    def test_post_inspection_intake_runs_sop_engine_from_measurements(self) -> None:
        response = self._post_intake(
            {
                "contract_version": "inspection.intake.v1",
                "inspection_id": "live-intake-001",
                "product_code": "611",
                "size_group": "11",
                "frame": {
                    "frame_id": "frame-live-001",
                    "source_uri": "camera://line-1/hikrobot/frame-live-001",
                    "captured_at": "2026-06-03T08:00:00Z",
                    "source_ref": "camera://line-1/hikrobot",
                },
                "measurements": {
                    "length_points": [74.9, 75.0, 75.1],
                    "width_points": [37.4, 37.5, 37.6],
                    "diagonals": [83.0, 83.25],
                    "unit": "inch",
                },
                "observations": [
                    {
                        "label": "punch_mark",
                        "confidence": 0.91,
                        "bbox": [0.42, 0.25, 0.12, 0.08],
                        "model_ref": "registry://flange-qc-v2/detector/punch-mark/candidate",
                        "evidence_ref": "artifact://eval/candidate.json",
                    }
                ],
            }
        )

        self.assertEqual(response["status"], 200)
        parsed = InspectionSnapshot.from_payload(response["body"])
        self.assertEqual(parsed.inspection_id, "live-intake-001")
        self.assertEqual(parsed.product_code, "611")
        self.assertEqual(parsed.phase, "FINAL")
        self.assertEqual(parsed.decision, "BLOCKED")
        self.assertIn("PRODUCT_SPEC_APPROVAL_MISSING", parsed.reason_codes)
        self.assertIn("CALIBRATION_MISSING", parsed.reason_codes)
        self.assertEqual(response["body"]["measurements"]["measurement_source"], "provided_measurements")
        self.assertEqual(response["body"]["phase_results"][2]["decision"], "ASSIST")
        self.assertFalse(response["body"]["phase_results"][2]["production_authority"])
        self.assertEqual(response["body"]["observations"][0]["model_ref"], "registry://flange-qc-v2/detector/punch-mark/candidate")

    def test_post_inspection_intake_derives_measurements_from_boundary_corners(self) -> None:
        response = self._post_intake(
            {
                "contract_version": "inspection.intake.v1",
                "inspection_id": "live-intake-boundary-001",
                "product_code": "611",
                "size_group": "11",
                "frame": {
                    "frame_id": "frame-live-boundary-001",
                    "source_uri": "camera://line-1/hikrobot/frame-live-boundary-001",
                    "captured_at": "2026-06-03T08:01:00Z",
                    "source_ref": "camera://line-1/hikrobot",
                },
                "boundary": {
                    "source": "camera_boundary_detector",
                    "corners": {
                        "top_left": [0, 0],
                        "top_right": [150, 0],
                        "bottom_right": [150, 75],
                        "bottom_left": [0, 75],
                    },
                },
                "observations": [],
            }
        )

        self.assertEqual(response["status"], 200)
        body = response["body"]
        self.assertEqual(body["measurements"]["length_points"], [75.0, 75.0, 75.0])
        self.assertEqual(body["measurements"]["width_points"], [37.5, 37.5, 37.5])
        self.assertEqual(body["measurements"]["measurement_source"], "boundary_corners_calibrated_shadow")
        self.assertEqual(
            body["measurements"]["measurement_evidence"]["calibration_method"],
            "top_down_boundary_corners_shadow_v1",
        )

    def test_post_inspection_intake_rejects_request_supplied_paths(self) -> None:
        response = self._post_intake(
            {
                "contract_version": "inspection.intake.v1",
                "inspection_id": "unsafe-intake",
                "product_code": "611",
                "size_group": "11",
                "product_specs_path": "/tmp/unsafe-product-specs.json",
                "frame": {
                    "frame_id": "frame-unsafe",
                    "source_uri": "camera://line-1/hikrobot/frame-unsafe",
                    "captured_at": "2026-06-03T08:02:00Z",
                    "source_ref": "camera://line-1/hikrobot",
                },
                "measurements": {
                    "length_points": [74.9, 75.0, 75.1],
                    "width_points": [37.4, 37.5, 37.6],
                    "diagonals": [83.0, 83.25],
                    "unit": "inch",
                },
            }
        )

        self.assertEqual(response["status"], 400)
        self.assertIn("product_specs_path", response["body"]["detail"])

    def test_post_inspection_intake_rejects_invalid_observation_bbox(self) -> None:
        response = self._post_intake(
            {
                "contract_version": "inspection.intake.v1",
                "inspection_id": "bad-observation",
                "product_code": "611",
                "size_group": "11",
                "frame": {
                    "frame_id": "frame-bad-observation",
                    "source_uri": "camera://line-1/hikrobot/frame-bad-observation",
                    "captured_at": "2026-06-03T08:03:00Z",
                    "source_ref": "camera://line-1/hikrobot",
                },
                "measurements": {
                    "length_points": [74.9, 75.0, 75.1],
                    "width_points": [37.4, 37.5, 37.6],
                    "diagonals": [83.0, 83.25],
                    "unit": "inch",
                },
                "observations": [{"label": "punch_mark", "confidence": 0.91, "bbox": [0.1, 0.2, 1.2, 0.1]}],
            }
        )

        self.assertEqual(response["status"], 400)
        self.assertIn("bbox values must be between 0 and 1", response["body"]["detail"])

    def test_post_inspection_intake_rejects_unsafe_frame_source_ref(self) -> None:
        response = self._post_intake(
            {
                "contract_version": "inspection.intake.v1",
                "inspection_id": "unsafe-source-ref",
                "product_code": "611",
                "size_group": "11",
                "frame": {
                    "frame_id": "frame-unsafe-source-ref",
                    "source_uri": "camera://line-1/hikrobot/frame-unsafe-source-ref",
                    "captured_at": "2026-06-03T08:05:00Z",
                    "source_ref": "/tmp/raw-camera-frame.jpg",
                },
                "measurements": {
                    "length_points": [74.9, 75.0, 75.1],
                    "width_points": [37.4, 37.5, 37.6],
                    "diagonals": [83.0, 83.25],
                    "unit": "inch",
                },
            }
        )

        self.assertEqual(response["status"], 400)
        self.assertIn("frame.source_ref must use", response["body"]["detail"])

    def test_post_inspection_intake_persists_audit_idempotently_when_configured(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            audit_path = Path(tmpdir) / "audit.sqlite"
            os.environ[AUDIT_ENV] = str(audit_path)
            payload = {
                "contract_version": "inspection.intake.v1",
                "inspection_id": "live-intake-audit-001",
                "product_code": "611",
                "size_group": "11",
                "frame": {
                    "frame_id": "frame-live-audit-001",
                    "source_uri": "camera://line-1/hikrobot/frame-live-audit-001",
                    "captured_at": "2026-06-03T08:04:00Z",
                    "source_ref": "camera://line-1/hikrobot",
                },
                "measurements": {
                    "length_points": [74.9, 75.0, 75.1],
                    "width_points": [37.4, 37.5, 37.6],
                    "diagonals": [83.0, 83.25],
                    "unit": "inch",
                },
            }

            first = self._post_intake(payload)
            second = self._post_intake(payload)
            self.assertEqual(first["status"], 200)
            self.assertEqual(second["status"], 200)
            store = AuditStore(audit_path)
            record = store.fetch_inspection("live-intake-audit-001")

        self.assertIsNotNone(record)
        assert record is not None
        self.assertEqual(record["payload"]["inspection_id"], "live-intake-audit-001")
        self.assertEqual(record["payload"]["event_type"], "inspection.snapshot")

    def _post_intake(self, payload: dict[str, object]) -> dict[str, object]:
        messages = []
        body = json.dumps(payload).encode("utf-8")

        async def receive():
            return {"type": "http.request", "body": body, "more_body": False}

        async def send(message):
            messages.append(message)

        scope = {"type": "http", "method": "POST", "path": "/inspection/intake"}
        asyncio.run(app(scope, receive, send))
        return {
            "status": messages[0]["status"],
            "body": json.loads(messages[1]["body"].decode("utf-8")),
        }


class InspectionIntakeContractTests(unittest.TestCase):
    def test_inspection_intake_schema_defines_camera_pipeline_contract_without_paths(self) -> None:
        schema = json.loads(INTAKE_SCHEMA.read_text(encoding="utf-8"))
        properties = schema["properties"]
        frame = properties["frame"]["properties"]
        observation = properties["observations"]["items"]["properties"]

        self.assertEqual(schema["title"], "FLANGE QC V2 Inspection Intake")
        self.assertIn("contract_version", schema["required"])
        self.assertEqual(
            schema["oneOf"],
            [
                {"required": ["measurements"], "not": {"required": ["boundary"]}},
                {"required": ["boundary"], "not": {"required": ["measurements"]}},
            ],
        )
        self.assertEqual(properties["contract_version"]["const"], "inspection.intake.v1")
        self.assertIn("measurements", properties)
        self.assertIn("boundary", properties)
        self.assertEqual(frame["source_uri"]["pattern"], "^(camera|replay|synthetic)://")
        self.assertEqual(frame["source_ref"]["pattern"], "^(camera|replay|synthetic)://")
        self.assertEqual(observation["bbox"]["items"]["minimum"], 0)
        self.assertEqual(observation["bbox"]["items"]["maximum"], 1)
        for forbidden in (
            "artifact_intake_dir",
            "calibration_path",
            "dataset_path",
            "manifest_path",
            "model_path",
            "product_specs_path",
            "weights_path",
        ):
            self.assertNotIn(forbidden, properties)


if __name__ == "__main__":
    unittest.main()
