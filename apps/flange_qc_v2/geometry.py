from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from apps.flange_qc_v2.domain import (
    DECISION_STATES,
    MEASUREMENT_UNITS,
    InspectionMeasurements,
    ValidationError,
)


CONTRACT_VERSION = "geometry.measurement_set.v1"
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
