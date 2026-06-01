"""Optional Mem0 payload adapter.

The development framework stays deterministic. This module only builds payloads
compatible with a future Mem0 client.
"""

from __future__ import annotations

from typing import Any

from f.mil.memory_contract import build_mem0_add_payload, build_mem0_search_payload


def build_add_payload(record: dict[str, Any]) -> dict[str, Any]:
    return build_mem0_add_payload(record)


def build_search_payload(query: str, *, filters: dict[str, Any], limit: int = 5) -> dict[str, Any]:
    return build_mem0_search_payload(query, filters=filters, limit=limit)
