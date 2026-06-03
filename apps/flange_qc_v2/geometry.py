from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any

from apps.flange_qc_v2.calibration import CalibrationConfig
from apps.flange_qc_v2.domain import (
    DECISION_STATES,
    MEASUREMENT_UNITS,
    InspectionMeasurements,
    ValidationError,
)


CONTRACT_VERSION = "geometry.measurement_set.v1"
BOUNDARY_MEASUREMENT_SOURCE = "boundary_corners_calibrated_shadow"
PROVIDED_MEASUREMENT_SOURCE = "provided_measurements"
BOUNDARY_SAMPLE_FRACTIONS = (0.0, 0.5, 1.0)
EXPECTED_COUNTS = {
    "length_points": 3,
    "width_points": 3,
    "diagonals": 2,
}


def _coerce_number_list(payload: dict[str, Any], field_name: str) -> list[float]:
    values = payload.get(field_name, [])
    if not isinstance(values, (list, tuple)):
        raise ValidationError(f"{field_name} must be a list")
    return [float(value) for value in values]


def _coerce_unit(payload: dict[str, Any]) -> str:
    unit = str(payload.get("unit", "inch")).strip()
    if unit not in MEASUREMENT_UNITS:
        raise ValidationError(f"unknown measurement unit: {unit}")
    return unit


@dataclass(frozen=True)
class GeometryMeasurementResolution:
    measurements: InspectionMeasurements
    decision: str
    reason_codes: tuple[str, ...]
    received_counts: dict[str, int]
    diagonal_deviation: float | None
    expected_counts: dict[str, int] = field(default_factory=lambda: dict(EXPECTED_COUNTS))
    production_authority: bool = False
    contract_version: str = CONTRACT_VERSION
    measurement_source: str = PROVIDED_MEASUREMENT_SOURCE
    evidence: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.decision not in DECISION_STATES:
            raise ValidationError(f"unknown decision: {self.decision}")
        if self.production_authority:
            raise ValidationError("geometry contract cannot approve production authority")
        if not self.reason_codes:
            raise ValidationError("geometry resolution requires at least one reason code")

    def to_payload(self) -> dict[str, Any]:
        return {
            "contract_version": self.contract_version,
            "decision": self.decision,
            "reason_codes": list(self.reason_codes),
            "production_authority": self.production_authority,
            "measurements": self.measurements.to_payload(),
            "expected_counts": dict(self.expected_counts),
            "received_counts": dict(self.received_counts),
            "diagonal_deviation": self.diagonal_deviation,
            "measurement_source": self.measurement_source,
            "evidence": dict(self.evidence),
        }


def resolve_geometry_measurements(payload: dict[str, Any]) -> GeometryMeasurementResolution:
    if not isinstance(payload, dict):
        raise ValidationError("geometry measurements must be an object")

    unit = _coerce_unit(payload)
    length_points = _coerce_number_list(payload, "length_points")
    width_points = _coerce_number_list(payload, "width_points")
    diagonals = _coerce_number_list(payload, "diagonals")
    received_counts = {
        "length_points": len(length_points),
        "width_points": len(width_points),
        "diagonals": len(diagonals),
    }

    if received_counts != EXPECTED_COUNTS:
        return GeometryMeasurementResolution(
            measurements=InspectionMeasurements(unit=unit),
            decision="BLOCKED",
            reason_codes=("MEASUREMENTS_INCOMPLETE",),
            received_counts=received_counts,
            diagonal_deviation=None,
        )

    measurements = InspectionMeasurements(
        length_points=length_points,
        width_points=width_points,
        diagonals=diagonals,
        unit=unit,
    )
    return GeometryMeasurementResolution(
        measurements=measurements,
        decision="BLOCKED",
        reason_codes=("SOP_TOLERANCE_APPROVAL_MISSING",),
        received_counts=received_counts,
        diagonal_deviation=abs(diagonals[0] - diagonals[1]),
    )


