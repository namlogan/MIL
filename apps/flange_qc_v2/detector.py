from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from apps.flange_qc_v2.artifact_intake import REQUIRED_ARTIFACTS, validate_artifact_intake
from apps.flange_qc_v2.domain import DECISION_STATES, DetectorObservation, ValidationError
from apps.flange_qc_v2.model_artifact import ModelArtifactManifest, load_model_artifact_manifest
from apps.flange_qc_v2.sop_registry import get_reason_code


CONTRACT_VERSION = "detector.result.v1"
SHADOW_OBSERVATION_REQUEST_CONTRACT_VERSION = "shadow_detector_observation_request.v1"
AUTHORITY_BLOCKERS = ("MODEL_APPROVAL_REQUIRED", "PRODUCTION_APPROVAL_REQUIRED")
ALLOWED_SOURCE_PREFIXES = ("synthetic://", "replay://")
SHADOW_DETECTOR_NEXT_TASK = "shadow_detector_observations"
SHADOW_OBSERVATION_ALLOWED_REQUEST_FIELDS = ("contract_version", "request", "observations")
SHADOW_OBSERVATION_ALLOWED_OBSERVATION_FIELDS = ("label", "confidence", "bbox")
SHADOW_OBSERVATION_FORBIDDEN_REQUEST_FIELDS = (
    "artifact_intake_dir",
    "manifest_path",
    "model_path",
    "dataset_path",
    "weights_path",
)
SHADOW_OBSERVATION_FORBIDDEN_OBSERVATION_FIELDS = ("model_ref", "evidence_ref")


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


def build_shadow_detector_result_from_payload(
    payload: Any,
    *,
    intake_dir: str,
    repo_root: str | Path | None = None,
) -> DetectorResult:
    if not str(intake_dir).strip():
        raise ValidationError("FLANGE_QC_V2_ARTIFACT_INTAKE_DIR is not configured")
    errors = validate_shadow_detector_observation_request(payload, require_contract_version=False)
    if errors:
        raise ValidationError(str(errors[0]["message"]))

    adapter = build_manifest_detector_from_intake(
        intake_dir,
        repo_root=repo_root,
        observations=payload.get("observations", []),
    )
    return adapter.detect(DetectorRequest.from_payload(_require_field(payload, "request")))


def validate_shadow_detector_observation_request(
    payload: Any,
    *,
    require_contract_version: bool = True,
) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if not isinstance(payload, dict):
        return [{"field": "payload", "message": "shadow detector payload must be an object"}]

    _validate_shadow_contract_version(payload, require_contract_version=require_contract_version, errors=errors)
    for field_name in SHADOW_OBSERVATION_FORBIDDEN_REQUEST_FIELDS:
        if field_name in payload:
            errors.append(
                {
                    "field": field_name,
                    "message": f"shadow detector payload must not include {field_name}",
                }
            )
    for field_name in payload:
        if field_name not in SHADOW_OBSERVATION_ALLOWED_REQUEST_FIELDS:
            errors.append(
                {
                    "field": field_name,
                    "message": f"shadow detector payload field is not allowed: {field_name}",
                }
            )

    request_payload = payload.get("request")
    if not isinstance(request_payload, dict):
        errors.append({"field": "request", "message": "request is required and must be an object"})
    else:
        try:
            DetectorRequest.from_payload(request_payload)
        except ValidationError as exc:
            errors.append({"field": "request", "message": str(exc)})

    observations = payload.get("observations")
    if not isinstance(observations, list):
        errors.append({"field": "observations", "message": "observations is required and must be a list"})
        return errors

    for index, observation in enumerate(observations):
        field_prefix = f"observations[{index}]"
        if not isinstance(observation, dict):
            errors.append({"field": field_prefix, "message": "observation must be an object"})
            continue
        for field_name in observation:
            if field_name not in SHADOW_OBSERVATION_ALLOWED_OBSERVATION_FIELDS:
                errors.append(
                    {
                        "field": f"{field_prefix}.{field_name}",
                        "message": f"shadow detector observation must not include {field_name}",
                    }
                )
        errors.extend(_validate_shadow_observation_fields(observation, field_prefix))
        try:
            DetectorObservation.from_payload(observation)
        except ValidationError as exc:
            errors.append({"field": field_prefix, "message": str(exc)})
    return errors


def _validate_shadow_contract_version(
    payload: dict[str, Any],
    *,
    require_contract_version: bool,
    errors: list[dict[str, Any]],
) -> None:
    if "contract_version" not in payload:
        if require_contract_version:
            errors.append(
                {
                    "field": "contract_version",
                    "message": "contract_version is required",
                }
            )
        return
    if payload.get("contract_version") != SHADOW_OBSERVATION_REQUEST_CONTRACT_VERSION:
        errors.append(
            {
                "field": "contract_version",
                "message": "contract_version must be shadow_detector_observation_request.v1",
            }
        )


def _validate_shadow_observation_fields(observation: dict[str, Any], field_prefix: str) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    label = str(observation.get("label", "")).strip()
    if not label:
        errors.append({"field": f"{field_prefix}.label", "message": "observation label is required"})

    try:
        confidence = float(observation.get("confidence", -1))
    except (TypeError, ValueError):
        confidence = -1
    if confidence < 0 or confidence > 1:
        errors.append({"field": f"{field_prefix}.confidence", "message": "confidence values must be between 0 and 1"})

    bbox = observation.get("bbox")
    if not isinstance(bbox, list) or len(bbox) != 4:
        errors.append({"field": f"{field_prefix}.bbox", "message": "bbox must contain 4 values"})
        return errors
    for value in bbox:
        try:
            number = float(value)
        except (TypeError, ValueError):
            number = -1
        if number < 0 or number > 1:
            errors.append({"field": f"{field_prefix}.bbox", "message": "bbox values must be between 0 and 1"})
            break
    return errors
