from __future__ import annotations

from dataclasses import dataclass

from apps.flange_qc_v2.domain import DECISION_STATES, PHASE_STATES, ValidationError


CORE_RULE_IDS = (
    "M1-SOP-6.1-LENGTH-001",
    "M1-SOP-6.1-WIDTH-001",
    "M1-SOP-6.1-DIAGONAL-001",
    "M1-SOP-6.1-DIAGONAL-002",
    "M1-SOP-6.4-PUNCH-MARK-001",
    "M1-SOP-6.2-PUNCH-OFFSET-001",
    "M1-SOP-7.3-SEAM-CURVATURE-001",
    "M1-SOP-7.3-CORNER-BEND-001",
    "M1-SOP-9.2-SKIPPED-STITCH-001",
    "M1-SOP-9.1-TORN-TOP-001",
    "M1-SOP-9.3-FABRIC-DEFECT-001",
    "M1-SOP-9.4-FABRIC-FOLD-001",
    "M1-SOP-9.5-FOAM-GAP-001",
    "M1-SOP-8.WRINKLE-*",
)


@dataclass(frozen=True)
class SopRule:
    rule_id: str
    phase: str
    category: str
    description: str
    authority: str
    safe_fallback_decision: str
    reason_code: str
    production_enabled: bool = False

    def __post_init__(self) -> None:
        if self.rule_id not in CORE_RULE_IDS:
            raise ValidationError(f"unknown SOP rule: {self.rule_id}")
        if self.phase not in PHASE_STATES:
            raise ValidationError(f"unknown phase: {self.phase}")
        if self.safe_fallback_decision not in DECISION_STATES:
            raise ValidationError(f"unknown decision: {self.safe_fallback_decision}")
        if self.production_enabled:
            raise ValidationError("SOP production rules are not enabled in bootstrap registry")


@dataclass(frozen=True)
class ReasonCode:
    code: str
    decision: str
    description: str
    severity: str

    def __post_init__(self) -> None:
        if self.decision not in DECISION_STATES:
            raise ValidationError(f"unknown decision: {self.decision}")
        if self.decision == "PASS":
            raise ValidationError("reason codes must not map to PASS")


REASON_CODES = (
    ReasonCode(
        code="PRODUCT_SPEC_APPROVAL_MISSING",
        decision="BLOCKED",
        description="Product specs are draft and require QC/domain owner approval.",
        severity="blocker",
    ),
    ReasonCode(
        code="UNKNOWN_PRODUCT",
        decision="BLOCKED",
        description="Product code or size is not present in the approved spec registry.",
        severity="blocker",
    ),
    ReasonCode(
        code="UNKNOWN_SIZE",
        decision="BLOCKED",
        description="Size group is not present for the resolved product spec.",
        severity="blocker",
    ),
    ReasonCode(
        code="CALIBRATION_MISSING",
        decision="BLOCKED",
        description="Camera or measurement calibration is missing, pending, or failed.",
        severity="blocker",
    ),
    ReasonCode(
        code="MEASUREMENTS_INCOMPLETE",
        decision="BLOCKED",
        description="Required length, width, or diagonal measurement points are incomplete.",
        severity="blocker",
    ),
    ReasonCode(
        code="DIAGONAL_DEVIATION_EXCEEDS_LIMIT",
        decision="NG",
        description="Shadow phase-2 diagonal deviation evidence is greater than the configured limit.",
        severity="reject",
    ),
    ReasonCode(
        code="MODEL_MISSING",
        decision="NOT_EVALUATED",
        description="Model-dependent rule cannot be evaluated because no approved model is available.",
        severity="warning",
    ),
    ReasonCode(
        code="MODEL_REVIEW_REQUIRED",
        decision="ASSIST",
        description="Model/vision output requires supervised QC review before production authority.",
        severity="review",
    ),
    ReasonCode(
        code="RULE_POST_MVP_DISABLED",
        decision="NOT_EVALUATED",
        description="The rule is documented but outside the enabled MVP evaluation set.",
        severity="info",
    ),
    ReasonCode(
        code="SOP_TOLERANCE_APPROVAL_MISSING",
        decision="BLOCKED",
        description="SOP tolerance has not been approved for production PASS/NG decisions.",
        severity="blocker",
    ),
)


_REASON_BY_CODE = {reason.code: reason for reason in REASON_CODES}