def resolve_geometry_from_boundary(
    payload: dict[str, Any],
    *,
    calibration: CalibrationConfig,
) -> GeometryMeasurementResolution:
    if not isinstance(payload, dict):
        raise ValidationError("boundary geometry must be an object")

    inch_per_pixel = _inch_per_pixel(calibration)
    method = str(calibration.geometry.get("method", "")).strip()
    corners_payload = payload.get("corners")
    if not isinstance(corners_payload, dict):
        raise ValidationError("boundary corners are required")

    top_left = _point(corners_payload, "top_left")
    top_right = _point(corners_payload, "top_right")
    bottom_right = _point(corners_payload, "bottom_right")
    bottom_left = _point(corners_payload, "bottom_left")

    length_points = [
        _rounded_distance(
            _interpolate(top_left, bottom_left, fraction),
            _interpolate(top_right, bottom_right, fraction),
            inch_per_pixel,
        )
        for fraction in BOUNDARY_SAMPLE_FRACTIONS
    ]
    width_points = [
        _rounded_distance(
            _interpolate(top_left, top_right, fraction),
            _interpolate(bottom_left, bottom_right, fraction),
            inch_per_pixel,
        )
        for fraction in BOUNDARY_SAMPLE_FRACTIONS
    ]
    diagonals = [
        _rounded_distance(top_left, bottom_right, inch_per_pixel),
        _rounded_distance(top_right, bottom_left, inch_per_pixel),
    ]
    measurements = {
        "length_points": length_points,
        "width_points": width_points,
        "diagonals": diagonals,
        "unit": "inch",
    }
    resolved = resolve_geometry_measurements(measurements)
    return GeometryMeasurementResolution(
        measurements=resolved.measurements,
        decision=resolved.decision,
        reason_codes=resolved.reason_codes,
        received_counts=resolved.received_counts,
        diagonal_deviation=resolved.diagonal_deviation,
        measurement_source=BOUNDARY_MEASUREMENT_SOURCE,
        evidence={
            "boundary_source": str(payload.get("source", "boundary_corners")),
            "calibration_source_ref": calibration.source_ref,
            "calibration_method": method,
            "source_units": calibration.geometry.get("source_units"),
            "inch_per_pixel": inch_per_pixel,
            "sample_fractions": list(BOUNDARY_SAMPLE_FRACTIONS),
            "corner_order": ["top_left", "top_right", "bottom_right", "bottom_left"],
        },
    )


def _inch_per_pixel(calibration: CalibrationConfig) -> float:
    geometry = calibration.geometry
    if not isinstance(geometry, dict) or "inch_per_pixel" not in geometry:
        raise ValidationError("calibration.geometry.inch_per_pixel is required")
    try:
        inch_per_pixel = float(geometry["inch_per_pixel"])
    except (TypeError, ValueError) as exc:
        raise ValidationError("calibration.geometry.inch_per_pixel must be a number") from exc
    if inch_per_pixel <= 0:
        raise ValidationError("calibration.geometry.inch_per_pixel must be positive")
    if str(geometry.get("source_units", "")).strip() != "pixel":
        raise ValidationError("calibration.geometry.source_units must be pixel")
    return inch_per_pixel


def _point(corners: dict[str, Any], name: str) -> tuple[float, float]:
    value = corners.get(name)
    if not isinstance(value, (list, tuple)) or len(value) != 2:
        raise ValidationError(f"boundary corner {name} must contain 2 values")
    return (float(value[0]), float(value[1]))


def _interpolate(first: tuple[float, float], second: tuple[float, float], fraction: float) -> tuple[float, float]:
    return (
        first[0] + (second[0] - first[0]) * fraction,
        first[1] + (second[1] - first[1]) * fraction,
    )


def _rounded_distance(first: tuple[float, float], second: tuple[float, float], inch_per_pixel: float) -> float:
    return round(math.dist(first, second) * inch_per_pixel, 6)
