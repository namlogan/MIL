from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from apps.flange_qc_v2.calibration import CalibrationConfig
from apps.flange_qc_v2.domain import DECISION_STATES, PHASE_STATES, ValidationError
from apps.flange_qc_v2.geometry import GeometryMeasurementResolution
from apps.flange_qc_v2.product_specs import ProductSpecResolution
from apps.flange_qc_v2.sop_registry import get_reason_code


PHASE_TWO_DIAGONAL_THRESHOLD_IN = 0.5
PHASE_ONE_LENGTH_RULE_ID = "M1-SOP-6.1-LENGTH-001"
PHASE_ONE_WIDTH_RULE_ID = "M1-SOP-6.1-WIDTH-001"
PHASE_TWO_DIAGONAL_RULE_ID = "M1-SOP-6.1-DIAGONAL-002"
SOP_AUTHORITY_BLOCKER = "SOP_TOLERANCE_APPROVAL_MISSING"
BOOTSTRAP_AGGREGATE_METHOD = "all_points_must_pass_bootstrap"
MM_PER_INCH = 25.4


@dataclass(frozen=True)
class RuleResult:
    rule_id: str
    phase: str
    decision: str
    reason_codes: tuple[str, ...]
    evidence: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.phase not in PHASE_STATES:
            raise ValidationError(f"unknown phase: {self.phase}")
        if self.decision not in DECISION_STATES:
            raise ValidationError(f"unknown decision: {self.decision}")
        for code in self.reason_codes:
            get_reason_code(code)

    def to_payload(self) -> dict[str, Any]:
        return {
            "rule_id": self.rule_id,
            "phase": self.phase,
            "decision": self.decision,
            "reason_codes": list(self.reason_codes),
            "evidence": dict(self.evidence),
        }


@dataclass(frozen=True)
class DecisionResult:
    phase: str
    decision: str
    reason_codes: tuple[str, ...]
    authority_blockers: tuple[str, ...] = ()
    rule_results: tuple[RuleResult, ...] = ()
    production_authority: bool = False
    shadow_mode: bool = False

    def __post_init__(self) -> None:
        if self.phase not in PHASE_STATES:
            raise ValidationError(f"unknown phase: {self.phase}")
        if self.decision not in DECISION_STATES:
            raise ValidationError(f"unknown decision: {self.decision}")
        if self.production_authority:
            raise ValidationError("decision engine cannot approve production authority")
        for code in self.reason_codes:
            get_reason_code(code)
        for code in self.authority_blockers:
            get_reason_code(code)

    def to_payload(self) -> dict[str, Any]:
        return {
            "phase": self.phase,
            "decision": self.decision,
            "reason_codes": list(self.reason_codes),
            "authority_blockers": list(self.authority_blockers),
            "production_authority": self.production_authority,
            "shadow_mode": self.shadow_mode,
            "rule_results": [rule_result.to_payload() for rule_result in self.rule_results],
        }


def evaluate_phase_two_geometry(
    *,
    product_spec: ProductSpecResolution,
    calibration: CalibrationConfig,
    geometry: GeometryMeasurementResolution,
) -> DecisionResult:
    blockers = _unique_codes(
        list(product_spec.reason_codes)
        + list(calibration.reason_codes)
        + _geometry_blockers(geometry)
    )
    if blockers:
        return DecisionResult(
            phase="PHASE_2",
            decision="BLOCKED",
            reason_codes=blockers,
            shadow_mode=False,
        )

    if geometry.diagonal_deviation is None:
        return DecisionResult(
            phase="PHASE_2",
            decision="BLOCKED",
            reason_codes=("MEASUREMENTS_INCOMPLETE",),
            shadow_mode=False,
        )

    decision = "NG" if geometry.diagonal_deviation > PHASE_TWO_DIAGONAL_THRESHOLD_IN else "PASS"
    reason_codes: tuple[str, ...] = (
        ("DIAGONAL_DEVIATION_EXCEEDS_LIMIT",) if decision == "NG" else ()
    )
    rule_result = RuleResult(
        rule_id=PHASE_TWO_DIAGONAL_RULE_ID,
        phase="PHASE_2",
        decision=decision,
        reason_codes=reason_codes,
        evidence={
            "diagonal_deviation_in": geometry.diagonal_deviation,
            "threshold_in": PHASE_TWO_DIAGONAL_THRESHOLD_IN,
            "unit": geometry.measurements.unit,
        },
    )
    return DecisionResult(
        phase="PHASE_2",
        decision=decision,
        reason_codes=reason_codes,
        authority_blockers=(SOP_AUTHORITY_BLOCKER,),
        rule_results=(rule_result,),
        production_authority=False,
        shadow_mode=True,
    )


