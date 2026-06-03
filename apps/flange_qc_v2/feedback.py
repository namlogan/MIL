from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from apps.flange_qc_v2.domain import DECISION_STATES, ValidationError


SCHEMA_VERSION = 1
FEEDBACK_EXPORT_CONTRACT_VERSION = "qc_feedback_export.v1"
LABELING_REVIEW_PACK_CONTRACT_VERSION = "qc_feedback_labeling_review_pack.v1"
FEEDBACK_TYPES = (
    "CONFIRM_BLOCKED",
    "MARK_FALSE_POSITIVE",
    "MARK_FALSE_NEGATIVE",
    "REQUEST_REVIEW",
)
AUTHORITY_BLOCKERS = ("PRODUCTION_APPROVAL_REQUIRED",)
FEEDBACK_EXPORT_REQUIRED_FIELDS = (
    "contract_version",
    "audit_feedback_id",
    "feedback_id",
    "inspection_id",
    "product",
    "inspection_decision",
    "inspection_created_at",
    "feedback_type",
    "reviewer_id",
    "note",
    "shadow_decision",
    "source_ref",
    "feedback_created_at",
    "production_authority",
    "authority_blockers",
    "observations",
)
FEEDBACK_EXPORT_ALLOWED_FIELDS = set(FEEDBACK_EXPORT_REQUIRED_FIELDS)
FEEDBACK_EXPORT_OBSERVATION_ALLOWED_FIELDS = {
    "label",
    "confidence",
    "bbox",
    "model_ref",
    "evidence_ref",
}
RAW_MEDIA_REF_PREFIXES = ("file://", "/", "~")
RAW_MEDIA_REF_SUFFIXES = (".bmp", ".jpeg", ".jpg", ".mov", ".mp4", ".png", ".tif", ".tiff", ".webp")


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


def validate_feedback_export_records(records: list[Any]) -> dict[str, Any]:
    errors = []
    for index, record in enumerate(records, start=1):
        errors.extend(validate_feedback_export_record(record, line=index))
    return {
        "ok": not errors,
        "record_count": len(records),
        "errors": errors,
    }


def build_labeling_review_pack(records: list[dict[str, Any]]) -> dict[str, Any]:
    validation = validate_feedback_export_records(records)
    if not validation["ok"]:
        raise ValueError(f"feedback export validation failed: {validation['errors']}")

    product_counts: dict[str, int] = {}
    feedback_type_counts: dict[str, int] = {}
    inspection_decision_counts: dict[str, int] = {}
    shadow_decision_counts: dict[str, int] = {}
    detector_label_counts: dict[str, int] = {}

    for record in records:
        _increment(product_counts, record["product"]["code"])
        _increment(feedback_type_counts, record["feedback_type"])
        _increment(inspection_decision_counts, record["inspection_decision"])
        _increment(shadow_decision_counts, record["shadow_decision"])
        for observation in record["observations"]:
            _increment(detector_label_counts, observation["label"])

    return {
        "contract_version": LABELING_REVIEW_PACK_CONTRACT_VERSION,
        "source_contract_version": FEEDBACK_EXPORT_CONTRACT_VERSION,
        "source_record_count": len(records),
        "product_counts": _sorted_counts(product_counts),
        "feedback_type_counts": _sorted_counts(feedback_type_counts),
        "inspection_decision_counts": _sorted_counts(inspection_decision_counts),
        "shadow_decision_counts": _sorted_counts(shadow_decision_counts),
        "detector_label_counts": _sorted_counts(detector_label_counts),
        "recommended_next_actions": _labeling_review_next_actions(records, feedback_type_counts),
        "production_authority": False,
        "authority_blockers": list(AUTHORITY_BLOCKERS),
    }


def validate_feedback_export_record(record: Any, *, line: int | None = None) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if not isinstance(record, dict):
        return [_feedback_export_error("record", "record must be an object", line=line)]

    for field_name in FEEDBACK_EXPORT_REQUIRED_FIELDS:
        if field_name not in record:
            errors.append(_feedback_export_error(field_name, f"{field_name} is required", line=line))
    for field_name in sorted(set(record) - FEEDBACK_EXPORT_ALLOWED_FIELDS):
        errors.append(_feedback_export_error(field_name, f"{field_name} is not allowed", line=line))

    if record.get("contract_version") != FEEDBACK_EXPORT_CONTRACT_VERSION:
        errors.append(_feedback_export_error("contract_version", "unknown feedback export contract_version", line=line))
    if not isinstance(record.get("audit_feedback_id"), int) or record.get("audit_feedback_id", 0) <= 0:
        errors.append(_feedback_export_error("audit_feedback_id", "audit_feedback_id must be a positive integer", line=line))
    for field_name in (
        "feedback_id",
        "inspection_id",
        "inspection_created_at",
        "reviewer_id",
        "note",
        "source_ref",
        "feedback_created_at",
    ):
        if not _is_non_empty_string(record.get(field_name)):
            errors.append(_feedback_export_error(field_name, f"{field_name} is required", line=line))
    if record.get("inspection_decision") not in DECISION_STATES:
        errors.append(_feedback_export_error("inspection_decision", "unknown inspection_decision", line=line))
    if record.get("shadow_decision") not in DECISION_STATES:
        errors.append(_feedback_export_error("shadow_decision", "unknown shadow_decision", line=line))
    if record.get("feedback_type") not in FEEDBACK_TYPES:
        errors.append(_feedback_export_error("feedback_type", "unknown feedback_type", line=line))
    if record.get("production_authority") is not False:
        errors.append(_feedback_export_error("production_authority", "production_authority must be false", line=line))
    if record.get("authority_blockers") != list(AUTHORITY_BLOCKERS):
        errors.append(_feedback_export_error("authority_blockers", "authority_blockers must require production approval", line=line))

    errors.extend(_validate_feedback_export_product(record.get("product"), line=line))
    errors.extend(_validate_feedback_export_observations(record.get("observations"), line=line))
    for field_name in ("source_ref",):
        if _looks_like_raw_media_ref(record.get(field_name, "")):
            errors.append(_feedback_export_error(field_name, f"{field_name} must not reference raw media", line=line))
    return errors


