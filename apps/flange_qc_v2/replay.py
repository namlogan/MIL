from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from apps.flange_qc_v2.calibration import load_calibration_config
from apps.flange_qc_v2.decision_engine import (
    DecisionResult,
    evaluate_phase_one_measurements,
    evaluate_phase_two_geometry,
    evaluate_sop_safe_fallbacks,
)
from apps.flange_qc_v2.domain import DetectorObservation, ValidationError
from apps.flange_qc_v2.geometry import (
    PROVIDED_MEASUREMENT_SOURCE,
    GeometryMeasurementResolution,
    resolve_geometry_from_boundary,
    resolve_geometry_measurements,
)
from apps.flange_qc_v2.product_specs import load_product_specs


@dataclass(frozen=True)
class ReplayFrame:
    frame_id: str
    source_uri: str
    captured_at: str
    measurements: dict[str, Any]
    boundary: dict[str, Any] | None = None
    detector_observations: tuple[dict[str, Any], ...] = ()
    measurement_source: str = PROVIDED_MEASUREMENT_SOURCE
    measurement_evidence: dict[str, Any] | None = None

    def __post_init__(self) -> None:
        for field_name in ("frame_id", "source_uri", "captured_at"):
            if not str(getattr(self, field_name)).strip():
                raise ValidationError(f"{field_name} is required")
        if not self.source_uri.startswith("synthetic://"):
            raise ValidationError("frame source_uri must use synthetic://")
        if not isinstance(self.measurements, dict):
            raise ValidationError("frame measurements must be an object")
        if self.measurements:
            resolve_geometry_measurements(self.measurements)
        elif not isinstance(self.boundary, dict):
            raise ValidationError("frame measurements or boundary is required")
        object.__setattr__(
            self,
            "detector_observations",
            _coerce_detector_observations(self.detector_observations),
        )
        evidence = self.measurement_evidence or {}
        if not isinstance(evidence, dict):
            raise ValidationError("measurement_evidence must be an object")
        object.__setattr__(self, "measurement_evidence", dict(evidence))

    @classmethod
    def from_payload(cls, payload: Any) -> "ReplayFrame":
        if not isinstance(payload, dict):
            raise ValidationError("frame must be an object")
        for field_name in ("frame_id", "source_uri", "captured_at"):
            if field_name not in payload:
                raise ValidationError(f"frame {field_name} is required")
        if "measurements" not in payload and "boundary" not in payload:
            raise ValidationError("frame measurements or boundary is required")
        return cls(
            frame_id=str(payload["frame_id"]),
            source_uri=str(payload["source_uri"]),
            captured_at=str(payload["captured_at"]),
            measurements=dict(payload.get("measurements", {})),
            boundary=dict(payload["boundary"]) if isinstance(payload.get("boundary"), dict) else None,
            detector_observations=payload.get("detector_observations", ()),
        )

    def to_payload(self) -> dict[str, Any]:
        payload = {
            "frame_id": self.frame_id,
            "source_uri": self.source_uri,
            "captured_at": self.captured_at,
            "measurements": dict(self.measurements),
            "measurement_source": self.measurement_source,
        }
        if self.boundary is not None:
            payload["boundary"] = dict(self.boundary)
        if self.measurement_evidence:
            payload["measurement_evidence"] = dict(self.measurement_evidence)
        if self.detector_observations:
            payload["detector_observations"] = [dict(observation) for observation in self.detector_observations]
        return payload

    def with_geometry(self, geometry: GeometryMeasurementResolution) -> "ReplayFrame":
        return ReplayFrame(
            frame_id=self.frame_id,
            source_uri=self.source_uri,
            captured_at=self.captured_at,
            measurements=geometry.measurements.to_payload(),
            boundary=self.boundary,
            detector_observations=self.detector_observations,
            measurement_source=geometry.measurement_source,
            measurement_evidence=geometry.evidence,
        )


@dataclass(frozen=True)
class ReplayManifest:
    schema_version: int
    replay_id: str
    product_code: str
    size_group: str
    no_camera: bool
    frames: tuple[ReplayFrame, ...]
    source_ref: str = ""

    def __post_init__(self) -> None:
        for field_name in ("replay_id", "product_code", "size_group"):
            if not str(getattr(self, field_name)).strip():
                raise ValidationError(f"{field_name} is required")
        if not self.no_camera:
            raise ValidationError("no_camera replay manifest must set no_camera=true")
        if not self.frames:
            raise ValidationError("frames is required")

    @classmethod
    def from_payload(cls, payload: Any) -> "ReplayManifest":
        if not isinstance(payload, dict):
            raise ValidationError("replay manifest must be an object")
        for field_name in ("schema_version", "replay_id", "product_code", "size_group", "no_camera", "frames"):
            if field_name not in payload:
                raise ValidationError(f"{field_name} is required")
        frames = payload["frames"]
        if not isinstance(frames, list) or not frames:
            raise ValidationError("frames is required")
        return cls(
            schema_version=int(payload["schema_version"]),
            replay_id=str(payload["replay_id"]),
            product_code=str(payload["product_code"]),
            size_group=str(payload["size_group"]),
            no_camera=bool(payload["no_camera"]),
            frames=tuple(ReplayFrame.from_payload(frame) for frame in frames),
            source_ref=str(payload.get("source_ref", "")),
        )

    def to_payload(self) -> dict[str, Any]:
        payload = {
            "schema_version": self.schema_version,
            "replay_id": self.replay_id,
            "product_code": self.product_code,
            "size_group": self.size_group,
            "no_camera": self.no_camera,
            "frames": [frame.to_payload() for frame in self.frames],
        }
        if self.source_ref:
            payload["source_ref"] = self.source_ref
        return payload


