from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from apps.flange_qc_v2.domain import ValidationError


DATASET_CONTRACT_VERSION = "mlops.dataset_manifest.v1"
EVALUATION_CONTRACT_VERSION = "mlops.evaluation_report.v1"
APPROVED_DATASET_REF_PREFIXES = ("dataset://", "s3://", "gs://", "az://", "registry://")
APPROVED_MODEL_REF_PREFIXES = ("registry://", "mlflow://", "model://")
RAW_MEDIA_SUFFIXES = (".bmp", ".jpeg", ".jpg", ".mov", ".mp4", ".png", ".tif", ".tiff", ".webp")
RAW_MODEL_SUFFIXES = (".bin", ".ckpt", ".engine", ".onnx", ".pt", ".pth", ".safetensors", ".trt")
APPROVAL_STATUSES = ("candidate", "shadow_reviewed", "rejected")
REQUIRED_SPLIT_KEYS = ("train", "validation", "test")
REQUIRED_METRICS = ("precision", "recall", "f1")


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


def _require_unit_interval(value: Any, field_name: str) -> float:
    number = float(value)
    if number < 0 or number > 1:
        raise ValidationError(f"{field_name} must be between 0 and 1")
    return number


def _reject_raw_or_unsafe_ref(value: str, field_name: str, raw_suffixes: tuple[str, ...]) -> None:
    lowered = value.lower()
    if (
        value.startswith("file://")
        or value.startswith("/")
        or value.startswith("~")
        or "/../" in value
        or value.endswith("/..")
        or lowered.endswith(raw_suffixes)
    ):
        raise ValidationError(f"{field_name} must use an approved dataset storage reference")


def _require_dataset_ref(value: Any, field_name: str) -> str:
    normalized = _require_non_empty(value, field_name)
    _reject_raw_or_unsafe_ref(normalized, field_name, RAW_MEDIA_SUFFIXES)
    if not normalized.startswith(APPROVED_DATASET_REF_PREFIXES):
        raise ValidationError(f"{field_name} must use an approved dataset storage reference")
    return normalized


def _require_dataset_snapshot_ref(value: Any) -> str:
    normalized = _require_dataset_ref(value, "dataset_snapshot_ref")
    if not normalized.startswith("dataset://"):
        raise ValidationError("dataset_snapshot_ref must use dataset://")
    return normalized


def _require_model_ref(value: Any) -> str:
    normalized = _require_non_empty(value, "model_ref")
    if not normalized.startswith(APPROVED_MODEL_REF_PREFIXES) or normalized.lower().endswith(RAW_MODEL_SUFFIXES):
        raise ValidationError("model_ref must use an approved model registry reference")
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


def _require_split_policy(value: Any) -> dict[str, str]:
    if not isinstance(value, dict):
        raise ValidationError("split_policy must be an object")
    policy = {
        "method": _require_non_empty(value.get("method", ""), "split_policy.method"),
        "leakage_guard": _require_non_empty(value.get("leakage_guard", ""), "split_policy.leakage_guard"),
        "label_timestamp_field": _require_non_empty(
            value.get("label_timestamp_field", ""),
            "split_policy.label_timestamp_field",
        ),
        "feature_timestamp_field": _require_non_empty(
            value.get("feature_timestamp_field", ""),
            "split_policy.feature_timestamp_field",
        ),
    }
    if policy["leakage_guard"] != "point_in_time":
        raise ValidationError("split_policy.leakage_guard must be point_in_time")
    return policy


def _require_split_counts(value: Any) -> dict[str, int]:
    if not isinstance(value, dict) or any(key not in value for key in REQUIRED_SPLIT_KEYS):
        raise ValidationError("split_counts requires train, validation, and test")
    counts = {key: int(value[key]) for key in REQUIRED_SPLIT_KEYS}
    if any(count <= 0 for count in counts.values()):
        raise ValidationError("split_counts values must be positive")
    return counts