def _increment(counts: dict[str, int], key: Any) -> None:
    normalized = str(key).strip()
    if not normalized:
        return
    counts[normalized] = counts.get(normalized, 0) + 1


def _sorted_counts(counts: dict[str, int]) -> dict[str, int]:
    return {key: counts[key] for key in sorted(counts)}


def _labeling_review_next_actions(records: list[dict[str, Any]], feedback_type_counts: dict[str, int]) -> list[str]:
    if not records:
        return ["collect_more_qc_feedback"]

    actions = ["review_labeling_policy_with_qc_owner"]
    if feedback_type_counts.get("MARK_FALSE_POSITIVE", 0):
        actions.append("review_false_positive_alerts")
    if feedback_type_counts.get("MARK_FALSE_NEGATIVE", 0):
        actions.append("review_false_negative_misses")
    if feedback_type_counts.get("CONFIRM_BLOCKED", 0):
        actions.append("prioritize_confirmed_alert_examples")
    if feedback_type_counts.get("REQUEST_REVIEW", 0):
        actions.append("triage_requested_reviews")
    actions.append("prepare_mlop_dataset_manifest_after_data_owner_review")
    return actions


def _validate_feedback_export_product(product: Any, *, line: int | None) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if not isinstance(product, dict):
        return [_feedback_export_error("product", "product must be an object", line=line)]
    allowed_fields = {"code", "spec_version"}
    for field_name in sorted(set(product) - allowed_fields):
        errors.append(_feedback_export_error(f"product.{field_name}", f"product.{field_name} is not allowed", line=line))
    for field_name in ("code", "spec_version"):
        if not _is_non_empty_string(product.get(field_name)):
            errors.append(_feedback_export_error(f"product.{field_name}", f"product.{field_name} is required", line=line))
    return errors


def _validate_feedback_export_observations(observations: Any, *, line: int | None) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if not isinstance(observations, list):
        return [_feedback_export_error("observations", "observations must be a list", line=line)]
    for index, observation in enumerate(observations):
        prefix = f"observations[{index}]"
        if not isinstance(observation, dict):
            errors.append(_feedback_export_error(prefix, "observation must be an object", line=line))
            continue
        for field_name in sorted(set(observation) - FEEDBACK_EXPORT_OBSERVATION_ALLOWED_FIELDS):
            errors.append(_feedback_export_error(f"{prefix}.{field_name}", f"{prefix}.{field_name} is not allowed", line=line))
        if not _is_non_empty_string(observation.get("label")):
            errors.append(_feedback_export_error(f"{prefix}.label", "observation label is required", line=line))
        confidence = observation.get("confidence")
        if not _is_unit_interval_number(confidence):
            errors.append(_feedback_export_error(f"{prefix}.confidence", "confidence must be between 0 and 1", line=line))
        bbox = observation.get("bbox")
        if not isinstance(bbox, list) or len(bbox) != 4 or not all(_is_unit_interval_number(value) for value in bbox):
            errors.append(_feedback_export_error(f"{prefix}.bbox", "bbox must contain 4 values between 0 and 1", line=line))
        for field_name in ("model_ref", "evidence_ref"):
            value = observation.get(field_name)
            if value is not None:
                if not _is_non_empty_string(value):
                    errors.append(_feedback_export_error(f"{prefix}.{field_name}", f"{field_name} must be non-empty", line=line))
                elif _looks_like_raw_media_ref(value):
                    errors.append(
                        _feedback_export_error(
                            f"{prefix}.{field_name}",
                            f"{field_name} must not reference raw media",
                            line=line,
                        )
                    )
    return errors


def _feedback_export_error(field: str, message: str, *, line: int | None) -> dict[str, Any]:
    error = {
        "field": field,
        "message": message,
    }
    if line is not None:
        error["line"] = line
    return error


def _is_non_empty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _is_unit_interval_number(value: Any) -> bool:
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        return False
    return 0 <= float(value) <= 1


def _looks_like_raw_media_ref(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    normalized = value.strip().lower()
    return normalized.startswith(RAW_MEDIA_REF_PREFIXES) or normalized.endswith(RAW_MEDIA_REF_SUFFIXES)
