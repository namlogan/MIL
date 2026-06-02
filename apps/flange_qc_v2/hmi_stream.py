from __future__ import annotations

from pathlib import Path

from apps.flange_qc_v2.domain import InspectionMeasurements, InspectionSnapshot
from apps.flange_qc_v2.replay import run_no_camera_replay


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_PRODUCT_SPECS = REPO_ROOT / "configs/flange_qc_v2/product_specs.bootstrap.json"
DEFAULT_CALIBRATION = REPO_ROOT / "configs/flange_qc_v2/camera_calibration.synthetic.example.json"
DEFAULT_REPLAY = REPO_ROOT / "samples/replay/flange_qc_v2/phase2_synthetic_measurements.json"


def build_replay_inspection_snapshot(
    *,
    manifest_path: str | Path = DEFAULT_REPLAY,
    product_specs_path: str | Path = DEFAULT_PRODUCT_SPECS,
    calibration_path: str | Path = DEFAULT_CALIBRATION,
) -> InspectionSnapshot:
    result = run_no_camera_replay(
        manifest_path=manifest_path,
        product_specs_path=product_specs_path,
        calibration_path=calibration_path,
    )
    frame = result.frames[0]
    return InspectionSnapshot(
        inspection_id=result.replay_id,
        product_code=result.product_code,
        product_spec_version="bootstrap_replay",
        phase=result.decision.phase,
        decision=result.decision.decision,
        reason_codes=list(result.decision.reason_codes),
        measurements=InspectionMeasurements.from_payload(frame.measurements),
        observations=[],
        phase_results=[phase_result.to_payload() for phase_result in result.phase_results],
        created_at=frame.captured_at,
    )
