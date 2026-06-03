from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from apps.flange_qc_v2.calibration import load_calibration_config
from apps.flange_qc_v2.decision_engine import (
    DecisionResult,
    evaluate_phase_one_measurements,
    evaluate_phase_three_observations,
    evaluate_phase_two_geometry,
    evaluate_sop_safe_fallbacks,
)
from apps.flange_qc_v2.domain import DetectorObservation, InspectionMeasurements, InspectionSnapshot, ValidationError
from apps.flange_qc_v2.geometry import GeometryMeasurementResolution, resolve_geometry_from_boundary, resolve_geometry_measurements
from apps.flange_qc_v2.product_specs import load_product_specs


CONTRACT_VERSION = "inspection.intake.v1"
ALLOWED_SOURCE_PREFIXES = ("camera://", "replay://", "synthetic://")
FORBIDDEN_REQUEST_FIELDS = {
    "artifact_intake_dir",
    "calibration_path",
    "dataset_path",
    "manifest_path",
    "model_path",
    "product_specs_path",
    "weights_path",
}


@dataclass(frozen=True)
class IntakeFrame:
    frame_id: str
    source_uri: str
    captured_at: str
    source_ref: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "frame_id", _require_non_empty(self.frame_id, "frame.frame_id"))
        source_uri = _require_non_empty(self.source_uri, "frame.source_uri")
        if not source_uri.startswith(ALLOWED_SOURCE_PREFIXES):
            raise ValidationError("frame.source_uri must use camera://, replay://, or synthetic://")
        object.__setattr__(self, "source_uri", source_uri)
        object.__setattr__(self, "captured_at", _require_non_empty(self.captured_at, "frame.captured_at"))
        source_ref = _require_non_empty(self.source_ref, "frame.source_ref")
        if not source_ref.startswith(ALLOWED_SOURCE_PREFIXES):
            raise ValidationError("frame.source_ref must use camera://, replay://, or synthetic://")
        object.__setattr__(self, "source_ref", source_ref)

    @classmethod
    def from_payload(cls, payload: Any) -> "IntakeFrame":
        if not isinstance(payload, dict):
            raise ValidationError("frame is required and must be an object")
        return cls(
            frame_id=_require_field(payload, "frame_id", prefix="frame"),
            source_uri=_require_field(payload, "source_uri", prefix="frame"),
            captured_at=_require_field(payload, "captured_at", prefix="frame"),
            source_ref=_require_field(payload, "source_ref", prefix="frame"),
        )


def build_inspection_snapshot_from_intake(
    payload: Any,
    *,
    product_specs_path: str | Path,
    calibration_path: str | Path,
) -> InspectionSnapshot:
    if not isinstance(payload, dict):
        raise ValidationError("inspection intake payload must be an object")
    _reject_forbidden_request_fields(payload)
    if payload.get("contract_version") != CONTRACT_VERSION:
        raise ValidationError(f"contract_version must be {CONTRACT_VERSION}")

    inspection_id = _require_non_empty(_require_field(payload, "inspection_id"), "inspection_id")
    product_code = _require_non_empty(_require_field(payload, "product_code"), "product_code")
    size_group = _require_non_empty(_require_field(payload, "size_group"), "size_group")
    frame = IntakeFrame.from_payload(_require_field(payload, "frame"))

    product_spec = load_product_specs(product_specs_path).resolve(
        product_code=product_code,
        size_group=size_group,
    )
    calibration = load_calibration_config(calibration_path)
    geometry = _resolve_intake_geometry(payload, calibration=calibration)
    observations = _coerce_observations(payload.get("observations", []))
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
        evaluate_phase_three_observations(observations=observations),
        evaluate_sop_safe_fallbacks(phase="PHASE_4"),
    )
    final_decision = _aggregate_phase_results(phase_results)
    measurement_payload = geometry.measurements.to_payload()
    measurement_payload["measurement_source"] = geometry.measurement_source
    measurement_payload["measurement_evidence"] = dict(geometry.evidence)

    return InspectionSnapshot(
        inspection_id=inspection_id,
        product_code=product_code,
        product_spec_version=_product_spec_version(product_spec),
        phase=final_decision.phase,
        decision=final_decision.decision,
        reason_codes=list(final_decision.reason_codes),
        measurements=InspectionMeasurements.from_payload(measurement_payload),
        observations=list(observations),
        phase_results=[phase_result.to_payload() for phase_result in phase_results],
        created_at=frame.captured_at,
    )


def _resolve_intake_geometry(payload: dict[str, Any], *, calibration: Any) -> GeometryMeasurementResolution:
    has_measurements = "measurements" in payload
    has_boundary = "boundary" in payload
    if has_measurements == has_boundary:
        raise ValidationError("exactly one of measurements or boundary is required")
    if has_measurements:
        return resolve_geometry_measurements(_require_object(payload["measurements"], "measurements"))
    return resolve_geometry_from_boundary(_require_object(payload["boundary"], "boundary"), calibration=calibration)


def _coerce_observations(values: Any) -> tuple[DetectorObservation, ...]:
    if values is None:
        return ()
    if not isinstance(values, list):
        raise ValidationError("observations must be a list")
    return tuple(DetectorObservation.from_payload(value) for value in values)


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


def _product_spec_version(product_spec: Any) -> str:
    group_id = str(product_spec.group_id or "unmatched").strip()
    return f"{product_spec.approval_status}:{group_id}"


def _reject_forbidden_request_fields(value: Any, *, path: str = "payload") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            if key in FORBIDDEN_REQUEST_FIELDS:
                raise ValidationError(f"{path}.{key} is not allowed")
            _reject_forbidden_request_fields(child, path=f"{path}.{key}")
        return
    if isinstance(value, list):
        for index, child in enumerate(value):
            _reject_forbidden_request_fields(child, path=f"{path}[{index}]")


def _require_field(payload: dict[str, Any], field_name: str, *, prefix: str = "") -> Any:
    if field_name not in payload:
        qualified = f"{prefix}.{field_name}" if prefix else field_name
        raise ValidationError(f"{qualified} is required")
    return payload[field_name]


def _require_non_empty(value: Any, field_name: str) -> str:
    normalized = str(value).strip()
    if not normalized:
        raise ValidationError(f"{field_name} is required")
    return normalized


def _require_object(value: Any, field_name: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValidationError(f"{field_name} must be an object")
    return dict(value)


def _unique_codes(codes: list[str]) -> tuple[str, ...]:
    unique: list[str] = []
    for code in codes:
        if code and code not in unique:
            unique.append(code)
    return tuple(unique)