def _require_metrics(value: Any) -> dict[str, float]:
    if not isinstance(value, dict):
        raise ValidationError("metrics must be an object")
    metrics = {name: _require_unit_interval(metric, f"metrics.{name}") for name, metric in value.items()}
    missing = [metric for metric in REQUIRED_METRICS if metric not in metrics]
    if missing:
        raise ValidationError("metrics requires precision, recall, and f1")
    return metrics


def _require_slice_metrics(value: Any) -> tuple[dict[str, Any], ...]:
    if not isinstance(value, list) or not value:
        raise ValidationError("slice_metrics must be a non-empty list")
    slices = []
    for index, item in enumerate(value):
        if not isinstance(item, dict):
            raise ValidationError("slice_metrics entries must be objects")
        support = int(_require_field(item, "support"))
        if support <= 0:
            raise ValidationError("slice_metrics.support must be positive")
        slices.append(
            {
                "slice": _require_non_empty(_require_field(item, "slice"), f"slice_metrics[{index}].slice"),
                "precision": _require_unit_interval(
                    _require_field(item, "precision"),
                    f"slice_metrics[{index}].precision",
                ),
                "recall": _require_unit_interval(_require_field(item, "recall"), f"slice_metrics[{index}].recall"),
                "support": support,
            }
        )
    return tuple(slices)


@dataclass(frozen=True)
class DatasetHandoffManifest:
    contract_version: str
    dataset_snapshot_ref: str
    entity_grain: str
    storage_ref: str
    labels: tuple[str, ...]
    split_policy: dict[str, str]
    split_counts: dict[str, int]
    privacy_class: str
    contains_pii: bool
    contains_customer_data: bool
    raw_media_included: bool
    approval_status: str
    production_authority: bool
    source_ref: str

    def __post_init__(self) -> None:
        if self.contract_version != DATASET_CONTRACT_VERSION:
            raise ValidationError(f"unknown dataset manifest contract_version: {self.contract_version}")
        object.__setattr__(self, "dataset_snapshot_ref", _require_dataset_snapshot_ref(self.dataset_snapshot_ref))
        object.__setattr__(self, "entity_grain", _require_non_empty(self.entity_grain, "entity_grain"))
        object.__setattr__(self, "storage_ref", _require_dataset_ref(self.storage_ref, "storage_ref"))
        object.__setattr__(self, "labels", _require_labels(self.labels))
        object.__setattr__(self, "split_policy", _require_split_policy(self.split_policy))
        object.__setattr__(self, "split_counts", _require_split_counts(self.split_counts))
        if self.privacy_class != "sanitized_metadata_only":
            raise ValidationError("privacy_class must be sanitized_metadata_only")
        if _require_bool(self.contains_pii, "contains_pii"):
            raise ValidationError("dataset manifest cannot contain PII")
        if _require_bool(self.contains_customer_data, "contains_customer_data"):
            raise ValidationError("dataset manifest cannot contain customer data")
        if _require_bool(self.raw_media_included, "raw_media_included"):
            raise ValidationError("dataset manifest cannot include raw media")
        if self.approval_status not in APPROVAL_STATUSES:
            raise ValidationError(f"unknown approval_status: {self.approval_status}")
        if _require_bool(self.production_authority, "production_authority"):
            raise ValidationError("dataset manifest cannot approve production authority")
        object.__setattr__(self, "source_ref", _require_non_empty(self.source_ref, "source_ref"))

    @classmethod
    def from_payload(cls, payload: Any) -> "DatasetHandoffManifest":
        if not isinstance(payload, dict):
            raise ValidationError("dataset manifest must be an object")
        return cls(
            contract_version=_require_field(payload, "contract_version"),
            dataset_snapshot_ref=_require_field(payload, "dataset_snapshot_ref"),
            entity_grain=_require_field(payload, "entity_grain"),
            storage_ref=_require_field(payload, "storage_ref"),
            labels=_require_field(payload, "labels"),
            split_policy=_require_field(payload, "split_policy"),
            split_counts=_require_field(payload, "split_counts"),
            privacy_class=_require_field(payload, "privacy_class"),
            contains_pii=_require_field(payload, "contains_pii"),
            contains_customer_data=_require_field(payload, "contains_customer_data"),
            raw_media_included=_require_field(payload, "raw_media_included"),
            approval_status=_require_field(payload, "approval_status"),
            production_authority=_require_field(payload, "production_authority"),
            source_ref=_require_field(payload, "source_ref"),
        )


