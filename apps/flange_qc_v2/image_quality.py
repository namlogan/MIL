from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from apps.flange_qc_v2.domain import DECISION_STATES, ValidationError
from apps.flange_qc_v2.sop_registry import get_reason_code


CONTRACT_VERSION = "image_quality.gate.v1"
AUTHORITY_BLOCKERS = ("IMAGE_QUALITY_APPROVAL_REQUIRED", "PRODUCTION_APPROVAL_REQUIRED")
ALLOWED_SOURCE_PREFIXES = ("synthetic://", "replay://")


def _require_field(payload: dict[str, Any], field_name: str) -> Any:
    if field_name not in payload:
        raise ValidationError(f"{field_name} is required")
    return payload[field_name]


def _require_non_empty(value: Any, field_name: str) -> str:
    normalized = str(value).strip()
    if not normalized:
        raise ValidationError(f"{field_name} is required")
    return normalized


def _coerce_unit_score(value: Any, field_name: str) -> float:
    try:
        score = float(value)
    except (TypeError, ValueError) as exc:
        raise ValidationError(f"{field_name} must be between 0 and 1") from exc
    if score < 0 or score > 1:
        raise ValidationError(f"{field_name} must be between 0 and 1")
    return score


@dataclass(frozen=True)
class ImageQualityThresholds:
    brightness_min: float = 0.35
    sharpness_min: float = 0.4
    occlusion_assist_min: float = 0.2
    occlusion_block_min: float = 0.45

    def __post_init__(self) -> None:
        for field_name in (
            "brightness_min",
            "sharpness_min",
            "occlusion_assist_min",
            "occlusion_block_min",
        ):
            object.__setattr__(self, field_name, _coerce_unit_score(getattr(self, field_name), field_name))
        if self.occlusion_assist_min >= self.occlusion_block_min:
            raise ValidationError("occlusion_assist_min must be lower than occlusion_block_min")

    def to_payload(self) -> dict[str, float]:
        return {
            "brightness_min": self.brightness_min,
            "sharpness_min": self.sharpness_min,
            "occlusion_assist_min": self.occlusion_assist_min,
            "occlusion_block_min": self.occlusion_block_min,
        }


DEFAULT_IMAGE_QUALITY_THRESHOLDS = ImageQualityThresholds()


@dataclass(frozen=True)
class ImageQualityEvidence:
    frame_id: str
    source_uri: str
    captured_at: str
    brightness_score: float
    sharpness_score: float
    occlusion_score: float
    source_ref: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "frame_id", _require_non_empty(self.frame_id, "frame_id"))
        source_uri = _require_non_empty(self.source_uri, "source_uri")
        if not source_uri.startswith(ALLOWED_SOURCE_PREFIXES):
            raise ValidationError("source_uri must use synthetic:// or replay://")
        object.__setattr__(self, "source_uri", source_uri)
        object.__setattr__(self, "captured_at", _require_non_empty(self.captured_at, "captured_at"))
        object.__setattr__(self, "source_ref", _require_non_empty(self.source_ref, "source_ref"))
        for field_name in ("brightness_score", "sharpness_score", "occlusion_score"):
            object.__setattr__(self, field_name, _coerce_unit_score(getattr(self, field_name), field_name))

    @classmethod
    def from_payload(cls, payload: Any) -> "ImageQualityEvidence":
        if not isinstance(payload, dict):
            raise ValidationError("image quality payload must be an object")
        return cls(
            frame_id=_require_field(payload, "frame_id"),
            source_uri=_require_field(payload, "source_uri"),
            captured_at=_require_field(payload, "captured_at"),
            brightness_score=_require_field(payload, "brightness_score"),
            sharpness_score=_require_field(payload, "sharpness_score"),
            occlusion_score=_require_field(payload, "occlusion_score"),
            source_ref=_require_field(payload, "source_ref"),
        )

    def evidence_payload(self) -> dict[str, str]:
        return {
            "frame_id": self.frame_id,
            "source_uri": self.source_uri,
            "captured_at": self.captured_at,
            "source_ref": self.source_ref,
        }

    def score_payload(self) -> dict[str, float]:
        return {
            "brightness_score": self.brightness_score,
            "sharpness_score": self.sharpness_score,
            "occlusion_score": self.occlusion_score,
        }


@dataclass(frozen=True)
class ImageQualityResult:
    evidence: ImageQualityEvidence
    thresholds: ImageQualityThresholds
    decision: str
    reason_codes: tuple[str, ...]
    authority_blockers: tuple[str, ...] = AUTHORITY_BLOCKERS
    production_authority: bool = False
    shadow_mode: bool = True
    contract_version: str = CONTRACT_VERSION

    def __post_init__(self) -> None:
        if self.decision not in DECISION_STATES:
            raise ValidationError(f"unknown decision: {self.decision}")
        if self.decision not in ("PASS", "ASSIST", "BLOCKED"):
            raise ValidationError(f"image quality cannot emit decision: {self.decision}")
        if self.production_authority:
            raise ValidationError("image quality gate cannot approve production authority")
        for code in self.reason_codes + self.authority_blockers:
            get_reason_code(code)

    def to_payload(self) -> dict[str, Any]:
        return {
            "contract_version": self.contract_version,
            "decision": self.decision,
            "reason_codes": list(self.reason_codes),
            "authority_blockers": list(self.authority_blockers),
            "production_authority": self.production_authority,
            "shadow_mode": self.shadow_mode,
            "evidence": self.evidence.evidence_payload(),
            "quality_scores": self.evidence.score_payload(),
            "thresholds": self.thresholds.to_payload(),
        }


def evaluate_image_quality(
    payload: dict[str, Any],
    thresholds: ImageQualityThresholds = DEFAULT_IMAGE_QUALITY_THRESHOLDS,
) -> ImageQualityResult:
    evidence = ImageQualityEvidence.from_payload(payload)
    blocked_reasons: list[str] = []
    assist_reasons: list[str] = []

    if evidence.brightness_score < thresholds.brightness_min:
        blocked_reasons.append("IMAGE_TOO_DARK")
    if evidence.sharpness_score < thresholds.sharpness_min:
        blocked_reasons.append("IMAGE_TOO_BLURRY")
    if evidence.occlusion_score >= thresholds.occlusion_block_min:
        blocked_reasons.append("IMAGE_OCCLUSION_BLOCKED")
    elif evidence.occlusion_score > thresholds.occlusion_assist_min:
        assist_reasons.append("IMAGE_OCCLUSION_REVIEW_REQUIRED")

    if blocked_reasons:
        return ImageQualityResult(
            evidence=evidence,
            thresholds=thresholds,
            decision="BLOCKED",
            reason_codes=tuple(blocked_reasons),
        )
    if assist_reasons:
        return ImageQualityResult(
            evidence=evidence,
            thresholds=thresholds,
            decision="ASSIST",
            reason_codes=tuple(assist_reasons),
        )
    return ImageQualityResult(
        evidence=evidence,
        thresholds=thresholds,
        decision="PASS",
        reason_codes=(),
    )
