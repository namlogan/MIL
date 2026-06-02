from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from apps.flange_qc_v2.domain import DECISION_STATES, ValidationError
from apps.flange_qc_v2.sop_registry import get_reason_code


CONTRACT_VERSION = "camera.boundary.v1"
AUTHORITY_BLOCKERS = (
    "CAMERA_HARDWARE_APPROVAL_REQUIRED",
    "CALIBRATION_APPROVAL_REQUIRED",
    "PRODUCTION_APPROVAL_REQUIRED",
)
DEFAULT_HARDWARE_PROFILE = {
    "camera_model": "pending_hardware_readiness",
    "lens": "pending_hardware_readiness",
    "lighting": "pending_hardware_readiness",
    "mount": "pending_hardware_readiness",
}


def _require_field(payload: dict[str, Any], field_name: str) -> Any:
    if field_name not in payload:
        raise ValidationError(f"{field_name} is required")
    return payload[field_name]


def _require_non_empty(value: Any, field_name: str) -> str:
    normalized = str(value).strip()
    if not normalized:
        raise ValidationError(f"{field_name} is required")
    return normalized


def _require_false(value: Any, field_name: str, message: str) -> bool:
    if bool(value):
        raise ValidationError(message)
    return False


@dataclass(frozen=True)
class CameraBoundaryConfig:
    adapter_id: str
    vendor: str
    enabled: bool
    live_capture_enabled: bool
    sdk_loaded: bool
    credentials_configured: bool
    source_ref: str
    hardware_profile: dict[str, Any] = field(default_factory=lambda: dict(DEFAULT_HARDWARE_PROFILE))

    def __post_init__(self) -> None:
        object.__setattr__(self, "adapter_id", _require_non_empty(self.adapter_id, "adapter_id"))
        object.__setattr__(self, "vendor", _require_non_empty(self.vendor, "vendor"))
        object.__setattr__(
            self,
            "enabled",
            _require_false(self.enabled, "enabled", "camera boundary must remain disabled until hardware readiness approval"),
        )
        object.__setattr__(
            self,
            "live_capture_enabled",
            _require_false(
                self.live_capture_enabled,
                "live_capture_enabled",
                "live capture must remain disabled until hardware readiness approval",
            ),
        )
        object.__setattr__(
            self,
            "sdk_loaded",
            _require_false(self.sdk_loaded, "sdk_loaded", "SDK loading must remain disabled until hardware readiness approval"),
        )
        object.__setattr__(
            self,
            "credentials_configured",
            _require_false(
                self.credentials_configured,
                "credentials_configured",
                "credentials must not be configured in bootstrap camera boundary",
            ),
        )
        object.__setattr__(self, "source_ref", _require_non_empty(self.source_ref, "source_ref"))
        if not isinstance(self.hardware_profile, dict):
            raise ValidationError("hardware_profile must be an object")
        normalized_profile = {
            key: _require_non_empty(value, f"hardware_profile.{key}")
            for key, value in self.hardware_profile.items()
        }
        for field_name in DEFAULT_HARDWARE_PROFILE:
            if field_name not in normalized_profile:
                raise ValidationError(f"hardware_profile.{field_name} is required")
        object.__setattr__(self, "hardware_profile", normalized_profile)

    @classmethod
    def from_payload(cls, payload: Any) -> "CameraBoundaryConfig":
        if not isinstance(payload, dict):
            raise ValidationError("camera boundary payload must be an object")
        return cls(
            adapter_id=_require_field(payload, "adapter_id"),
            vendor=_require_field(payload, "vendor"),
            enabled=_require_field(payload, "enabled"),
            live_capture_enabled=_require_field(payload, "live_capture_enabled"),
            sdk_loaded=_require_field(payload, "sdk_loaded"),
            credentials_configured=_require_field(payload, "credentials_configured"),
            source_ref=_require_field(payload, "source_ref"),
            hardware_profile=dict(_require_field(payload, "hardware_profile")),
        )

    @classmethod
    def disabled_hikrobot(cls, *, source_ref: str) -> "CameraBoundaryConfig":
        return cls(
            adapter_id="hikrobot-boundary",
            vendor="Hikrobot",
            enabled=False,
            live_capture_enabled=False,
            sdk_loaded=False,
            credentials_configured=False,
            source_ref=source_ref,
            hardware_profile=dict(DEFAULT_HARDWARE_PROFILE),
        )


@dataclass(frozen=True)
class CameraBoundaryResult:
    config: CameraBoundaryConfig
    decision: str
    reason_codes: tuple[str, ...]
    authority_blockers: tuple[str, ...] = AUTHORITY_BLOCKERS
    production_authority: bool = False
    contract_version: str = CONTRACT_VERSION

    def __post_init__(self) -> None:
        if self.decision not in DECISION_STATES:
            raise ValidationError(f"unknown decision: {self.decision}")
        if self.decision in ("PASS", "NG"):
            raise ValidationError(f"camera boundary cannot emit decision: {self.decision}")
        if self.production_authority:
            raise ValidationError("camera boundary cannot approve production authority")
        for code in self.reason_codes + self.authority_blockers:
            get_reason_code(code)

    @property
    def adapter_id(self) -> str:
        return self.config.adapter_id

    @property
    def vendor(self) -> str:
        return self.config.vendor

    @property
    def enabled(self) -> bool:
        return self.config.enabled

    @property
    def live_capture_enabled(self) -> bool:
        return self.config.live_capture_enabled

    @property
    def sdk_loaded(self) -> bool:
        return self.config.sdk_loaded

    @property
    def credentials_configured(self) -> bool:
        return self.config.credentials_configured

    def to_payload(self) -> dict[str, Any]:
        return {
            "contract_version": self.contract_version,
            "adapter_id": self.adapter_id,
            "vendor": self.vendor,
            "enabled": self.enabled,
            "live_capture_enabled": self.live_capture_enabled,
            "sdk_loaded": self.sdk_loaded,
            "credentials_configured": self.credentials_configured,
            "source_ref": self.config.source_ref,
            "hardware_profile": dict(self.config.hardware_profile),
            "decision": self.decision,
            "reason_codes": list(self.reason_codes),
            "authority_blockers": list(self.authority_blockers),
            "production_authority": self.production_authority,
        }


@dataclass(frozen=True)
class HikrobotCameraBoundary:
    config: CameraBoundaryConfig

    @classmethod
    def default_disabled(cls, *, source_ref: str) -> "HikrobotCameraBoundary":
        return cls(config=CameraBoundaryConfig.disabled_hikrobot(source_ref=source_ref))

    def describe(self) -> CameraBoundaryResult:
        return CameraBoundaryResult(
            config=self.config,
            decision="BLOCKED",
            reason_codes=("CAMERA_HARDWARE_READINESS_MISSING", "LIVE_CAMERA_DISABLED"),
        )

    def capture_frame(self) -> None:
        raise ValidationError("live camera capture is disabled until hardware readiness approval")
