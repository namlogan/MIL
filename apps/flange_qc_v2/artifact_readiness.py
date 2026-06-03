from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from apps.flange_qc_v2.feedback import LABELING_REVIEW_PACK_CONTRACT_VERSION


ARTIFACT_READINESS_REPORT_CONTRACT_VERSION = "artifact_readiness_report.v1"
PRODUCTION_AUTHORITY_BLOCKERS = (
    "PRODUCT_SPEC_APPROVAL_REQUIRED",
    "QC_SOP_TOLERANCE_APPROVAL_REQUIRED",
    "MODEL_PROMOTION_APPROVAL_REQUIRED",
    "CAMERA_HARDWARE_APPROVAL_REQUIRED",
    "PRODUCTION_RELEASE_APPROVAL_REQUIRED",
    "PRODUCTION_APPROVAL_REQUIRED",
)
LIVE_CAMERA_AUTHORITY_BLOCKERS = (
    "CAMERA_HARDWARE_APPROVAL_REQUIRED",
    "CALIBRATION_APPROVAL_REQUIRED",
    "PRODUCTION_APPROVAL_REQUIRED",
)


def build_artifact_readiness_report(
    artifact_intake_result: dict[str, Any],
    *,
    labeling_review_pack: dict[str, Any] | None = None,
    generated_at: str | None = None,
    source_ref: str = "",
) -> dict[str, Any]:
    """Build a metadata-only readiness report from existing validation results."""
    if not isinstance(artifact_intake_result, dict):
        raise ValueError("artifact intake result must be an object")
    if labeling_review_pack is not None:
        _validate_labeling_review_pack(labeling_review_pack)

    timestamp = generated_at or datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    artifact_lane = _artifact_intake_lane(artifact_intake_result)
    shadow_lane = _shadow_model_lane(artifact_intake_result)
    live_camera_lane = _live_camera_lane(artifact_intake_result)
    qc_feedback_lane = _qc_feedback_lane(labeling_review_pack)
    production_lane = {
        "ready": False,
        "state": "blocked",
        "authority_blockers": list(PRODUCTION_AUTHORITY_BLOCKERS),
        "reason": "production release and PASS/NG authority require explicit human approval gates",
    }

    recommended_next_actions = _recommended_next_actions(
        artifact_lane=artifact_lane,
        shadow_lane=shadow_lane,
        live_camera_lane=live_camera_lane,
        qc_feedback_lane=qc_feedback_lane,
    )

    return {
        "contract_version": ARTIFACT_READINESS_REPORT_CONTRACT_VERSION,
        "generated_at": timestamp,
        "source_ref": source_ref,
        "lanes": {
            "artifact_intake": artifact_lane,
            "shadow_model": shadow_lane,
            "live_camera": live_camera_lane,
            "qc_feedback": qc_feedback_lane,
            "production_release": production_lane,
        },
        "recommended_next_actions": recommended_next_actions,
        "production_authority": False,
        "authority_blockers": list(PRODUCTION_AUTHORITY_BLOCKERS),
    }


def _artifact_intake_lane(result: dict[str, Any]) -> dict[str, Any]:
    errors = _strings(result.get("errors", []))
    warnings = _strings(result.get("warnings", []))
    next_issue = result.get("next_issue") if isinstance(result.get("next_issue"), dict) else {}
    artifacts = result.get("artifacts") if isinstance(result.get("artifacts"), dict) else {}
    return {
        "ok": bool(result.get("ok")) and not errors,
        "state": "valid" if bool(result.get("ok")) and not errors else "blocked",
        "intake_dir": str(result.get("intake_dir", "")),
        "artifact_count": len(artifacts),
        "artifacts": sorted(str(name) for name in artifacts),
        "errors": errors,
        "warnings": warnings,
        "recommended_task": str(next_issue.get("recommended_task", "fix_artifact_intake")),
        "source_ref": str(next_issue.get("source_ref", "")),
    }


