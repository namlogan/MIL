from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from apps.flange_qc_v2.domain import DECISION_STATES, DetectorObservation, ValidationError
from apps.flange_qc_v2.sop_registry import get_reason_code


CONTRACT_VERSION = "detector.result.v1"
AUTHORITY_BLOCKERS = ("MODEL_APPROVAL_REQUIRED", "PRODUCTION_APPROVAL_REQUIRED")
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


@dataclass(frozen=True)
class DetectorRequest:
    frame_id: str
    source_uri: str
    captured_at: str
    source_ref: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "frame_id", _require_non_empty(self.frame_id, "frame_id"))
        source_uri = _require_non_empty(self.source_uri, "source_uri")
        if not source_uri.startswith(ALLOWED_SOURCE_PREFIXES):
            raise ValidationError("source_uri must use synthetic:// or replay://")
        object.__setattr__(self, "source_uri", source_uri)
        object.__setattr__(self, "captured_at", _require_non_empty(self.captured_at, "captured_at"))
        object.__setattr__(self, "source_ref", _require_non_empty(self.source_ref, "source_ref"))

    @classmethod
    def from_payload(cls, payload: Any) -> "DetectorRequest":
        if not isinstance(payload, dict):
            raise ValidationError("detector request must be an object")
        return cls(
            frame_id=_require_field(payload, "frame_id"),
            source_uri=_require_field(payload, "source_uri"),
            captured_at=_require_field(payload, "captured_at"),
            source_ref=_require_field(payload, "source_ref"),
        )

    def to_payload(self) -> dict[str, str]:
        return {
            "frame_id": self.frame_id,
            "source_uri": self.source_uri,
            "captured_at": self.captured_at,
            "source_ref": self.source_ref,
        }


@dataclass(frozen=True)
class DetectorResult:
    adapter_id: str
    request: DetectorRequest
    decision: str
    reason_codes: tuple[str, ...]
    observations: tuple[DetectorObservation, ...]
    authority_blockers: tuple[str, ...] = AUTHORITY_BLOCKERS
    production_authority: bool = False
    shadow_mode: bool = True
    contract_version: str = CONTRACT_VERSION

    def __post_init__(self) -> None:
        object.__setattr__(self, "adapter_id", _require_non_empty(self.adapter_id, "adapter_id"))
        if self.decision not in DECISION_STATES:
            raise ValidationError(f"unknown decision: {self.decision}")
        if self.decision in ("PASS", "NG"):
            raise ValidationError(f"detector result cannot emit decision: {self.decision}")
        if self.production_authority:
            raise ValidationError("detector result cannot approve production authority")
        for code in self.reason_codes + self.authority_blockers:
            get_reason_code(code)

    def to_payload(self) -> dict[str, Any]:
        return {
            "contract_version": self.contract_version,
            "adapter_id": self.adapter_id,
            "request": self.request.to_payload(),
            "decision": self.decision,
            "reason_codes": list(self.reason_codes),
            "authority_blockers": list(self.authority_blockers),
            "production_authority": self.production_authority,
            "shadow_mode": self.shadow_mode,
            "observations": [observation.to_payload() for observation in self.observations],
        }


@dataclass(frozen=True)
class StubDetectorAdapter:
    adapter_id: str = "stub-detector"
    model_ref: str = ""
    observations: tuple[dict[str, Any], ...] | list[dict[str, Any]] = field(default_factory=tuple)

    def detect(self, request: DetectorRequest) -> DetectorResult:
        observations = tuple(DetectorObservation.from_payload(observation) for observation in self.observations)
        if observations:
            return DetectorResult(
                adapter_id=self.adapter_id,
                request=request,
                decision="ASSIST",
                reason_codes=("MODEL_REVIEW_REQUIRED",),
                observations=observations,
            )
        return DetectorResult(
            adapter_id=self.adapter_id,
            request=request,
            decision="NOT_EVALUATED",
            reason_codes=("MODEL_MISSING",),
            observations=(),
        )
