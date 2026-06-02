import json
import tempfile
import unittest
from pathlib import Path

from apps.flange_qc_v2.calibration import load_calibration_config
from apps.flange_qc_v2.domain import ValidationError


REPO_ROOT = Path(__file__).resolve().parents[2]
CALIBRATION_FIXTURE = REPO_ROOT / "configs/flange_qc_v2/camera_calibration.synthetic.example.json"


class CalibrationConfigTests(unittest.TestCase):
    def test_synthetic_calibration_exposes_metadata_without_production_authority(self) -> None:
        calibration = load_calibration_config(CALIBRATION_FIXTURE)

        self.assertEqual(calibration.status, "synthetic")
        self.assertFalse(calibration.production_authority)
        self.assertEqual(calibration.decision, "BLOCKED")
        self.assertEqual(calibration.reason_codes, ["CALIBRATION_MISSING"])
        self.assertEqual(calibration.camera["mount"], "top_down_90_degrees")
        self.assertEqual(calibration.lighting["layout"], "four_led_bars")

    def test_invalid_calibration_shape_is_rejected_explicitly(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "calibration.json"
            path.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "status": "synthetic",
                        "approved_for_production": False,
                        "source_ref": "fixture",
                        "lighting": {"layout": "four_led_bars"},
                    }
                ),
                encoding="utf-8",
            )

            with self.assertRaisesRegex(ValidationError, "camera is required"):
                load_calibration_config(path)


if __name__ == "__main__":
    unittest.main()