_RULES = (
    SopRule(
        rule_id="M1-SOP-6.1-LENGTH-001",
        phase="PHASE_1",
        category="measurement",
        description="Measure 3 length points, persist raw points and aggregate.",
        authority="deterministic_after_calibration_and_approved_config",
        safe_fallback_decision="BLOCKED",
        reason_code="MEASUREMENTS_INCOMPLETE",
    ),
    SopRule(
        rule_id="M1-SOP-6.1-WIDTH-001",
        phase="PHASE_1",
        category="measurement",
        description="Measure 3 width points, persist raw points and aggregate.",
        authority="deterministic_after_calibration_and_approved_config",
        safe_fallback_decision="BLOCKED",
        reason_code="MEASUREMENTS_INCOMPLETE",
    ),
    SopRule(
        rule_id="M1-SOP-6.1-DIAGONAL-001",
        phase="PHASE_2",
        category="measurement",
        description="Measure 2 diagonals and persist values in inches.",
        authority="deterministic_after_calibration",
        safe_fallback_decision="BLOCKED",
        reason_code="MEASUREMENTS_INCOMPLETE",
    ),
    SopRule(
        rule_id="M1-SOP-6.1-DIAGONAL-002",
        phase="PHASE_2",
        category="measurement",
        description="Diagonal deviation rule metadata; production NG authority remains gated.",
        authority="deterministic_after_calibration",
        safe_fallback_decision="BLOCKED",
        reason_code="SOP_TOLERANCE_APPROVAL_MISSING",
    ),
    SopRule(
        rule_id="M1-SOP-6.4-PUNCH-MARK-001",
        phase="PHASE_3",
        category="vision",
        description="Top has 4 corner marks and 2 mid-width marks.",
        authority="model_vision_dependent_until_approved",
        safe_fallback_decision="ASSIST",
        reason_code="MODEL_REVIEW_REQUIRED",
    ),
    SopRule(
        rule_id="M1-SOP-6.2-PUNCH-OFFSET-001",
        phase="PHASE_3",
        category="vision",
        description="Punch mark offset rule metadata; model output needs approval.",
        authority="model_vision_dependent_until_approved",
        safe_fallback_decision="ASSIST",
        reason_code="MODEL_REVIEW_REQUIRED",
    ),
    SopRule(
        rule_id="M1-SOP-7.3-SEAM-CURVATURE-001",
        phase="PHASE_4",
        category="post_mvp",
        description="Seam edge curvature rule documented for future enablement.",
        authority="post_mvp_disabled_until_enabled",
        safe_fallback_decision="NOT_EVALUATED",
        reason_code="RULE_POST_MVP_DISABLED",
    ),
    SopRule(
        rule_id="M1-SOP-7.3-CORNER-BEND-001",
        phase="PHASE_4",
        category="post_mvp",
        description="Corner bend rule documented for future enablement.",
        authority="post_mvp_disabled_until_enabled",
        safe_fallback_decision="NOT_EVALUATED",
        reason_code="RULE_POST_MVP_DISABLED",
    ),
    SopRule(
        rule_id="M1-SOP-9.2-SKIPPED-STITCH-001",
        phase="PHASE_4",
        category="assist",
        description="Skipped or loose stitches are unacceptable, pending approved evaluator.",
        authority="assist_or_not_evaluated_until_approved",
        safe_fallback_decision="ASSIST",
        reason_code="MODEL_REVIEW_REQUIRED",
    ),
    SopRule(
        rule_id="M1-SOP-9.1-TORN-TOP-001",
        phase="PHASE_4",
        category="assist",
        description="Visible tear unacceptable, pending approved evaluator.",
        authority="assist_or_not_evaluated_until_approved",
        safe_fallback_decision="ASSIST",
        reason_code="MODEL_REVIEW_REQUIRED",
    ),
    SopRule(
        rule_id="M1-SOP-9.3-FABRIC-DEFECT-001",
        phase="PHASE_4",
        category="assist",
        description="Fabric defect unacceptable, pending approved evaluator.",
        authority="assist_or_not_evaluated_until_approved",
        safe_fallback_decision="ASSIST",
        reason_code="MODEL_REVIEW_REQUIRED",
    ),
    SopRule(
        rule_id="M1-SOP-9.4-FABRIC-FOLD-001",
        phase="PHASE_4",
        category="assist",
        description="Fabric folding during sewing unacceptable, pending approved evaluator.",
        authority="assist_or_not_evaluated_until_approved",
        safe_fallback_decision="ASSIST",
        reason_code="MODEL_REVIEW_REQUIRED",
    ),
    SopRule(
        rule_id="M1-SOP-9.5-FOAM-GAP-001",
        phase="PHASE_4",
        category="post_mvp",
        description="Foam joint gap rule documented for future enablement.",
        authority="post_mvp_disabled_until_enabled",
        safe_fallback_decision="NOT_EVALUATED",
        reason_code="RULE_POST_MVP_DISABLED",
    ),
    SopRule(
        rule_id="M1-SOP-8.WRINKLE-*",
        phase="PHASE_4",
        category="post_mvp",
        description="Product-specific wrinkle rules remain outside MVP.",
        authority="post_mvp_disabled_until_enabled",
        safe_fallback_decision="NOT_EVALUATED",
        reason_code="RULE_POST_MVP_DISABLED",
    ),
)


_RULE_BY_ID = {rule.rule_id: rule for rule in _RULES}


def list_rules() -> tuple[SopRule, ...]:
    return _RULES


def get_rule(rule_id: str) -> SopRule:
    try:
        return _RULE_BY_ID[rule_id]
    except KeyError as exc:
        raise ValidationError(f"unknown SOP rule: {rule_id}") from exc


def get_reason_code(code: str) -> ReasonCode:
    try:
        return _REASON_BY_CODE[code]
    except KeyError as exc:
        raise ValidationError(f"unknown reason code: {code}") from exc
