from __future__ import annotations

from typing import Any

from f.mil.memory_contract import build_mem0_add_payload, build_memory_record


def main(request: dict[str, Any]) -> dict[str, Any]:
    metadata = request.get("metadata") or {}
    if not isinstance(metadata, dict):
        raise ValueError("metadata must be an object")

    record = build_memory_record(
        project=str(request.get("project") or "MIL"),
        task_id=str(request.get("task_id") or ""),
        memory_type=str(request.get("memory_type") or ""),
        text=str(request.get("text") or ""),
        metadata=metadata,
        approved=bool(request.get("approved")),
    )
    return {
        "decision": "MEMORY_WRITE_RECORDED",
        "blocking": False,
        "provider": "mem0_optional",
        "record": record,
        "mem0_add_payload": build_mem0_add_payload(record),
    }