@dataclass(frozen=True)
class EvaluationHandoffReport:
    contract_version: str
    model_ref: str
    dataset_snapshot_ref: str
    metrics: dict[str, float]
    slice_metrics: tuple[dict[str, Any], ...]
    latency_ms_p95: float
    latency_budget_ms_p95: float
    approval_status: str
    promotion_decision: str
    production_authority: bool
    source_ref: str

    def __post_init__(self) -> None:
        if self.contract_version != EVALUATION_CONTRACT_VERSION:
            raise ValidationError(f"unknown evaluation report contract_version: {self.contract_version}")
        object.__setattr__(self, "model_ref", _require_model_ref(self.model_ref))
        object.__setattr__(self, "dataset_snapshot_ref", _require_dataset_snapshot_ref(self.dataset_snapshot_ref))
        object.__setattr__(self, "metrics", _require_metrics(self.metrics))
        object.__setattr__(self, "slice_metrics", _require_slice_metrics(self.slice_metrics))
        latency_ms_p95 = float(self.latency_ms_p95)
        latency_budget_ms_p95 = float(self.latency_budget_ms_p95)
        if latency_ms_p95 <= 0 or latency_budget_ms_p95 <= 0:
            raise ValidationError("latency evidence must be positive")
        if latency_ms_p95 > latency_budget_ms_p95:
            raise ValidationError("latency_ms_p95 exceeds latency_budget_ms_p95")
        object.__setattr__(self, "latency_ms_p95", latency_ms_p95)
        object.__setattr__(self, "latency_budget_ms_p95", latency_budget_ms_p95)
        if self.approval_status not in APPROVAL_STATUSES:
            raise ValidationError(f"unknown approval_status: {self.approval_status}")
        if self.promotion_decision != "not_approved":
            raise ValidationError("promotion_decision must remain not_approved")
        if _require_bool(self.production_authority, "production_authority"):
            raise ValidationError("evaluation report cannot approve production authority")
        object.__setattr__(self, "source_ref", _require_non_empty(self.source_ref, "source_ref"))

    @classmethod
    def from_payload(cls, payload: Any) -> "EvaluationHandoffReport":
        if not isinstance(payload, dict):
            raise ValidationError("evaluation report must be an object")
        return cls(
            contract_version=_require_field(payload, "contract_version"),
            model_ref=_require_field(payload, "model_ref"),
            dataset_snapshot_ref=_require_field(payload, "dataset_snapshot_ref"),
            metrics=_require_field(payload, "metrics"),
            slice_metrics=_require_field(payload, "slice_metrics"),
            latency_ms_p95=_require_field(payload, "latency_ms_p95"),
            latency_budget_ms_p95=_require_field(payload, "latency_budget_ms_p95"),
            approval_status=_require_field(payload, "approval_status"),
            promotion_decision=_require_field(payload, "promotion_decision"),
            production_authority=_require_field(payload, "production_authority"),
            source_ref=_require_field(payload, "source_ref"),
        )


def validate_evaluation_against_dataset(
    report: EvaluationHandoffReport,
    dataset: DatasetHandoffManifest,
) -> None:
    if report.dataset_snapshot_ref != dataset.dataset_snapshot_ref:
        raise ValidationError("evaluation dataset snapshot does not match dataset manifest")
    declared_labels = set(dataset.labels)
    for item in report.slice_metrics:
        if item["slice"] not in declared_labels:
            raise ValidationError("evaluation slice is not declared by dataset manifest")
