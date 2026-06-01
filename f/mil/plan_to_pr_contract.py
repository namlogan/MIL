"""Real plan-to-PR orchestration for MIL Windmill dispatch."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from f.mil.codex_worker_contract import (
    DEFAULT_APPROVAL,
    DEFAULT_EVIDENCE_ROOT,
    DEFAULT_SANDBOX,
    DEFAULT_WORKTREE_ROOT,
    ContractError,
    build_worker_plan,
    redact_secrets,
)


AUGMENT_MCP_SERVER = "mil-auggie-local"
AUGMENT_MCP_TOOL = "codebase-retrieval"
MAX_CONTEXT_TEXT = 4000

ROLES = {
    "codex": "implementation_test_and_qa_worker",
    "augment_context": "codebase_index_and_context_provider",
    "mem0_memory": "sanitized_long_term_agent_memory_layer",
    "windmill": "cockpit_and_orchestrator",
}


def _agent_call(agent: str, action: str, task_id: str) -> dict[str, str]:
    return {
        "agent": agent,
        "action": action,
        "task_id": task_id,
        "role": ROLES[agent],
    }


def _request_parts(request: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    if not isinstance(request, dict):
        raise ContractError("plan_to_pr request must be an object")
    task = request.get("task") if "task" in request else request
    options = request.get("options") or {}
    if not isinstance(task, dict):
        raise ContractError("task must be an object")
    if not isinstance(options, dict):
        raise ContractError("options must be an object")
    return task, options


def _task_id(task: dict[str, Any]) -> str:
    return redact_secrets(task.get("task_id") or task.get("issue_id") or "UNKNOWN")


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [redact_secrets(item).strip() for item in value if str(item).strip()]


def _compact_context_items(value: Any, *, text_key: str) -> list[dict[str, str]]:
    if not isinstance(value, list):
        return []

    context: list[dict[str, str]] = []
    for index, item in enumerate(value[:12], start=1):
        if isinstance(item, dict):
            source_ref = redact_secrets(
                item.get("source_ref") or item.get("source_uri") or item.get("uri") or ""
            )
            summary = redact_secrets(
                item.get(text_key)
                or item.get("summary")
                or item.get("memory")
                or item.get("content")
                or ""
            ).strip()
            context.append(
                {
                    "memory_id": redact_secrets(item.get("memory_id") or item.get("id") or f"context-{index}"),
                    "source_ref": source_ref,
                    text_key: summary[:MAX_CONTEXT_TEXT],
                }
            )
            continue

        context.append(
            {
                "memory_id": f"context-{index}",
                "source_ref": "",
                text_key: redact_secrets(item)[:MAX_CONTEXT_TEXT],
            }
        )
    return context


def _memory_context(request: dict[str, Any], task: dict[str, Any]) -> list[dict[str, str]]:
    for key in ("memory_context", "mem0_context", "context_pack"):
        context = _compact_context_items(request.get(key), text_key="memory")
        if context:
            return context
    for key in ("memory_context", "mem0_context", "context_pack"):
        context = _compact_context_items(task.get(key), text_key="memory")
        if context:
            return context
    return []


def _provided_augment_context(request: dict[str, Any], task: dict[str, Any]) -> list[dict[str, str]]:
    for key in ("augment_context", "augment_context_pack", "codebase_context"):
        context = _compact_context_items(request.get(key), text_key="summary")
        if context:
            return context
    for key in ("augment_context", "augment_context_pack", "codebase_context"):
        context = _compact_context_items(task.get(key), text_key="summary")
        if context:
            return context
    return []


def build_augment_context_request(task: dict[str, Any], repo_root: str | Path) -> dict[str, Any]:
    title = redact_secrets(task.get("title") or task.get("task_id") or "")
    goal = redact_secrets(task.get("goal") or "")
    allowed_files = _string_list(task.get("allowed_files"))
    out_of_scope = _string_list(task.get("out_of_scope_files"))
    acceptance = _string_list(task.get("acceptance_criteria"))
    checks = _string_list(task.get("checks") or task.get("required_checks"))

    query_lines = [
        f"Task: {title}",
        f"Goal: {goal}",
        "Use Augment MCP codebase-retrieval to inspect relevant MIL files before Codex edits.",
        "Focus on allowed files and nearby contracts; stay read-only.",
        "Allowed files:",
        *[f"- {item}" for item in allowed_files],
        "Out of scope:",
        *[f"- {item}" for item in out_of_scope],
        "Acceptance criteria:",
        *[f"- {item}" for item in acceptance],
        "Required checks:",
        *[f"- {item}" for item in checks],
    ]
    return {
        "provider": "augment_mcp",
        "mcp_server": AUGMENT_MCP_SERVER,
        "tool": AUGMENT_MCP_TOOL,
        "mode": "readonly",
        "repo_root": str(Path(repo_root).resolve()),
        "query": "\n".join(line for line in query_lines if line.strip())[:MAX_CONTEXT_TEXT],
        "context_pack": [],
        "instructions": [
            "Use Augment only for codebase context, symbol lookup, and risk notes.",
            "Do not let Augment/Auggie edit files, create branches, write commits, open PRs, or approve merge.",
            "If retrieved context conflicts with issue scope or AI Factory rules, stop and request human review.",
        ],
    }


def _augment_prompt_context(
    augment_request: dict[str, Any],
    provided_context: list[dict[str, str]],
) -> list[dict[str, str]]:
    query = str(augment_request["query"])
    request_item = {
        "source_uri": f"augment://mcp/{AUGMENT_MCP_SERVER}/{AUGMENT_MCP_TOOL}",
        "summary": (
            "Before implementation, use Augment MCP codebase-retrieval read-only "
            f"with this query:\n{query}"
        )[:MAX_CONTEXT_TEXT],
    }
    return [*provided_context, request_item]


def _blocked(
    task_id: str,
    reason: str,
    *,
    artifacts: dict[str, Any] | None = None,
    agent_calls: list[dict[str, str]] | None = None,
) -> dict[str, Any]:
    return {
        "flow": "plan_to_pr",
        "task_id": task_id,
        "decision": "PLAN_TO_PR_BLOCKED",
        "blocking": True,
        "reasons": [redact_secrets(reason)],
        "agent_calls": agent_calls or [],
        "artifacts": artifacts or {},
    }


def run_plan_to_pr(request: dict[str, Any]) -> dict[str, Any]:
    try:
        task, options = _request_parts(request)
        task_id = _task_id(task)
        repo_root = options.get("repo_root", ".")
        memory_context = _memory_context(request, task)
        provided_augment_context = _provided_augment_context(request, task)
        augment_request = build_augment_context_request(task, repo_root)
        augment_request["context_pack"] = provided_augment_context

        worker_task = {
            **task,
            "memory_context": memory_context,
            "augment_context": _augment_prompt_context(
                augment_request,
                provided_augment_context,
            ),
        }

        agent_calls = [
            _agent_call("mem0_memory", "wm_task_context_pack", task_id),
            _agent_call("augment_context", "provide_codebase_context", task_id),
            _agent_call("windmill", "dispatch_coding_agent", task_id),
        ]

        worker = build_worker_plan(
            worker_task,
            repo_root=repo_root,
            worktree_root=options.get("worktree_root", DEFAULT_WORKTREE_ROOT),
            evidence_root=options.get("evidence_root", DEFAULT_EVIDENCE_ROOT),
            execute_agent=bool(options.get("execute_agent", False)),
            push=bool(options.get("push", False)),
            open_pr=bool(options.get("open_pr", False)),
            model=options.get("model") or None,
            sandbox=str(options.get("sandbox") or DEFAULT_SANDBOX),
            approval=str(options.get("approval") or DEFAULT_APPROVAL),
            rule_sources=options.get("rule_sources") or options.get("ai_factory_rule_sources"),
        )
        artifacts = {
            "summary": f"plan_to_pr prepared Codex worker dispatch for {task_id}",
            "memory": {
                "provider": "mem0_memory",
                "context_pack": memory_context,
                "records": ["developer_handoff", "review_note"]
                if worker.get("decision") == "CODEX_WORKER_READY"
                else [],
            },
            "augment_context": augment_request,
            "dispatch": {
                "developer_agent": "codex",
                "context_provider": "augment_context",
                "branch": worker.get("branch", ""),
                "requires_pull_request": True,
            },
            "codex_worker": worker,
        }

        if worker.get("decision") != "CODEX_WORKER_READY":
            return _blocked(
                task_id,
                "; ".join(worker.get("reasons") or ["codex_worker is not ready"]),
                artifacts=artifacts,
                agent_calls=agent_calls,
            )

        agent_calls.append(_agent_call("codex", "prepare_command_pack", task_id))
        return {
            "flow": "plan_to_pr",
            "task_id": task_id,
            "decision": "PLAN_TO_PR_COMMAND_PACK_READY",
            "blocking": False,
            "reasons": [],
            "agent_calls": agent_calls,
            "artifacts": artifacts,
        }
    except (ContractError, ValueError, TypeError) as exc:
        task = request.get("task") if isinstance(request, dict) else {}
        task_id = _task_id(task) if isinstance(task, dict) else "UNKNOWN"
        return _blocked(
            task_id,
            str(exc),
            artifacts={
                "codex_worker": {
                    "decision": "CODEX_WORKER_BLOCKED",
                    "blocking": True,
                    "reasons": [redact_secrets(str(exc))],
                    "codex_command": [],
                    "codex_stdin_prompt": False,
                }
            },
        )


def main(request: dict[str, Any] | None = None) -> dict[str, Any]:
    return run_plan_to_pr(request or {})
