from __future__ import annotations

from typing import Any

from f.mil.memory_contract import (
    build_context_pack,
    build_mem0_search_payload,
    build_search_filters,
    search_records,
)


def main(request: dict[str, Any]) -> dict[str, Any]:
    memory_types = request.get("memory_types") or request.get("memory_type") or []
    if isinstance(memory_types, str):
        memory_types = [memory_types]

    filters = build_search_filters(
        tenant_id=request.get("tenant_id"),
        workspace_id=request.get("workspace_id"),
        repo_id=request.get("repo_id"),
        memory_types=list(memory_types),
        status=str(request.get("status") or "active"),
        visibility=str(request.get("visibility") or "repo"),
        branch=request.get("branch"),
        user_id=request.get("user_id"),
        agent_id=request.get("agent_id"),
        app_id=request.get("app_id"),
        run_id=request.get("run_id"),
    )
    query = str(request.get("query") or "").strip()
    limit = int(request.get("limit") or 5)
    records = request.get("records") or []
    if not isinstance(records, list):
        raise ValueError("records must be a list when provided")

    results = search_records(records, query, filters=filters, limit=limit)
    return {
        "decision": "MEMORY_CONTEXT_READY",
        "blocking": False,
        "provider": "mem0_optional",
        "filters": filters,
        "mem0_search_payload": build_mem0_search_payload(query, filters=filters, limit=limit),
        "context_pack": build_context_pack(results),
    }
