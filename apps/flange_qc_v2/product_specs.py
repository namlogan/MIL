from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from apps.flange_qc_v2.domain import DECISION_STATES, ValidationError
from apps.flange_qc_v2.sop_registry import get_reason_code


@dataclass(frozen=True)
class ProductSpecResolution:
    matched: bool
    product_code: str
    size_group: str
    approval_status: str
    production_authority: bool
    decision: str
    reason_codes: list[str]
    group_id: str | None = None
    nominal_length_in: float | None = None
    nominal_width_in: float | None = None
    length_plus_in: float | None = None
    length_minus_in: float | None = None
    width_plus_in: float | None = None
    width_minus_in: float | None = None

    def __post_init__(self) -> None:
        if self.decision not in DECISION_STATES:
            raise ValidationError(f"unknown decision: {self.decision}")
        for code in self.reason_codes:
            get_reason_code(code)


@dataclass(frozen=True)
class ProductSpecCatalog:
    schema_version: int
    approval_status: str
    approval_required: bool
    source_ref: str
    product_groups: list[dict[str, Any]]

    def resolve(self, *, product_code: str, size_group: str) -> ProductSpecResolution:
        product = str(product_code).strip()
        size = str(size_group).strip()
        group = self._find_group(product)
        if group is None:
            return self._blocked(product, size, ["UNKNOWN_PRODUCT"])
        size_spec = self._find_size(group, size)
        if size_spec is None:
            return self._blocked(product, size, ["UNKNOWN_SIZE"], group_id=str(group["group_id"]))

        tolerances = group["tolerances_in"]
        production_authority = self._has_production_authority()
        reason_codes = [] if production_authority else ["PRODUCT_SPEC_APPROVAL_MISSING"]
        return ProductSpecResolution(
            matched=True,
            product_code=product,
            size_group=size,
            group_id=str(group["group_id"]),
            nominal_length_in=float(size_spec["length_in"]),
            nominal_width_in=float(size_spec["width_in"]),
            length_plus_in=float(tolerances["length_plus"]),
            length_minus_in=float(tolerances["length_minus"]),
            width_plus_in=float(tolerances["width_plus"]),
            width_minus_in=float(tolerances["width_minus"]),
            approval_status=self.approval_status,
            production_authority=production_authority,
            decision="NOT_EVALUATED" if production_authority else "BLOCKED",
            reason_codes=reason_codes,
        )

    def _find_group(self, product_code: str) -> dict[str, Any] | None:
        for group in self.product_groups:
            if product_code in group["product_ids"]:
                return group
        return None

    def _find_size(self, group: dict[str, Any], size_group: str) -> dict[str, Any] | None:
        for size in group["sizes"]:
            if str(size["size_group"]) == size_group:
                return size
        return None

    def _blocked(
        self,
        product_code: str,
        size_group: str,
        reason_codes: list[str],
        *,
        group_id: str | None = None,
    ) -> ProductSpecResolution:
        return ProductSpecResolution(
            matched=False,
            product_code=product_code,
            size_group=size_group,
            group_id=group_id,
            approval_status=self.approval_status,
            production_authority=False,
            decision="BLOCKED",
            reason_codes=reason_codes,
        )

    def _has_production_authority(self) -> bool:
        return self.approval_required is False and self.approval_status == "approved_for_production"


def load_product_specs(path: str | Path) -> ProductSpecCatalog:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValidationError("product specs config must be an object")
    _validate_config(data)
    return ProductSpecCatalog(
        schema_version=int(data["schema_version"]),
        approval_status=str(data["status"]),
        approval_required=bool(data["approval_required"]),
        source_ref=str(data["source_ref"]),
        product_groups=list(data["product_groups"]),
    )


def _validate_config(data: dict[str, Any]) -> None:
    for field in ("schema_version", "status", "source_ref", "approval_required", "product_groups"):
        if field not in data:
            raise ValidationError(f"{field} is required")
    if not isinstance(data["product_groups"], list) or not data["product_groups"]:
        raise ValidationError("product_groups is required")
    for group in data["product_groups"]:
        _validate_group(group)


def _validate_group(group: Any) -> None:
    if not isinstance(group, dict):
        raise ValidationError("product group must be an object")
    for field in ("group_id", "product_ids", "tolerances_in", "sizes"):
        if field not in group:
            raise ValidationError(f"product group {field} is required")
    if not isinstance(group["product_ids"], list) or not group["product_ids"]:
        raise ValidationError("product group product_ids is required")
    tolerances = group["tolerances_in"]
    if not isinstance(tolerances, dict):
        raise ValidationError("tolerances_in must be an object")
    for field in ("length_plus", "length_minus", "width_plus", "width_minus"):
        _coerce_number(tolerances.get(field), f"tolerances_in.{field}")
    if not isinstance(group["sizes"], list) or not group["sizes"]:
        raise ValidationError("product group sizes is required")
    for size in group["sizes"]:
        _validate_size(size)


def _validate_size(size: Any) -> None:
    if not isinstance(size, dict):
        raise ValidationError("size must be an object")
    for field in ("size_group", "width_in", "length_in"):
        if field not in size:
            raise ValidationError(f"size {field} is required")
    _coerce_number(size["width_in"], "size.width_in")
    _coerce_number(size["length_in"], "size.length_in")


def _coerce_number(value: Any, field_name: str) -> float:
    try:
        return float(value)
    except (TypeError, ValueError) as exc:
        raise ValidationError(f"{field_name} must be a number") from exc
