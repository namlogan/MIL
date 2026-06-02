from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from apps.flange_qc_v2.camera import (
    CONTRACT_VERSION as CAMERA_CONTRACT_VERSION,
    CameraBoundaryConfig,
    CameraBoundaryResult,
)
from apps.flange_qc_v2.domain import ValidationError
from apps.flange_qc_v2.mlops_handoff import (
    DatasetHandoffManifest,
    EvaluationHandoffReport,
    validate_evaluation_against_dataset,
)
from apps.flange_qc_v2.model_artifact import ModelArtifactManifest


REQUIRED_ARTIFACTS = {
    "dataset_manifest": "dataset_manifest.json",
    "evaluation_report": "evaluation_report.json",
    "model_artifact_manifest": "model_artifact_manifest.json",
    "camera_boundary": "camera_boundary.json",
}

FORBIDDEN_FILE_SUFFIXES = (
    ".bmp",
    ".ckpt",
    ".engine",
    ".jpeg",
    ".jpg",
    ".key",
    ".mov",
    ".mp4",
    ".onnx",
    ".pem",
    ".png",
    ".pt",
    ".pth",
    ".safetensors",
    ".tif",
    ".tiff",
    ".trt",
    ".webp",
    ".weights",
)
FORBIDDEN_FILE_NAMES = (".env", ".env.local", "credentials.json", "secrets.json")


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _artifact_status(path: Path, contract_version: str, summary: dict[str, Any] | None = None) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "path": str(path),
        "contract_version": contract_version,
        "status": "valid",
    }
    if summary:
        payload["summary"] = summary
    return payload


def _scan_for_forbidden_files(root: Path) -> list[str]:
    errors: list[str] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        name = path.name.lower()
        suffix = path.suffix.lower()
        if name in FORBIDDEN_FILE_NAMES or suffix in FORBIDDEN_FILE_SUFFIXES:
            errors.append(f"{path.relative_to(root)} is not allowed in artifact intake bundle")
    return errors


def _validate_camera_boundary(path: Path) -> dict[str, Any]:
    payload = _load_json(path)
    if not isinstance(payload, dict):
        raise ValidationError("camera boundary artifact must be an object")
    if payload.get("contract_version") != CAMERA_CONTRACT_VERSION:
        raise ValidationError("unknown camera boundary contract_version")
    config = CameraBoundaryConfig.from_payload(payload)
    result = CameraBoundaryResult(
        config=config,
        decision=payload.get("decision", ""),
        reason_codes=tuple(payload.get("reason_codes", ())),
        authority_blockers=tuple(payload.get("authority_blockers", ())),
        production_authority=payload.get("production_authority", False),
    )
    return _artifact_status(
        path,
        result.contract_version,
        {
            "vendor": result.vendor,
            "enabled": result.enabled,
            "live_capture_enabled": result.live_capture_enabled,
            "decision": result.decision,
        },
    )


def validate_artifact_intake(intake_dir: str | Path, *, repo_root: str | Path | None = None) -> dict[str, Any]:
    intake_root = Path(intake_dir).resolve()
    repo = Path(repo_root).resolve() if repo_root else Path.cwd().resolve()
    errors: list[str] = []
    warnings: list[str] = []
    artifacts: dict[str, dict[str, Any]] = {}
    parsed: dict[str, Any] = {}

    if not intake_root.is_dir():
        return {
            "ok": False,
            "intake_dir": str(intake_root),
            "repo_root": str(repo),
            "errors": [f"{intake_root} is not a directory"],
            "warnings": [],
            "artifacts": {},
            "ready": {
                "shadow_model_integration_issue": False,
                "live_camera_implementation_issue": False,
            },
            "next_issue": {
                "recommended_task": "fix_artifact_intake",
                "reason": "intake directory is missing",
            },
        }

    errors.extend(_scan_for_forbidden_files(intake_root))

    paths = {name: intake_root / filename for name, filename in REQUIRED_ARTIFACTS.items()}
    for artifact_name, path in paths.items():
        if not path.is_file():
            errors.append(f"{path.name} is required")
            continue
        try:
            if artifact_name == "dataset_manifest":
                dataset = DatasetHandoffManifest.from_payload(_load_json(path))
                parsed[artifact_name] = dataset
                artifacts[artifact_name] = _artifact_status(
                    path,
                    dataset.contract_version,
                    {
                        "dataset_snapshot_ref": dataset.dataset_snapshot_ref,
                        "labels": list(dataset.labels),
                    },
                )
            elif artifact_name == "evaluation_report":
                report = EvaluationHandoffReport.from_payload(_load_json(path))
                parsed[artifact_name] = report
                artifacts[artifact_name] = _artifact_status(
                    path,
                    report.contract_version,
                    {
                        "model_ref": report.model_ref,
                        "dataset_snapshot_ref": report.dataset_snapshot_ref,
                    },
                )
            elif artifact_name == "model_artifact_manifest":
                manifest = ModelArtifactManifest.from_payload(_load_json(path))
                parsed[artifact_name] = manifest
                artifacts[artifact_name] = _artifact_status(
                    path,
                    manifest.contract_version,
                    {
                        "model_ref": manifest.model_ref,
                        "labels": list(manifest.labels),
                    },
                )
            elif artifact_name == "camera_boundary":
                artifacts[artifact_name] = _validate_camera_boundary(path)
        except (json.JSONDecodeError, OSError, ValidationError, ValueError) as exc:
            errors.append(f"{path.name}: {exc}")

    dataset = parsed.get("dataset_manifest")
    report = parsed.get("evaluation_report")
    model = parsed.get("model_artifact_manifest")
    if dataset and report:
        try:
            validate_evaluation_against_dataset(report, dataset)
        except ValidationError as exc:
            errors.append(str(exc))
    if report and model and model.model_ref != report.model_ref:
        errors.append("model artifact model_ref does not match evaluation report")
    if dataset and model:
        dataset_labels = set(dataset.labels)
        model_labels = set(model.labels)
        if not model_labels.issubset(dataset_labels):
            errors.append("model artifact labels are not declared by dataset manifest")

    camera_artifact = artifacts.get("camera_boundary", {})
    camera_summary = camera_artifact.get("summary", {})
    live_camera_ready = bool(
        camera_summary.get("enabled") is True and camera_summary.get("live_capture_enabled") is True
    )
    if camera_artifact and not live_camera_ready:
        warnings.append("camera boundary remains disabled; open hardware readiness before live capture")

    ok = not errors
    shadow_ready = ok and all(name in artifacts for name in REQUIRED_ARTIFACTS)
    recommended_task = "shadow_model_integration" if shadow_ready else "fix_artifact_intake"
    return {
        "ok": ok,
        "intake_dir": str(intake_root),
        "repo_root": str(repo),
        "errors": errors,
        "warnings": warnings,
        "artifacts": artifacts,
        "ready": {
            "shadow_model_integration_issue": shadow_ready,
            "live_camera_implementation_issue": ok and live_camera_ready,
        },
        "next_issue": {
            "recommended_task": recommended_task,
            "source_ref": "https://github.com/namlogan/MIL/issues/103",
        },
    }
