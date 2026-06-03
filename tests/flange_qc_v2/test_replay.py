import json
import tempfile
import unittest
from pathlib import Path

from apps.flange_qc_v2.domain import ValidationError
from apps.flange_qc_v2.replay import load_replay_manifest, run_no_camera_replay


REPO_ROOT = Path(__file__).resolve().parents[2]
PRODUCT_SPECS = REPO_ROOT / "configs/flange_qc_v2/product_specs.bootstrap.json"
CALIBRATION_FIXTURE = REPO_ROOT / "configs/flange_qc_v2/camera_calibration.synthetic.example.json"
SAMPLE_REPLAY = REPO_ROOT / "samples/replay/flange_qc_v2/phase2_synthetic_measurements.json"
BOUNDARY_REPLAY = REPO_ROOT / "samples/replay/flange_qc_v2/phase2_synthetic_boundary.json"


class ReplayFrameSourceTests(unittest.TestCase):
    def test_load_replay_manifest_exposes_synthetic_frame_measurements(self) -> None:
        manifest = load_replay_manifest(SAMPLE_REPLAY)

        self.assertEqual(manifest.replay_id, "fqv2-phase2-synthetic-001")
        self.assertTrue(manifest.no_camera)
        self.assertEqual(manifest.product_code, "611")
        self.assertEqual(manifest.size_group, "11")
        self.assertEqual(len(manifest.frames), 1)
        self.assertEqual(manifest.frames[0].frame_id, "frame-001")
        self.assertEqual(manifest.frames[0].source_uri, "synthetic://flange-qc-v2/phase2/frame-001")
        self.assertEqual(manifest.frames[0].measurements["diagonals"], [83.0, 83.25])
        self.assertEqual(manifest.frames[0].detector_observations[0]["label"], "punch_mark")
        self.assertEqual(manifest.to_payload()["frames"][0]["detector_observations"][0]["confidence"], 0.87)

    def test_no_camera_replay_flow_runs_fail_closed_with_current_bootstrap_authority(self) -> None:
        result = run_no_camera_replay(
            manifest_path=SAMPLE_REPLAY,
            product_specs_path=PRODUCT_SPECS,
            calibration_path=CALIBRATION_FIXTURE,
        )

        payload = result.to_payload()

        self.assertEqual(result.replay_id, "fqv2-phase2-synthetic-001")
        self.assertEqual(result.frame_count, 1)
        self.assertEqual(result.decision.phase, "FINAL")
        self.assertEqual(result.decision.decision, "BLOCKED")
        self.assertEqual(
            result.decision.reason_codes,
            (
                "PRODUCT_SPEC_APPROVAL_MISSING",
                "CALIBRATION_MISSING",
                "MODEL_REVIEW_REQUIRED",
                "RULE_POST_MVP_DISABLED",
            ),
        )
        self.assertFalse(result.decision.production_authority)
        self.assertEqual(
            tuple(phase_result.phase for phase_result in result.phase_results),
            ("PHASE_1", "PHASE_2", "PHASE_3", "PHASE_4"),
        )
        self.assertEqual(payload["mode"], "no_camera_replay")
        self.assertEqual(payload["decision"]["phase"], "FINAL")
        self.assertEqual(payload["phase_results"][0]["phase"], "PHASE_1")
        self.assertEqual(
            payload["phase_results"][0]["reason_codes"],
            ["PRODUCT_SPEC_APPROVAL_MISSING", "CALIBRATION_MISSING"],
        )
        self.assertEqual(payload["phase_results"][2]["decision"], "ASSIST")
        self.assertEqual(payload["phase_results"][3]["decision"], "ASSIST")
        self.assertEqual(
            payload["phase_results"][2]["rule_results"][0]["rule_id"],
            "M1-SOP-6.4-PUNCH-MARK-001",
        )
        self.assertEqual(payload["phase_results"][2]["rule_results"][0]["evidence"]["matched_labels"], ["punch_mark"])
        self.assertEqual(payload["phase_results"][2]["rule_results"][0]["evidence"]["max_confidence"], 0.87)
        self.assertEqual(payload["frames"][0]["frame_id"], "frame-001")

    def test_no_camera_replay_derives_measurements_from_boundary_corners(self) -> None:
        result = run_no_camera_replay(
            manifest_path=BOUNDARY_REPLAY,
            product_specs_path=PRODUCT_SPECS,
            calibration_path=CALIBRATION_FIXTURE,
        )

        payload = result.to_payload()
        frame = payload["frames"][0]
        measurements = frame["measurements"]

        self.assertEqual(frame["measurement_source"], "boundary_corners_calibrated_shadow")
        self.assertEqual(measurements["length_points"], [75.0, 75.0, 75.0])
        self.assertEqual(measurements["width_points"], [37.5, 37.5, 37.5])
        self.assertEqual(payload["decision"]["decision"], "BLOCKED")
        self.assertIn("PRODUCT_SPEC_APPROVAL_MISSING", payload["decision"]["reason_codes"])
        self.assertIn("CALIBRATION_MISSING", payload["decision"]["reason_codes"])
        self.assertEqual(payload["phase_results"][2]["decision"], "NOT_EVALUATED")
        self.assertEqual(payload["phase_results"][2]["reason_codes"], ["MODEL_MISSING"])
        self.assertFalse(payload["decision"]["production_authority"])

    def test_replay_manifest_without_frames_is_rejected_explicitly(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "replay.json"
            path.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "replay_id": "bad-replay",
                        "product_code": "611",
                        "size_group": "11",
                        "no_camera": True,
                    }
                ),
                encoding="utf-8",
            )

            with self.assertRaisesRegex(ValidationError, "frames is required"):
                load_replay_manifest(path)

    def test_replay_manifest_rejects_invalid_detector_observation(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "replay.json"
            path.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "replay_id": "bad-detector-observation",
                        "product_code": "611",
                        "size_group": "11",
                        "no_camera": True,
                        "frames": [
                            {
                                "frame_id": "frame-bad-observation",
                                "source_uri": "synthetic://flange-qc-v2/phase2/frame-bad-observation",
                                "captured_at": "2026-06-02T00:00:00Z",
                                "measurements": {
                                    "length_points": [74.9, 75.0, 75.1],
                                    "width_points": [37.4, 37.5, 37.6],
                                    "diagonals": [83.0, 83.25],
                                    "unit": "inch",
                                },
                                "detector_observations": [
                                    {
                                        "label": "punch_mark",
                                        "confidence": 0.91,
                                        "bbox": [0.1, 0.2, 1.2, 0.1],
                                    }
                                ],
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            with self.assertRaisesRegex(ValidationError, "bbox values must be between 0 and 1"):
                load_replay_manifest(path)


if __name__ == "__main__":
    unittest.main()
