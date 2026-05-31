"""Windmill entrypoint for the MIL Codex worker command pack."""

from __future__ import annotations

from typing import Any

from f.mil.codex_worker_contract import ContractError, build_worker_plan


def main(request: dict[str, Any] | None = None) -> dict[str, Any]:
    request = request or {}
    task = request.get("task") or request
    options = request.get("options") or {}
    if not isinstance(task, dict):
        raise ContractError("task must be an object")
    if not isinstance(options, dict):
        raise ContractError("options must be an object")

    return build_worker_plan(
        task,
        repo_root=options.get("repo_root", "."),
        worktree_root=options.get("worktree_root", ".ai-factory/tmp/worktrees"),
        evidence_root=options.get("evidence_root", ".ai-factory/qa/codex_worker"),
        execute_agent=bool(options.get("execute_agent", False)),
        push=bool(options.get("push", False)),
        open_pr=bool(options.get("open_pr", False)),
        model=options.get("model") or None,
        sandbox=str(options.get("sandbox") or "workspace-write"),
        approval=str(options.get("approval") or "never"),
        rule_sources=options.get("rule_sources") or options.get("ai_factory_rule_sources"),
    )