def evaluate_phase_one_measurements(
    *,
    product_spec: ProductSpecResolution,
    calibration: CalibrationConfig,
    geometry: GeometryMeasurementResolution,
) -> DecisionResult:
    blockers = _unique_codes(
        list(product_spec.reason_codes)
        + list(calibration.reason_codes)
        + _geometry_blockers(geometry)
    )
    if blockers:
        return DecisionResult(
            phase="PHASE_1",
            decision="BLOCKED",
            reason_codes=blockers,
            shadow_mode=False,
        )

    length_result = _evaluate_dimension_rule(
        rule_id=PHASE_ONE_LENGTH_RULE_ID,
        points=geometry.measurements.length_points,
        unit=geometry.measurements.unit,
        nominal_in=product_spec.nominal_length_in,
        plus_in=product_spec.length_plus_in,
        minus_in=product_spec.length_minus_in,
        out_of_tolerance_reason="LENGTH_OUT_OF_TOLERANCE",
    )
    width_result = _evaluate_dimension_rule(
        rule_id=PHASE_ONE_WIDTH_RULE_ID,
        points=geometry.measurements.width_points,
        unit=geometry.measurements.unit,
        nominal_in=product_spec.nominal_width_in,
        plus_in=product_spec.width_plus_in,
        minus_in=product_spec.width_minus_in,
        out_of_tolerance_reason="WIDTH_OUT_OF_TOLERANCE",
    )
    rule_results = (length_result, width_result)
    reason_codes = _unique_codes(
        [
            code
            for rule_result in rule_results
            for code in rule_result.reason_codes
        ]
    )
    return DecisionResult(
        phase="PHASE_1",
        decision="NG" if reason_codes else "PASS",
        reason_codes=reason_codes,
        authority_blockers=(SOP_AUTHORITY_BLOCKER,),
        rule_results=rule_results,
        production_authority=False,
        shadow_mode=True,
    )


def _geometry_blockers(geometry: GeometryMeasurementResolution) -> list[str]:
    return [
        code
        for code in geometry.reason_codes
        if code != SOP_AUTHORITY_BLOCKER
    ]


def _evaluate_dimension_rule(
    *,
    rule_id: str,
    points: list[float],
    unit: str,
    nominal_in: float | None,
    plus_in: float | None,
    minus_in: float | None,
    out_of_tolerance_reason: str,
) -> RuleResult:
    if nominal_in is None or plus_in is None or minus_in is None:
        raise ValidationError("phase-one dimension rule requires resolved product spec values")

    points_in = _points_to_inches(points, unit)
    lower_bound_in = nominal_in - minus_in
    upper_bound_in = nominal_in + plus_in
    out_of_tolerance_indexes = [
        index
        for index, value in enumerate(points_in)
        if value < lower_bound_in or value > upper_bound_in
    ]
    decision = "NG" if out_of_tolerance_indexes else "PASS"
    reason_codes: tuple[str, ...] = (
        (out_of_tolerance_reason,) if out_of_tolerance_indexes else ()
    )
    return RuleResult(
        rule_id=rule_id,
        phase="PHASE_1",
        decision=decision,
        reason_codes=reason_codes,
        evidence={
            "aggregate_method": BOOTSTRAP_AGGREGATE_METHOD,
            "source_unit": unit,
            "unit": "inch",
            "points_in": points_in,
            "nominal_in": nominal_in,
            "tolerance_plus_in": plus_in,
            "tolerance_minus_in": minus_in,
            "lower_bound_in": lower_bound_in,
            "upper_bound_in": upper_bound_in,
            "min_in": min(points_in),
            "max_in": max(points_in),
            "average_in": sum(points_in) / len(points_in),
            "out_of_tolerance_point_indexes": out_of_tolerance_indexes,
        },
    )


def _points_to_inches(points: list[float], unit: str) -> list[float]:
    if unit == "inch":
        return list(points)
    if unit == "mm":
        return [point / MM_PER_INCH for point in points]
    raise ValidationError(f"unsupported phase-one measurement unit: {unit}")


def _unique_codes(codes: list[str]) -> tuple[str, ...]:
    unique: list[str] = []
    for code in codes:
        if code and code not in unique:
            unique.append(code)
    return tuple(unique)
