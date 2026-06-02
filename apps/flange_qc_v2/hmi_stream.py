from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from apps.flange_qc_v2.detector import DetectorRequest, build_manifest_detector_from_intake
from apps.flange_qc_v2.domain import DetectorObservation, InspectionMeasurements, InspectionSnapshot, ValidationError
from apps.flange_qc_v2.replay import run_no_camera_replay


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_PRODUCT_SPECS = REPO_ROOT / "configs/flange_qc_v2/product_specs.bootstrap.json"
DEFAULT_CALIBRATION = REPO_ROOT / "configs/flange_qc_v2/camera_calibration.synthetic.example.json"
DEFAULT_REPLAY = REPO_ROOT / "samples/replay/flange_qc_v2/phase2_synthetic_measurements.json"
ARTIFACT_INTAKE_ENV = "FLANGE_QC_V2_ARTIFACT_INTAKE_DIR"


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
    observations = _build_review_only_observations(
        frame,
        source_ref=result.replay_id,
    )
    return InspectionSnapshot(
        inspection_id=result.replay_id,
        product_code=result.product_code,
        product_spec_version="bootstrap_replay",
        phase=result.decision.phase,
        decision=result.decision.decision,
        reason_codes=list(result.decision.reason_codes),
        measurements=InspectionMeasurements.from_payload(frame.measurements),
        observations=observations,
        phase_results=[phase_result.to_payload() for phase_result in result.phase_results],
        created_at=frame.captured_at,
    )


def _build_review_only_observations(frame: Any, *, source_ref: str) -> list[DetectorObservation]:
    replay_observations = tuple(getattr(frame, "detector_observations", ()))
    if not replay_observations:
        return []

    intake_dir = os.environ.get(ARTIFACT_INTAKE_ENV, "").strip()
    if not intake_dir:
        return []

    try:
        adapter = build_manifest_detector_from_intake(
            intake_dir,
            repo_root=REPO_ROOT,
            observations=replay_observations,
        )
        detector_result = adapter.detect(
            DetectorRequest(
                frame_id=frame.frame_id,
                source_uri=frame.source_uri,
                captured_at=frame.captured_at,
                source_ref=source_ref,
            )
        )
    except (OSError, ValueError, ValidationError):
        return []

    return list(detector_result.observations)
