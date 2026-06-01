#!/usr/bin/env python3
"""Integration smoke for MIL memory flow and Mem0 OSS library mode."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from f.mil import mem0_writeback, plan_to_pr
from f.mil.memory_contract import (
    build_context_pack,
    build_search_filters,
    sanitize_value,
)


def sample_metadata() -> dict[str, Any]:
    return {
        "tenant_id": "org_mil",
        "workspace_id": "engineering",
        "repo": "MIL",
        "repo_id": "github:namlogan/MIL",
        "user_id": "repo:github:namlogan/MIL",
        "agent_id": "codex",
        "app_id": "mil-framework",
        "run_id": "mem0-integration-smoke",
        "project_id": "mil",
        "framework_id": "ai-factory-sdlc",
        "source_ref": "https://github.com/namlogan/MIL/pull/local-smoke",
        "source_type": "pull_request",
        "confidence": "high",
        "scope": "framework",
        "status": "approved",
        "sensitivity": "internal",
        "visibility": "repo",
        "created_by": "memory_gateway",
        "approved_by": "PM_Logan",
    }


def sample_writeback_record(
    *,
    text: str = "Use library-first Mem0 during framework development; do not start Docker.",
) -> dict[str, Any]:
    return mem0_writeback.main(
        {
            "project": "MIL",
            "task_id": "MEM0-INTEGRATION-SMOKE",
            "memory_type": "framework_rule",
            "text": text,
            "metadata": sample_metadata(),
            "approved": True,
        }
    )


def sample_filters() -> dict[str, Any]:
    return build_search_filters(
        tenant_id="org_mil",
        workspace_id="engineering",
        repo_id="github:namlogan/MIL",
        memory_types=["framework_rule"],
        status="approved",
        visibility="repo",
        framework_id="ai-factory-sdlc",
        scope="framework",
        sensitivity="internal",
        user_id="repo:github:namlogan/MIL",
        agent_id="codex",
        run_id="mem0-integration-smoke",
    )


def build_python_mem0_add_kwargs(record: dict[str, Any]) -> dict[str, Any]:
    metadata = sanitize_value(record.get("metadata") or {})
    entity_scope = record.get("entity_scope") or {}
    if not isinstance(metadata, dict):
        raise ValueError("record.metadata must be an object")
    if not isinstance(entity_scope, dict):
        raise ValueError("record.entity_scope must be an object")

    kwargs: dict[str, Any] = {
        "messages": [{"role": "user", "content": str(record.get("memory") or "")}],
        "metadata": metadata,
        "infer": False,
        "memory_type": str(record.get("memory_type") or metadata.get("memory_type") or ""),
    }
    for field in ("user_id", "agent_id", "run_id"):
        if entity_scope.get(field):
            kwargs[field] = str(entity_scope[field])
    return kwargs


def add_record_to_mem0(memory_client: Any, record: dict[str, Any]) -> Any:
    kwargs = build_python_mem0_add_kwargs(record)
    return memory_client.add(**kwargs)


def _normalize_mem0_results(result: Any) -> list[dict[str, Any]]:
    if isinstance(result, dict):
        raw_results = result.get("results", [])
    else:
        raw_results = result
    if not isinstance(raw_results, list):
        return []

    normalized: list[dict[str, Any]] = []
    for item in raw_results:
        if not isinstance(item, dict):
            continue
        metadata = item.get("metadata") if isinstance(item.get("metadata"), dict) else {}
        memory_type = item.get("memory_type") or metadata.get("memory_type")
        normalized.append(
            {
                "id": item.get("id") or item.get("memory_id"),
                "memory_id": item.get("id") or item.get("memory_id"),
                "memory": item.get("memory") or item.get("content") or "",
                "memory_type": memory_type or "",
                "metadata": metadata,
                "entity_scope": {
                    key: item.get(key) or metadata.get(key)
                    for key in ("user_id", "agent_id", "app_id", "run_id")
                    if item.get(key) or metadata.get(key)
                },
            }
        )
    return normalized


def search_mem0_context(
    memory_client: Any,
    *,
    query: str,
    filters: dict[str, Any],
    limit: int = 5,
) -> list[dict[str, Any]]:
    result = memory_client.search(query, top_k=limit, filters=filters)
    return build_context_pack(_normalize_mem0_results(result))


class FakeMem0Memory:
    def __init__(self) -> None:
        self.add_calls: list[dict[str, Any]] = []
        self.search_calls: list[dict[str, Any]] = []
        self.records: list[dict[str, Any]] = []

    def add(self, **kwargs: Any) -> dict[str, Any]:
        self.add_calls.append(kwargs)
        memory = kwargs["messages"][0]["content"]
        metadata = kwargs.get("metadata") if isinstance(kwargs.get("metadata"), dict) else {}
        record = {
            "id": "mem_fake_1",
            "memory": memory,
            "metadata": metadata,
            "user_id": kwargs.get("user_id"),
            "agent_id": kwargs.get("agent_id"),
            "run_id": kwargs.get("run_id"),
        }
        self.records.append(record)
        return {"results": [record]}

    def search(self, query: str, **kwargs: Any) -> dict[str, Any]:
        self.search_calls.append({"query": query, **kwargs})
        return {"results": self.records}


def sample_plan_task() -> dict[str, Any]:
    return {
        "task_id": "MEM0-INTEGRATION-SMOKE",
        "issue_id": "https://github.com/namlogan/MIL/issues/local-smoke",
        "title": "Verify Mem0 framework integration",
        "goal": "Confirm Mem0 memory context reaches Codex worker prompt.",
        "acceptance_criteria": [
            "Mem0 writeback produces a sanitized memory record.",
            "Mem0 library adapter returns a context pack.",
            "plan_to_pr injects the context pack into the Codex worker prompt.",
        ],
        "allowed_files": [
            "scripts/agent-memory/**",
            "f/mil/**",
            "tests/**",
            "docs/**",
        ],
        "out_of_scope_files": [".env", ".ai-factory/secrets/**"],
        "checks": ["python3 -m unittest tests.test_mem0_framework_integration -v"],
        "base_branch": "main",
        "developer_agent": "codex",
        "restricted_changes": [],
        "rollback_note": "Revert the integration smoke change.",
    }


def run_framework_smoke(repo_root: str | Path = REPO_ROOT) -> dict[str, Any]:
    fake = FakeMem0Memory()
    writeback = sample_writeback_record()
    add_record_to_mem0(fake, writeback["record"])
    context_pack = search_mem0_context(
        fake,
        query="library-first Mem0",
        filters=sample_filters(),
        limit=5,
    )
    plan = plan_to_pr.main(
        {
            "task": sample_plan_task(),
            "options": {
                "repo_root": str(Path(repo_root).resolve()),
                "execute_agent": False,
                "push": False,
                "open_pr": False,
            },
            "memory_context": context_pack,
            "augment_context": [
                {
                    "source_uri": "augment://local-smoke",
                    "summary": "Mem0 framework integration smoke only; no codebase edit required.",
                }
            ],
        }
    )
    prompt = plan.get("artifacts", {}).get("codex_worker", {}).get("prompt", "")
    return {
        "ok": bool(
            writeback.get("decision") == "MEMORY_WRITE_RECORDED"
            and len(fake.add_calls) == 1
            and len(fake.search_calls) == 1
            and context_pack
            and plan.get("decision") == "PLAN_TO_PR_COMMAND_PACK_READY"
            and "library-first Mem0" in prompt
        ),
        "writeback_decision": writeback.get("decision"),
        "mem0_add_calls": len(fake.add_calls),
        "mem0_search_calls": len(fake.search_calls),
        "context_pack_count": len(context_pack),
        "context_pack": context_pack,
        "plan_to_pr_decision": plan.get("decision"),
        "codex_prompt_excerpt": prompt[prompt.find("library-first Mem0") - 80 : prompt.find("library-first Mem0") + 160]
        if "library-first Mem0" in prompt
        else "",
    }


def run_self_test() -> None:
    result = run_framework_smoke()
    assert result["ok"], result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", default=str(REPO_ROOT))
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args(argv)

    if args.self_test:
        run_self_test()
        print("mem0_framework_integration self-test passed")
        return 0

    result = run_framework_smoke(args.repo)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