@dataclass(frozen=True)
class ReplayRunResult:
    replay_id: str
    mode: str
    product_code: str
    size_group: str
    frame_count: int
    decision: DecisionResult
    phase_results: tuple[DecisionResult, ...]
    frames: tuple[ReplayFrame, ...]

    def to_payload(self) -> dict[str, Any]:
        return {
            "replay_id": self.replay_id,
            "mode": self.mode,
            "product_code": self.product_code,
            "size_group": self.size_group,
            "frame_count": self.frame_count,
            "decision": self.decision.to_payload(),
            "phase_results": [phase_result.to_payload() for phase_result in self.phase_results],
            "frames": [frame.to_payload() for frame in self.frames],
        }


def load_replay_manifest(path: str | Path) -> ReplayManifest:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return ReplayManifest.from_payload(data)


def run_no_camera_replay(
    *,
    manifest_path: str | Path,
    product_specs_path: str | Path,
    calibration_path: str | Path,
) -> ReplayRunResult:
    manifest = load_replay_manifest(manifest_path)
    product_spec = load_product_specs(product_specs_path).resolve(
        product_code=manifest.product_code,
        size_group=manifest.size_group,
    )
    calibration = load_calibration_config(calibration_path)
    frame_geometries = tuple(_resolve_frame_geometry(frame, calibration) for frame in manifest.frames)
    geometry = frame_geometries[0]
    frames = tuple(
        frame.with_geometry(frame_geometry)
        for frame, frame_geometry in zip(manifest.frames, frame_geometries, strict=True)
    )
    phase_results = (
        evaluate_phase_one_measurements(
            product_spec=product_spec,
            calibration=calibration,
            geometry=geometry,
        ),
        evaluate_phase_two_geometry(
            product_spec=product_spec,
            calibration=calibration,
            geometry=geometry,
        ),
        evaluate_sop_safe_fallbacks(phase="PHASE_3"),
        evaluate_sop_safe_fallbacks(phase="PHASE_4"),
    )
    return ReplayRunResult(
        replay_id=manifest.replay_id,
        mode="no_camera_replay",
        product_code=manifest.product_code,
        size_group=manifest.size_group,
        frame_count=len(manifest.frames),
        decision=_aggregate_phase_results(phase_results),
        phase_results=phase_results,
        frames=frames,
    )


def _resolve_frame_geometry(frame: ReplayFrame, calibration: Any) -> GeometryMeasurementResolution:
    if frame.measurements:
        return resolve_geometry_measurements(frame.measurements)
    if frame.boundary is None:
        raise ValidationError("frame measurements or boundary is required")
    return resolve_geometry_from_boundary(frame.boundary, calibration=calibration)


def _aggregate_phase_results(phase_results: tuple[DecisionResult, ...]) -> DecisionResult:
    return DecisionResult(
        phase="FINAL",
        decision=_aggregate_decision_state(phase_results),
        reason_codes=_unique_codes(
            [
                code
                for phase_result in phase_results
                for code in phase_result.reason_codes
            ]
        ),
        authority_blockers=_unique_codes(
            [
                code
                for phase_result in phase_results
                for code in phase_result.authority_blockers
            ]
        ),
        production_authority=False,
        shadow_mode=True,
    )


def _aggregate_decision_state(phase_results: tuple[DecisionResult, ...]) -> str:
    decisions = {phase_result.decision for phase_result in phase_results}
    for decision in ("BLOCKED", "NG", "ASSIST", "NOT_EVALUATED"):
        if decision in decisions:
            return decision
    return "PASS"


def _unique_codes(codes: list[str]) -> tuple[str, ...]:
    unique: list[str] = []
    for code in codes:
        if code and code not in unique:
            unique.append(code)
    return tuple(unique)


def _coerce_detector_observations(values: Any) -> tuple[dict[str, Any], ...]:
    if values in (None, ()):
        return ()
    if not isinstance(values, (list, tuple)):
        raise ValidationError("detector_observations must be a list")

    observations: list[dict[str, Any]] = []
    for value in values:
        observation = DetectorObservation.from_payload(value)
        observations.append(
            {
                "label": observation.label,
                "confidence": observation.confidence,
                "bbox": observation.bbox.to_list(),
            }
        )
    return tuple(observations)