def _shadow_model_lane(result: dict[str, Any]) -> dict[str, Any]:
    ready = _ready_flag(result, "shadow_model_integration_issue")
    errors = _strings(result.get("errors", []))
    recommended_task = "shadow_observation_review" if ready else "fix_artifact_intake"
    blockers = [] if ready else (errors or ["artifact_intake_not_ready"])
    return {
        "ready": ready,
        "state": "ready_for_shadow_observation_review" if ready else "blocked",
        "recommended_task": recommended_task,
        "blockers": blockers,
        "authority_blockers": ["MODEL_PROMOTION_APPROVAL_REQUIRED", "PRODUCTION_APPROVAL_REQUIRED"],
        "production_authority": False,
    }


def _live_camera_lane(result: dict[str, Any]) -> dict[str, Any]:
    ready = _ready_flag(result, "live_camera_implementation_issue")
    return {
        "ready": ready,
        "state": "ready_for_hardware_implementation_issue" if ready else "blocked",
        "recommended_task": "live_camera_implementation" if ready else "schedule_camera_hardware_readiness",
        "authority_blockers": [] if ready else list(LIVE_CAMERA_AUTHORITY_BLOCKERS),
        "production_authority": False,
    }


def _qc_feedback_lane(pack: dict[str, Any] | None) -> dict[str, Any]:
    if pack is None:
        return {
            "configured": False,
            "ready_for_labeling_review": False,
            "source_record_count": 0,
            "recommended_task": "collect_qc_feedback",
            "recommended_next_actions": ["collect_more_qc_feedback"],
            "authority_blockers": ["PRODUCTION_APPROVAL_REQUIRED"],
            "production_authority": False,
        }

    source_record_count = int(pack.get("source_record_count", 0))
    recommended_actions = _strings(pack.get("recommended_next_actions", [])) or ["collect_more_qc_feedback"]
    return {
        "configured": True,
        "ready_for_labeling_review": source_record_count > 0,
        "source_record_count": source_record_count,
        "product_counts": dict(pack.get("product_counts", {})),
        "feedback_type_counts": dict(pack.get("feedback_type_counts", {})),
        "detector_label_counts": dict(pack.get("detector_label_counts", {})),
        "recommended_task": "labeling_review" if source_record_count > 0 else "collect_qc_feedback",
        "recommended_next_actions": recommended_actions,
        "authority_blockers": _strings(pack.get("authority_blockers", [])) or ["PRODUCTION_APPROVAL_REQUIRED"],
        "production_authority": False,
    }


def _recommended_next_actions(
    *,
    artifact_lane: dict[str, Any],
    shadow_lane: dict[str, Any],
    live_camera_lane: dict[str, Any],
    qc_feedback_lane: dict[str, Any],
) -> list[str]:
    actions: list[str] = []
    if not artifact_lane["ok"]:
        actions.append(str(artifact_lane.get("recommended_task") or "fix_artifact_intake"))
    if shadow_lane["ready"]:
        actions.append("submit_shadow_observation_payload")
    if not live_camera_lane["ready"]:
        actions.append("schedule_camera_hardware_readiness")
    if qc_feedback_lane["ready_for_labeling_review"]:
        actions.append("start_labeling_review")
    else:
        actions.append("collect_more_qc_feedback")
    actions.append("keep_production_release_blocked")
    return _unique(actions)


def _validate_labeling_review_pack(pack: dict[str, Any]) -> None:
    if not isinstance(pack, dict):
        raise ValueError("labeling review pack must be an object")
    if pack.get("contract_version") != LABELING_REVIEW_PACK_CONTRACT_VERSION:
        raise ValueError("labeling review pack contract_version is invalid")
    if pack.get("production_authority") is not False:
        raise ValueError("labeling review pack cannot approve production authority")
    source_record_count = pack.get("source_record_count")
    if not isinstance(source_record_count, int) or source_record_count < 0:
        raise ValueError("labeling review pack source_record_count must be a non-negative integer")
    for forbidden in ("records", "payload", "payload_json", "raw_media", "raw_dataset", "model_weights"):
        if forbidden in pack:
            raise ValueError(f"labeling review pack must not include {forbidden}")


def _ready_flag(result: dict[str, Any], name: str) -> bool:
    ready = result.get("ready") if isinstance(result.get("ready"), dict) else {}
    return bool(ready.get(name))


def _strings(values: Any) -> list[str]:
    if not isinstance(values, list):
        return []
    return [str(value) for value in values]


def _unique(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result
