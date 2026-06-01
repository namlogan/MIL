#!/usr/bin/env python3
"""Dispatch routed MIL webhook tasks to the local Codex worker runner."""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import re
import sys
import tempfile
from pathlib import Path
from typing import Any, Callable

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from f.mil.github_webhook_router import route_github_webhook
from f.mil.plan_to_pr_contract import build_augment_context_request, run_plan_to_pr


AUTO_BUILD_LABEL = "agent:auto-build"
AUTO_BUILD_COMMANDS = {"/agent autobuild", "/agent auto-build"}
COMPLETED_STATUSES = {"CODEX_WORKER_COMPLETED", "DRY_RUN", "SKIPPED_AGENT_EXECUTION"}
DEFAULT_LOCK_ROOT = ".ai-factory/queue/locks"


def load_codex_worker_runner():
    module_path = REPO_ROOT / "scripts" / "agent-flow" / "codex_worker.py"
    spec = importlib.util.spec_from_file_location("mil_codex_worker_runner", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load Codex worker runner from {module_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_augment_context_provider():
    module_path = REPO_ROOT / "scripts" / "agent-flow" / "augment_context_provider.py"
    spec = importlib.util.spec_from_file_location("mil_augment_context_provider", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load Augment context provider from {module_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _load_json(path: str | Path) -> dict[str, Any]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


def _write_json(path: str | Path, payload: dict[str, Any]) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _safe_id(value: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_.-]+", "-", value.strip())[:120] or "task"


def _labels(issue: dict[str, Any]) -> set[str]:
    names: set[str] = set()
    for label in issue.get("labels") or []:
        if isinstance(label, dict):
            name = label.get("name")
        else:
            name = label
        if name:
            names.add(str(name).strip().lower())
    return names


def is_auto_dispatch_requested(request: dict[str, Any]) -> bool:
    event = str(request.get("github_event") or "").strip()
    payload = request.get("payload") or {}
    if not isinstance(payload, dict):
        return False

    if event == "issues":
        issue = payload.get("issue") or {}
        return AUTO_BUILD_LABEL in _labels(issue)

    if event == "issue_comment":
        comment = payload.get("comment") or {}
        body = str(comment.get("body") or "").strip().lower()
        return any(command in body for command in AUTO_BUILD_COMMANDS)

    return False


def _augment_context_item(plan_result: dict[str, Any]) -> dict[str, str]:
    augment = (plan_result.get("artifacts") or {}).get("augment_context") or {}
    mcp_server = str(augment.get("mcp_server") or "mil-auggie-local")
    tool = str(augment.get("tool") or "codebase-retrieval")
    query = str(augment.get("query") or "")
    return {
        "source_uri": f"augment://mcp/{mcp_server}/{tool}",
        "summary": (
            "Before implementation, use Augment MCP codebase-retrieval read-only "
            f"with this query:\n{query}"
        ),
    }


def _runner_task(route: dict[str, Any], plan_result: dict[str, Any]) -> dict[str, Any]:
    artifacts = plan_result.get("artifacts") or {}
    memory = artifacts.get("memory") or {}
    augment = artifacts.get("augment_context") or {}
    task = dict(route.get("task") or {})
    task["issue_id"] = route.get("github", {}).get("issue_number") or task.get("issue_id", "")
    task["memory_context"] = memory.get("context_pack") or []
    task["augment_context"] = [
        *list(augment.get("context_pack") or []),
        _augment_context_item(plan_result),
    ]
    return task


def _claim_task(task_id: str, *, repo_root: str | Path, lock_root: str | Path) -> Path | None:
    root = Path(lock_root)
    if not root.is_absolute():
        root = Path(repo_root).resolve() / root
    root.mkdir(parents=True, exist_ok=True)
    lock_path = root / f"{_safe_id(task_id)}.lock"
    try:
        fd = os.open(str(lock_path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError:
        return None
    with os.fdopen(fd, "w", encoding="utf-8") as lock_file:
        lock_file.write(json.dumps({"task_id": task_id}, sort_keys=True) + "\n")
    return lock_path


def dispatch_request(
    request: dict[str, Any],
    *,
    repo_root: str | Path,
    dry_run: bool = False,
    execute_agent: bool = True,
    push: bool = True,
    open_pr: bool = True,
    model: str | None = None,
    sandbox: str = "workspace-write",
    approval: str = "never",
    worktree_root: str = ".ai-factory/tmp/worktrees",
    evidence_root: str = ".ai-factory/qa/codex_worker",
    lock_root: str | Path = DEFAULT_LOCK_ROOT,
    runner: Callable[..., dict[str, Any]] | None = None,
    preload_augment_context: bool = False,
    require_augment_context: bool = False,
    augment_context_provider: Callable[..., dict[str, Any]] | None = None,
) -> dict[str, Any]:
    if not is_auto_dispatch_requested(request):
        return {
            "decision": "AUTO_DISPATCH_IGNORED",
            "reason": f"missing explicit {AUTO_BUILD_LABEL} label or /agent autobuild command",
        }

    route = route_github_webhook(request)
    if not route.get("matched"):
        return {
            "decision": "AUTO_DISPATCH_IGNORED",
            "reason": route.get("reason", "webhook route did not match"),
            "route": route,
        }
    if route.get("flow") != "plan_to_pr":
        return {
            "decision": "AUTO_DISPATCH_IGNORED",
            "reason": f"route flow {route.get('flow')} is not executable by auto dispatcher",
            "route": route,
        }

    augment_context = list(request.get("augment_context") or [])
    augment_preload: dict[str, Any] = {
        "ok": False,
        "context_pack": [],
        "reasons": ["Augment context preload disabled"],
    }
    if preload_augment_context:
        augment_request = build_augment_context_request(route["task"], repo_root)
        provider = augment_context_provider or load_augment_context_provider().retrieve_context_pack
        augment_preload = provider(
            query=augment_request["query"],
            repo_root=repo_root,
        )
        if augment_preload.get("ok"):
            augment_context = [
                *list(augment_preload.get("context_pack") or []),
                *augment_context,
            ]
        elif require_augment_context:
            return {
                "decision": "AUTO_DISPATCH_BLOCKED",
                "reason": "Augment context preload is required but unavailable",
                "route": route,
                "augment_context_preload": augment_preload,
                "reasons": augment_preload.get("reasons") or ["Augment context preload failed"],
            }

    plan_options = dict(request.get("options") or {})
    plan_options["repo_root"] = str(Path(repo_root).resolve())
    plan_result = run_plan_to_pr(
        {
            "task": route["task"],
            "options": plan_options,
            "memory_context": request.get("memory_context", []),
            "augment_context": augment_context,
        }
    )
    if plan_result.get("decision") != "PLAN_TO_PR_COMMAND_PACK_READY":
        return {
            "decision": "AUTO_DISPATCH_BLOCKED",
            "route": route,
            "plan_result": plan_result,
            "reasons": plan_result.get("reasons") or ["plan_to_pr is not ready"],
        }

    task_id = str(plan_result.get("task_id") or route.get("task", {}).get("task_id") or "UNKNOWN")
    lock_path = _claim_task(task_id, repo_root=repo_root, lock_root=lock_root)
    if lock_path is None:
        return {
            "decision": "AUTO_DISPATCH_IGNORED",
            "reason": f"task {task_id} is already claimed",
            "route": route,
            "plan_result": plan_result,
        }

    worker_runner = runner or load_codex_worker_runner().run_worker
    worker_result = worker_runner(
        task=_runner_task(route, plan_result),
        repo_root=repo_root,
        dry_run=dry_run,
        execute_agent=execute_agent,
        push=push,
        open_pr=open_pr,
        model=model,
        sandbox=sandbox,
        approval=approval,
        worktree_root=worktree_root,
        evidence_root=evidence_root,
    )
    status = str(worker_result.get("status") or "")
    return {
        "decision": "AUTO_DISPATCH_COMPLETED" if status in COMPLETED_STATUSES else "AUTO_DISPATCH_FAILED",
        "lock_path": str(lock_path),
        "route": route,
        "augment_context_preload": augment_preload,
        "plan_result": plan_result,
        "worker_result": worker_result,
    }


def _self_test() -> None:
    request = {
        "github_event": "issues",
        "delivery": "self-test",
        "payload": {
            "action": "labeled",
            "repository": {"full_name": "namlogan/MIL"},
            "issue": {
                "number": 1,
                "title": "MIL-001 Auto dispatch self test",
                "body": "\n".join(
                    [
                        "### Task ID",
                        "MIL-001",
                        "",
                        "### User or business goal",
                        "Build a dry-run auto dispatch.",
                        "",
                        "### Acceptance criteria",
                        "- Dispatcher is ready.",
                        "",
                        "### Allowed files and out-of-scope files",
                        "Allowed:",
                        "- docs/**",
                        "",
                        "Out of scope:",
                        "- secrets/**",
                        "",
                        "### Required checks",
                        "- git diff --check",
                        "",
                        "### Restricted change check",
                        "- [x] none of the above",
                        "",
                        "### Rollback note",
                        "No-op.",
                    ]
                ),
                "labels": [{"name": AUTO_BUILD_LABEL}],
            },
        },
    }
    with tempfile.TemporaryDirectory() as tmpdir:
        result = dispatch_request(
            request,
            repo_root=REPO_ROOT,
            dry_run=True,
            lock_root=Path(tmpdir),
        )
    assert result["decision"] == "AUTO_DISPATCH_COMPLETED"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--request", help="Path to a GitHub webhook router request JSON.")
    parser.add_argument("--repo", default=str(REPO_ROOT), help="Local repository root.")
    parser.add_argument("--worktree-root", default=".ai-factory/tmp/worktrees")
    parser.add_argument("--evidence-root", default=".ai-factory/qa/codex_worker")
    parser.add_argument("--lock-root", default=DEFAULT_LOCK_ROOT)
    parser.add_argument("--execute-agent", action="store_true", help="Actually run codex exec.")
    parser.add_argument("--push", action="store_true", help="Push the worker branch after commit.")
    parser.add_argument("--open-pr", action="store_true", help="Open a PR after push.")
    parser.add_argument("--dry-run", action="store_true", help="Prepare the run without creating worktree or running Codex.")
    parser.add_argument("--model", help="Optional Codex model override.")
    parser.add_argument("--sandbox", default="workspace-write")
    parser.add_argument("--approval", default="never")
    parser.add_argument("--preload-augment-context", action="store_true")
    parser.add_argument("--require-augment-context", action="store_true")
    parser.add_argument("--out", help="Write dispatcher result JSON to this path.")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args(argv)

    if args.self_test:
        _self_test()
        print("auto_dispatcher self-test passed")
        return 0

    if not args.request:
        parser.error("--request is required unless --self-test is used")

    try:
        result = dispatch_request(
            _load_json(args.request),
            repo_root=args.repo,
            dry_run=args.dry_run,
            execute_agent=args.execute_agent,
            push=args.push,
            open_pr=args.open_pr,
            model=args.model,
            sandbox=args.sandbox,
            approval=args.approval,
            worktree_root=args.worktree_root,
            evidence_root=args.evidence_root,
            lock_root=args.lock_root,
            preload_augment_context=args.preload_augment_context,
            require_augment_context=args.require_augment_context,
        )
    except (OSError, RuntimeError, ValueError, json.JSONDecodeError) as exc:
        print(f"auto_dispatcher failed: {exc}", file=sys.stderr)
        return 2

    if args.out:
        _write_json(args.out, result)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result.get("decision") in {"AUTO_DISPATCH_COMPLETED", "AUTO_DISPATCH_IGNORED"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
