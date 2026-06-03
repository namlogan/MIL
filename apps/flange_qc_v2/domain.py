from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


DECISION_STATES = ("PASS", "NG", "BLOCKED", "NOT_EVALUATED", "ASSIST")
PHASE_STATES = ("BOOTSTRAP", "PHASE_1", "PHASE_2", "PHASE_3", "PHASE_4", "FINAL")
MEASUREMENT_UNITS = ("inch", "mm")
BOOTSTRAP_SUBSYSTEM_STATES = {
    "camera": "unavailable",
    "gpu": "unavailable",
    "model": "unavailable",
    "product_specs": "draft_requires_qc_owner_approval",
    "sop_decision_engine": "shadow_implemented_requires_qc_sop_approval",
    "audit_db": "not_configured",
    "replay_source": "not_configured",
}


class ValidationError(ValueError):
    """Raised when a Flange QC v2 domain payload violates its contract."""


def _require_non_empty(value: str, field_name: str) -> str:
    normalized = str(value).strip()
    if not normalized:
        raise ValidationError(f"{field_name} is required")
    return normalized


def _require_unit_interval(value: float, field_name: str) -> float:
    number = float(value)
    if number < 0 or number > 1:
        raise ValidationError(f"{field_name} values must be between 0 and 1")
    return number


def _coerce_number_list(values: list[float] | tuple[float, ...], field_name: str) -> list[float]:
    if not isinstance(values, (list, tuple)):
        raise ValidationError(f"{field_name} must be a list")
    return [float(value) for value in values]


@dataclass(frozen=True)
class BoundingBox:
    x: float
    y: float
    width: float
    height: float

    def __post_init__(self) -> None:
        for field_name in ("x", "y", "width", "height"):
            object.__setattr__(self, field_name, _require_unit_interval(getattr(self, field_name), "bbox"))

    def to_list(self) -> list[float]:
        return [self.x, self.y, self.width, self.height]

    @classmethod
    def from_payload(cls, payload: Any) -> "BoundingBox":
        if not isinstance(payload, list) or len(payload) != 4:
            raise ValidationError("bbox must contain 4 values")
        return cls(x=payload[0], y=payload[1], width=payload[2], height=payload[3])


@dataclass(frozen=True)
class DetectorObservation:
    label: str
    confidence: float
    bbox: BoundingBox
    model_ref: str = ""
    evidence_ref: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(self, "label", _require_non_empty(self.label, "observation label"))
        object.__setattr__(self, "confidence", _require_unit_interval(self.confidence, "confidence"))

    def to_payload(self) -> dict[str, Any]:
        payload = {
            "label": self.label,
            "confidence": self.confidence,
            "bbox": self.bbox.to_list(),
        }
        if self.model_ref:
            payload["model_ref"] = self.model_ref
        if self.evidence_ref:
            payload["evidence_ref"] = self.evidence_ref
        return payload

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "DetectorObservation":
        if not isinstance(payload, dict):
            raise ValidationError("observation must be an object")
        return cls(
            label=payload.get("label", ""),
            confidence=payload.get("confidence", -1),
            bbox=BoundingBox.from_payload(payload.get("bbox")),
            model_ref=str(payload.get("model_ref", "")),
            evidence_ref=str(payload.get("evidence_ref", "")),
        )


@dataclass(frozen=True)
class SubsystemHealth:
    camera: str
    gpu: str
    model: str
    product_specs: str
    sop_decision_engine: str
    audit_db: str
    replay_source: str

    def __post_init__(self) -> None:
        for field_name in BOOTSTRAP_SUBSYSTEM_STATES:
            object.__setattr__(self, field_name, _require_non_empty(getattr(self, field_name), field_name))

    @classmethod
    def bootstrap(cls) -> "SubsystemHealth":
        return cls(**BOOTSTRAP_SUBSYSTEM_STATES)

    def to_payload(self) -> dict[str, str]:
        return {
            "camera": self.camera,
            "gpu": self.gpu,
            "model": self.model,
            "product_specs": self.product_specs,
            "sop_decision_engine": self.sop_decision_engine,
            "audit_db": self.audit_db,
            "replay_source": self.replay_source,
        }


