"""Schema helpers for the MIL memory gateway."""

from __future__ import annotations

from typing import Any

from f.mil.memory_contract import validate_memory_event


def validate_event(payload: dict[str, Any]) -> dict[str, Any]:
    return validate_memory_event(payload)
