from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from apps.flange_qc_v2.artifact_intake import REQUIRED_ARTIFACTS, validate_artifact_intake
from apps.flange_qc_v2.domain import DECISION_STATES, DetectorObservation, ValidationError
from apps.flange_qc_v2.model_artifact import ModelArtifactManifest, load_model_artifact_manifest
from apps.flange_qc_v2.sop_registry import get_reason_code


CONTRACT_VERSION = "detector.result.v1"
AUTHORITY_BLOCKERS = ("MODEL_APPROVAL_REQUIRED", "PRODUCTION_APPROVAL_REQUIRED")
ALLOWED_SOURCE_PREFIXES = ("synthetic://", "replay://")
SHADOW_DETECTOR_NEXT_TASK = "shadow_detector_observations"


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


@dataclass(frozen=True)
class ManifestDetectorAdapter:
    manifest: ModelArtifactManifest
    adapter_id: str = "manifest-detector"
    observations: tuple[dict[str, Any], ...] | list[dict[str, Any]] = field(default_factory=tuple)

    def detect(self, request: DetectorRequest) -> DetectorResult:
        observations = tuple(self._observation_from_payload(observation) for observation in self.observations)
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

    def _observation_from_payload(self, payload: dict[str, Any]) -> DetectorObservation:
        normalized = dict(payload)
        label = str(normalized.get("label", "")).strip()
        if label not in self.manifest.labels:
            raise ValidationError("observation label is not declared by model manifest")
        if not str(normalized.get("model_ref", "")).strip():
            normalized["model_ref"] = self.manifest.model_ref
        if not str(normalized.get("evidence_ref", "")).strip():
            normalized["evidence_ref"] = self.manifest.eval_report_ref
        return DetectorObservation.from_payload(normalized)


def build_shadow_detector_unconfigured_status(reason: str) -> dict[str, Any]:
    return {
        "configured": False,
        "ready": False,
        "adapter_id": "manifest-detector",
        "model_ref": "",
        "artifact_version": "",
        "labels": [],
        "eval_report_ref": "",
        "approval_status": "",
        "shadow_mode": True,
        "production_authority": False,
        "authority_blockers": list(AUTHORITY_BLOCKERS),
        "errors": [reason],
        "warnings": [],
        "artifact_intake_ready": {
            "shadow_model_integration_issue": False,
            "live_camera_implementation_issue": False,
        },
        "next_issue": {
            "recommended_task": "configure_artifact_intake",
            "reason": reason,
        },
    }


def build_shadow_detector_status_from_intake(
    intake_dir: str | Path,
    *,
    repo_root: str | Path | None = None,
) -> dict[str, Any]:
    intake_status = validate_artifact_intake(intake_dir, repo_root=repo_root)
    artifact_ready = intake_status.get("ready", {})
    shadow_ready = bool(artifact_ready.get("shadow_model_integration_issue"))
    base_status: dict[str, Any] = {
        "configured": True,
        "ready": False,
        "adapter_id": "manifest-detector",
        "model_ref": "",
        "artifact_version": "",
        "labels": [],
        "eval_report_ref": "",
        "approval_status": "",
        "shadow_mode": True,
        "production_authority": False,
        "authority_blockers": list(AUTHORITY_BLOCKERS),
        "errors": list(intake_status.get("errors", [])),
        "warnings": list(intake_status.get("warnings", [])),
        "artifact_intake_ready": artifact_ready,
        "next_issue": intake_status.get("next_issue", {}),
    }
    if not shadow_ready:
        return base_status

    manifest_path = Path(intake_dir).resolve() / REQUIRED_ARTIFACTS["model_artifact_manifest"]
    manifest = load_model_artifact_manifest(manifest_path)
    base_status.update(
        {
            "ready": True,
            "model_ref": manifest.model_ref,
            "artifact_version": manifest.artifact_version,
            "labels": list(manifest.labels),
            "eval_report_ref": manifest.eval_report_ref,
            "approval_status": manifest.approval_status,
            "shadow_mode": manifest.shadow_mode,
            "next_issue": {
                "recommended_task": SHADOW_DETECTOR_NEXT_TASK,
                "source_ref": manifest.source_ref,
                "reason": "shadow detector metadata bridge is ready for review-only observations",
            },
        }
    )
    return base_status


def build_manifest_detector_from_intake(
    intake_dir: str | Path,
    *,
    repo_root: str | Path | None = None,
    observations: tuple[dict[str, Any], ...] | list[dict[str, Any]] = (),
) -> ManifestDetectorAdapter:
    status = build_shadow_detector_status_from_intake(intake_dir, repo_root=repo_root)
    if not status["ready"]:
        raise ValidationError("artifact intake is not ready for shadow detector integration")
    manifest_path = Path(intake_dir).resolve() / REQUIRED_ARTIFACTS["model_artifact_manifest"]
    return ManifestDetectorAdapter(
        manifest=load_model_artifact_manifest(manifest_path),
        observations=observations,
    )
