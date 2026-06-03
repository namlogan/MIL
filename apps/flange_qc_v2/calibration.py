from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from apps.flange_qc_v2.domain import DECISION_STATES, ValidationError
from apps.flange_qc_v2.sop_registry import get_reason_code


@dataclass(frozen=True)
class CalibrationConfig:
    schema_version: int
    status: str
    approved_for_production: bool
    source_ref: str
    camera: dict[str, Any]
    lighting: dict[str, Any]
    production_authority: bool
    decision: str
    reason_codes: list[str]
    geometry: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.decision not in DECISION_STATES:
            raise ValidationError(f"unknown decision: {self.decision}")
        for code in self.reason_codes:
            get_reason_code(code)


def load_calibration_config(path: str | Path) -> CalibrationConfig:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValidationError("calibration config must be an object")
    _validate_config(data)
    production_authority = bool(data["approved_for_production"]) and str(data["status"]) == "approved"
    return CalibrationConfig(
        schema_version=int(data["schema_version"]),
        status=str(data["status"]),
        approved_for_production=bool(data["approved_for_production"]),
        source_ref=str(data["source_ref"]),
        camera=dict(data["camera"]),
        lighting=dict(data["lighting"]),
        production_authority=production_authority,
        decision="NOT_EVALUATED" if production_authority else "BLOCKED",
        reason_codes=[] if production_authority else ["CALIBRATION_MISSING"],
        geometry=dict(data.get("geometry", {})),
    )


def _validate_config(data: dict[str, Any]) -> None:
    for field in ("schema_version", "status", "approved_for_production", "source_ref", "camera", "lighting"):
        if field not in data:
            raise ValidationError(f"{field} is required")
    camera = data["camera"]
    if not isinstance(camera, dict):
        raise ValidationError("camera must be an object")
    for field in ("mount", "working_distance_meters", "lens", "focus_locked", "iris_locked"):
        if field not in camera:
            raise ValidationError(f"camera.{field} is required")
    _coerce_positive_number(camera["working_distance_meters"], "camera.working_distance_meters")
    lighting = data["lighting"]
    if not isinstance(lighting, dict):
        raise ValidationError("lighting must be an object")
    for field in ("layout", "angle_degrees_min", "angle_degrees_max", "diffuser_required"):
        if field not in lighting:
            raise ValidationError(f"lighting.{field} is required")
    min_angle = _coerce_positive_number(lighting["angle_degrees_min"], "lighting.angle_degrees_min")
    max_angle = _coerce_positive_number(lighting["angle_degrees_max"], "lighting.angle_degrees_max")
    if min_angle > max_angle:
        raise ValidationError("lighting angle minimum must be <= maximum")
    geometry = data.get("geometry", {})
    if geometry:
        if not isinstance(geometry, dict):
            raise ValidationError("geometry must be an object")
        for field in ("source_units", "inch_per_pixel", "method"):
            if field not in geometry:
                raise ValidationError(f"geometry.{field} is required")
        if str(geometry["source_units"]) != "pixel":
            raise ValidationError("geometry.source_units must be pixel")
        _coerce_positive_number(geometry["inch_per_pixel"], "geometry.inch_per_pixel")
        if not str(geometry["method"]).strip():
            raise ValidationError("geometry.method is required")


def _coerce_positive_number(value: Any, field_name: str) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ValidationError(f"{field_name} must be a number") from exc
    if number <= 0:
        raise ValidationError(f"{field_name} must be positive")
    return number
