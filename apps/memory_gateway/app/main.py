"""Local Memory Gateway facade for app-style imports."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from f.mil.memory_contract import (
    DEFAULT_AUDIT_PATH,
    DEFAULT_STORE_PATH,
    LocalJsonlMemoryStore,
    build_memory_record,
    build_search_filters,
)


def add_memory(request: dict[str, Any], *, store_path: str | Path = DEFAULT_STORE_PATH) -> dict[str, Any]:
    record = build_memory_record(
        project=str(request.get("project") or "MIL"),
        task_id=str(request.get("task_id") or ""),
        memory_type=str(request.get("memory_type") or ""),
        text=str(request.get("content") or request.get("text") or ""),
        metadata=request.get("metadata") if isinstance(request.get("metadata"), dict) else {},
        approved=bool(request.get("approved")),
    )
    store = LocalJsonlMemoryStore(Path(store_path))
    return store.add(record, audit_path=DEFAULT_AUDIT_PATH)


def search_memory(request: dict[str, Any], *, store_path: str | Path = DEFAULT_STORE_PATH) -> list[dict[str, Any]]:
    memory_types = request.get("memory_types") or []
    if isinstance(memory_types, str):
        memory_types = [memory_types]
    filters = build_search_filters(
        tenant_id=request.get("tenant_id"),
        repo_id=request.get("repo_id"),
        project_id=request.get("project_id"),
        framework_id=request.get("framework_id"),
        memory_types=list(memory_types),
        user_id=request.get("user_id"),
        agent_id=request.get("agent_id"),
        app_id=request.get("app_id"),
        run_id=request.get("run_id"),
    )
    store = LocalJsonlMemoryStore(Path(store_path))
    return store.search(str(request.get("query") or ""), filters=filters, audit_path=DEFAULT_AUDIT_PATH)
