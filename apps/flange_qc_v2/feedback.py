from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from apps.flange_qc_v2.domain import DECISION_STATES, ValidationError


SCHEMA_VERSION = 1
FEEDBACK_TYPES = (
    "CONFIRM_BLOCKED",
    "MARK_FALSE_POSITIVE",
    "MARK_FALSE_NEGATIVE",
    "REQUEST_REVIEW",
)
AUTHORITY_BLOCKERS = ("PRODUCTION_APPROVAL_REQUIRED",)


def _require_non_empty(value: Any, field_name: str) -> str:
    normalized = str(value).strip()
    if not normalized:
        raise ValidationError(f"{field_name} is required")
    return normalized


def _coerce_schema_version(value: Any) -> int:
    try:
        version = int(value)
    except (TypeError, ValueError) as exc:
        raise ValidationError(f"unsupported feedback schema_version: {value}") from exc
    if version != SCHEMA_VERSION:
        raise ValidationError(f"unsupported feedback schema_version: {value}")
    return version


@dataclass(frozen=True)
class QcFeedback:
    feedback_id: str
    inspection_id: str
    feedback_type: str
    reviewer_id: str
    note: str
    shadow_decision: str
    source_ref: str
    created_at: str
    schema_version: int = SCHEMA_VERSION
    production_authority: bool = False
    authority_blockers: tuple[str, ...] = AUTHORITY_BLOCKERS

    def __post_init__(self) -> None:
        schema_version = _coerce_schema_version(self.schema_version)
        for field_name in ("feedback_id", "inspection_id", "reviewer_id", "note", "source_ref", "created_at"):
            object.__setattr__(self, field_name, _require_non_empty(getattr(self, field_name), field_name))
        feedback_type = _require_non_empty(self.feedback_type, "feedback_type")
        if feedback_type not in FEEDBACK_TYPES:
            raise ValidationError(f"unknown feedback type: {feedback_type}")
        shadow_decision = _require_non_empty(self.shadow_decision, "shadow_decision")
        if shadow_decision not in DECISION_STATES:
            raise ValidationError(f"unknown decision: {shadow_decision}")
        if self.production_authority:
            raise ValidationError("QC feedback cannot approve production authority")
        object.__setattr__(self, "feedback_type", feedback_type)
        object.__setattr__(self, "shadow_decision", shadow_decision)
        object.__setattr__(self, "schema_version", schema_version)
        object.__setattr__(self, "production_authority", False)
        object.__setattr__(self, "authority_blockers", AUTHORITY_BLOCKERS)

    def to_payload(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "feedback_id": self.feedback_id,
            "inspection_id": self.inspection_id,
            "feedback_type": self.feedback_type,
            "reviewer_id": self.reviewer_id,
            "note": self.note,
            "shadow_decision": self.shadow_decision,
            "source_ref": self.source_ref,
            "created_at": self.created_at,
            "production_authority": self.production_authority,
            "authority_blockers": list(self.authority_blockers),
        }

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "QcFeedback":
        if not isinstance(payload, dict):
            raise ValidationError("feedback payload must be an object")
        return cls(
            schema_version=payload.get("schema_version", SCHEMA_VERSION),
            feedback_id=payload.get("feedback_id", ""),
            inspection_id=payload.get("inspection_id", ""),
            feedback_type=payload.get("feedback_type", ""),
            reviewer_id=payload.get("reviewer_id", ""),
            note=payload.get("note", ""),
            shadow_decision=payload.get("shadow_decision", ""),
            source_ref=payload.get("source_ref", ""),
            created_at=payload.get("created_at", ""),
            production_authority=bool(payload.get("production_authority", False)),
        )