@dataclass(frozen=True)
class InspectionMeasurements:
    length_points: list[float] = field(default_factory=list)
    width_points: list[float] = field(default_factory=list)
    diagonals: list[float] = field(default_factory=list)
    unit: str = "inch"
    measurement_source: str = "provided_measurements"
    measurement_evidence: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        length_points = _coerce_number_list(self.length_points, "length_points")
        width_points = _coerce_number_list(self.width_points, "width_points")
        diagonals = _coerce_number_list(self.diagonals, "diagonals")
        unit = str(self.unit).strip()
        if unit not in MEASUREMENT_UNITS:
            raise ValidationError(f"unknown measurement unit: {unit}")
        measurement_source = _require_non_empty(self.measurement_source, "measurement_source")
        if not isinstance(self.measurement_evidence, dict):
            raise ValidationError("measurement_evidence must be an object")
        has_measurements = bool(length_points or width_points or diagonals)
        if has_measurements:
            if len(length_points) != 3:
                raise ValidationError("length_points requires 3 values")
            if len(width_points) != 3:
                raise ValidationError("width_points requires 3 values")
            if len(diagonals) != 2:
                raise ValidationError("diagonals requires 2 values")
        object.__setattr__(self, "length_points", length_points)
        object.__setattr__(self, "width_points", width_points)
        object.__setattr__(self, "diagonals", diagonals)
        object.__setattr__(self, "unit", unit)
        object.__setattr__(self, "measurement_source", measurement_source)
        object.__setattr__(self, "measurement_evidence", dict(self.measurement_evidence))

    def to_payload(self) -> dict[str, Any]:
        return {
            "length_points": self.length_points,
            "width_points": self.width_points,
            "diagonals": self.diagonals,
            "unit": self.unit,
            "measurement_source": self.measurement_source,
            "measurement_evidence": dict(self.measurement_evidence),
        }

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "InspectionMeasurements":
        if not isinstance(payload, dict):
            raise ValidationError("measurements must be an object")
        return cls(
            length_points=payload.get("length_points", []),
            width_points=payload.get("width_points", []),
            diagonals=payload.get("diagonals", []),
            unit=payload.get("unit", "inch"),
            measurement_source=payload.get("measurement_source", "provided_measurements"),
            measurement_evidence=payload.get("measurement_evidence", {}),
        )


@dataclass(frozen=True)
class InspectionSnapshot:
    inspection_id: str
    product_code: str
    product_spec_version: str
    phase: str
    decision: str
    reason_codes: list[str]
    measurements: InspectionMeasurements = field(default_factory=InspectionMeasurements)
    observations: list[DetectorObservation] = field(default_factory=list)
    phase_results: list[dict[str, Any]] = field(default_factory=list)
    created_at: str = "not_recorded"

    def __post_init__(self) -> None:
        object.__setattr__(self, "inspection_id", _require_non_empty(self.inspection_id, "inspection_id"))
        object.__setattr__(self, "product_code", _require_non_empty(self.product_code, "product_code"))
        object.__setattr__(
            self,
            "product_spec_version",
            _require_non_empty(self.product_spec_version, "product_spec_version"),
        )
        phase = str(self.phase).strip()
        decision = str(self.decision).strip()
        if phase not in PHASE_STATES:
            raise ValidationError(f"unknown phase: {phase}")
        if decision not in DECISION_STATES:
            raise ValidationError(f"unknown decision: {decision}")
        object.__setattr__(self, "phase", phase)
        object.__setattr__(self, "decision", decision)
        object.__setattr__(self, "reason_codes", [str(code).strip() for code in self.reason_codes if str(code).strip()])
        object.__setattr__(self, "phase_results", _coerce_phase_results(self.phase_results))
        object.__setattr__(self, "created_at", _require_non_empty(self.created_at, "created_at"))

    @classmethod
    def bootstrap_blocked(
        cls,
        *,
        inspection_id: str,
        product_code: str,
        reason_codes: list[str],
    ) -> "InspectionSnapshot":
        return cls(
            inspection_id=inspection_id,
            product_code=product_code,
            product_spec_version="draft_unapproved",
            phase="BOOTSTRAP",
            decision="BLOCKED",
            reason_codes=reason_codes,
        )

    def to_payload(self) -> dict[str, Any]:
        return {
            "event_type": "inspection.snapshot",
            "inspection_id": self.inspection_id,
            "product": {
                "code": self.product_code,
                "spec_version": self.product_spec_version,
            },
            "phase": self.phase,
            "decision": self.decision,
            "reason_codes": self.reason_codes,
            "phase_results": [dict(phase_result) for phase_result in self.phase_results],
            "measurements": self.measurements.to_payload(),
            "observations": [observation.to_payload() for observation in self.observations],
            "created_at": self.created_at,
        }

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "InspectionSnapshot":
        if not isinstance(payload, dict):
            raise ValidationError("inspection snapshot must be an object")
        if payload.get("event_type") != "inspection.snapshot":
            raise ValidationError("event_type must be inspection.snapshot")
        product = payload.get("product")
        if not isinstance(product, dict):
            raise ValidationError("product must be an object")
        return cls(
            inspection_id=payload.get("inspection_id", ""),
            product_code=product.get("code", ""),
            product_spec_version=product.get("spec_version", ""),
            phase=payload.get("phase", ""),
            decision=payload.get("decision", ""),
            reason_codes=list(payload.get("reason_codes", [])),
            phase_results=list(payload.get("phase_results", [])),
            measurements=InspectionMeasurements.from_payload(payload.get("measurements", {})),
            observations=[
                DetectorObservation.from_payload(observation)
                for observation in payload.get("observations", [])
            ],
            created_at=payload.get("created_at", ""),
        )


def _coerce_phase_results(values: Any) -> list[dict[str, Any]]:
    if not isinstance(values, list):
        raise ValidationError("phase_results must be a list")
    normalized: list[dict[str, Any]] = []
    for value in values:
        if not isinstance(value, dict):
            raise ValidationError("phase_results entries must be objects")
        normalized.append(dict(value))
    return normalized
