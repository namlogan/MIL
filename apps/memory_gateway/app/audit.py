"""Audit helpers for local Memory0 gateway runs."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from f.mil.memory_contract import append_audit_event


def record(path: str | Path, *, action: str, memory: dict[str, Any], actor: str, source_ref: str) -> dict[str, Any]:
    return append_audit_event(Path(path), action=action, record=memory, actor=actor, source_ref=source_ref)
