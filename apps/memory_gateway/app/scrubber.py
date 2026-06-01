"""Scrubbing helpers for gateway preflight checks."""

from __future__ import annotations

from typing import Any

from f.mil.memory_contract import sanitize_value


def scrub_payload(payload: Any) -> Any:
    return sanitize_value(payload)
