from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from apps.flange_qc_v2.domain import ValidationError


CONTRACT_VERSION = "model.artifact.v1"
MODEL_FAMILIES = ("detector",)
TASKS = ("flange_qc_v2.detector",)
APPROVAL_STATUSES = ("candidate", "shadow_reviewed", "rejected")
RAW_ARTIFACT_SUFFIXES = (
    ".bin",
    ".ckpt",
    ".engine",
    ".onnx",
    ".pt",
    ".pth",
    ".safetensors",
    ".trt",
    ".weights",
)
APPROVED_MODEL_REF_PREFIXES = ("registry://", "mlflow://", "model://")
_SHA256_PATTERN = re.compile(r"^sha256:[0-9a-f]{64}$")


def _require_field(payload: dict[str, Any], field_name: str) -> Any:
    if field_name not in payload:
        raise ValidationError(f"{field_name} is required")
    return payload[field_name]


def _require_non_empty(value: Any, field_name: str) -> str:
    normalized = str(value).strip()
    if not normalized:
        raise ValidationError(f"{field_name} is required")
    return normalized


def _require_bool(value: Any, field_name: str) -> bool:
    if not isinstance(value, bool):
        raise ValidationError(f"{field_name} must be a boolean")
    return value


def _require_safe_repo_path(value: Any, field_name: str) -> str:
    normalized = _require_non_empty(value, field_name)
    path = Path(normalized)
    if (
        path.is_absolute()
        or normalized.startswith("~")
        or "://" in normalized
        or "\\" in normalized
        or any(part == ".." for part in path.parts)
    ):
        raise ValidationError(f"{field_name} must be a safe repository-relative path")
    return normalized


def _require_model_ref(value: Any) -> str:
    normalized = _require_non_empty(value, "model_ref")
    if not normalized.startswith(APPROVED_MODEL_REF_PREFIXES):
        raise ValidationError("model_ref must use an approved model registry reference")
    if normalized.lower().endswith(RAW_ARTIFACT_SUFFIXES):
        raise ValidationError("model_ref must not point directly to raw model weights")
    return normalized


def _require_labels(value: Any) -> tuple[str, ...]:
    if not isinstance(value, list):
        raise ValidationError("labels must be a list")
    labels = tuple(_require_non_empty(label, "label") for label in value)
    if not labels:
        raise ValidationError("labels must not be empty")
    if len(set(labels)) != len(labels):
        raise ValidationError("labels must be unique")
    return labels


@dataclass(frozen=True)
class ModelArtifactManifest:
    contract_version: str
    model_ref: str
    artifact_version: str
    model_family: str
    task: str
    labels: tuple[str, ...]
    output_schema: str
    eval_report_ref: str
    artifact_digest: str
    approval_status: str
    production_authority: bool
    shadow_mode: bool
    source_ref: str

    def __post_init__(self) -> None:
        if self.contract_version != CONTRACT_VERSION:
            raise ValidationError(f"unknown model artifact contract_version: {self.contract_version}")
        object.__setattr__(self, "model_ref", _require_model_ref(self.model_ref))
        object.__setattr__(self, "artifact_version", _require_non_empty(self.artifact_version, "artifact_version"))
        if self.model_family not in MODEL_FAMILIES:
            raise ValidationError(f"unknown model_family: {self.model_family}")
        if self.task not in TASKS:
            raise ValidationError(f"unknown model artifact task: {self.task}")
        object.__setattr__(self, "labels", _require_labels(self.labels))
        object.__setattr__(self, "output_schema", _require_safe_repo_path(self.output_schema, "output_schema"))
        object.__setattr__(self, "eval_report_ref", _require_safe_repo_path(self.eval_report_ref, "eval_report_ref"))
        artifact_digest = _require_non_empty(self.artifact_digest, "artifact_digest")
        if not _SHA256_PATTERN.match(artifact_digest):
            raise ValidationError("artifact_digest must be a sha256 digest")
        object.__setattr__(self, "artifact_digest", artifact_digest)
        if self.approval_status not in APPROVAL_STATUSES:
            raise ValidationError(f"unknown approval_status: {self.approval_status}")
        production_authority = _require_bool(self.production_authority, "production_authority")
        if production_authority:
            raise ValidationError("model artifact cannot approve production authority")
        object.__setattr__(self, "production_authority", production_authority)
        shadow_mode = _require_bool(self.shadow_mode, "shadow_mode")
        if not shadow_mode:
            raise ValidationError("model artifact must remain in shadow_mode")
        object.__setattr__(self, "shadow_mode", shadow_mode)
        object.__setattr__(self, "source_ref", _require_non_empty(self.source_ref, "source_ref"))

    @classmethod
    def from_payload(cls, payload: Any) -> "ModelArtifactManifest":
        if not isinstance(payload, dict):
            raise ValidationError("model artifact manifest must be an object")
        return cls(
            contract_version=_require_field(payload, "contract_version"),
            model_ref=_require_field(payload, "model_ref"),
            artifact_version=_require_field(payload, "artifact_version"),
            model_family=_require_field(payload, "model_family"),
            task=_require_field(payload, "task"),
            labels=_require_field(payload, "labels"),
            output_schema=_require_field(payload, "output_schema"),
            eval_report_ref=_require_field(payload, "eval_report_ref"),
            artifact_digest=_require_field(payload, "artifact_digest"),
            approval_status=_require_field(payload, "approval_status"),
            production_authority=_require_field(payload, "production_authority"),
            shadow_mode=_require_field(payload, "shadow_mode"),
            source_ref=_require_field(payload, "source_ref"),
        )

    def to_payload(self) -> dict[str, Any]:
        return {
            "contract_version": self.contract_version,
            "model_ref": self.model_ref,
            "artifact_version": self.artifact_version,
            "model_family": self.model_family,
            "task": self.task,
            "labels": list(self.labels),
            "output_schema": self.output_schema,
            "eval_report_ref": self.eval_report_ref,
            "artifact_digest": self.artifact_digest,
            "approval_status": self.approval_status,
            "production_authority": self.production_authority,
            "shadow_mode": self.shadow_mode,
            "source_ref": self.source_ref,
        }


def load_model_artifact_manifest(path: str | Path) -> ModelArtifactManifest:
    manifest_path = Path(path)
    if manifest_path.suffix != ".json":
        raise ValidationError("manifest path must point to a JSON file")
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    return ModelArtifactManifest.from_payload(payload)
