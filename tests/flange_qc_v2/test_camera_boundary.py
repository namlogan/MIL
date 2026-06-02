import json
import unittest
from pathlib import Path

from apps.flange_qc_v2.camera import CameraBoundaryConfig, HikrobotCameraBoundary
from apps.flange_qc_v2.domain import ValidationError


REPO_ROOT = Path(__file__).resolve().parents[2]
CAMERA_SCHEMA = REPO_ROOT / "contracts/flange_qc_v2/camera/camera_boundary.schema.json"


def boundary_payload(**overrides):
    payload = {
        "adapter_id": "hikrobot-boundary",
        "vendor": "Hikrobot",
        "enabled": False,
        "live_capture_enabled": False,
        "sdk_loaded": False,
        "credentials_configured": False,
        "source_ref": "https://github.com/namlogan/MIL/issues/87",
        "hardware_profile": {
            "camera_model": "pending_hardware_readiness",
            "lens": "pending_hardware_readiness",
            "lighting": "pending_hardware_readiness",
            "mount": "pending_hardware_readiness",
        },
    }
    payload.update(overrides)
    return payload


class CameraBoundarySchemaTests(unittest.TestCase):
    def test_camera_boundary_schema_exposes_disabled_no_hardware_contract(self) -> None:
        schema = json.loads(CAMERA_SCHEMA.read_text(encoding="utf-8"))
        properties = schema["properties"]

        self.assertEqual(schema["title"], "FLANGE QC V2 Camera Boundary")
        self.assertEqual(properties["enabled"]["const"], False)
        self.assertEqual(properties["live_capture_enabled"]["const"], False)
        self.assertEqual(properties["sdk_loaded"]["const"], False)
        self.assertEqual(properties["credentials_configured"]["const"], False)
        self.assertEqual(set(properties["decision"]["enum"]), {"BLOCKED", "NOT_EVALUATED"})
        self.assertEqual(properties["production_authority"]["const"], False)


class HikrobotCameraBoundaryTests(unittest.TestCase):
    def test_default_boundary_is_disabled_without_hardware_or_sdk(self) -> None:
        result = HikrobotCameraBoundary.default_disabled(
            source_ref="https://github.com/namlogan/MIL/issues/87"
        ).describe()

        payload = result.to_payload()

        self.assertEqual(result.vendor, "Hikrobot")
        self.assertFalse(result.enabled)
        self.assertFalse(result.live_capture_enabled)
        self.assertFalse(result.sdk_loaded)
        self.assertFalse(result.credentials_configured)
        self.assertEqual(result.decision, "BLOCKED")
        self.assertEqual(
            result.reason_codes,
            ("CAMERA_HARDWARE_READINESS_MISSING", "LIVE_CAMERA_DISABLED"),
        )
        self.assertEqual(
            result.authority_blockers,
            (
                "CAMERA_HARDWARE_APPROVAL_REQUIRED",
                "CALIBRATION_APPROVAL_REQUIRED",
                "PRODUCTION_APPROVAL_REQUIRED",
            ),
        )
        self.assertFalse(result.production_authority)
        self.assertEqual(payload["contract_version"], "camera.boundary.v1")

    def test_enabled_attempt_is_rejected_until_hardware_readiness(self) -> None:
        with self.assertRaisesRegex(ValidationError, "camera boundary must remain disabled"):
            CameraBoundaryConfig.from_payload(boundary_payload(enabled=True))

    def test_live_capture_attempt_is_rejected_until_hardware_readiness(self) -> None:
        with self.assertRaisesRegex(ValidationError, "live capture must remain disabled"):
            CameraBoundaryConfig.from_payload(boundary_payload(live_capture_enabled=True))

    def test_sdk_import_attempt_is_rejected_until_hardware_readiness(self) -> None:
        with self.assertRaisesRegex(ValidationError, "SDK loading must remain disabled"):
            CameraBoundaryConfig.from_payload(boundary_payload(sdk_loaded=True))

    def test_credentials_attempt_is_rejected_without_secrets(self) -> None:
        with self.assertRaisesRegex(ValidationError, "credentials must not be configured"):
            CameraBoundaryConfig.from_payload(boundary_payload(credentials_configured=True))

    def test_capture_frame_is_blocked_without_live_hardware(self) -> None:
        boundary = HikrobotCameraBoundary.default_disabled(
            source_ref="https://github.com/namlogan/MIL/issues/87"
        )

        with self.assertRaisesRegex(ValidationError, "live camera capture is disabled"):
            boundary.capture_frame()


if __name__ == "__main__":
    unittest.main()
