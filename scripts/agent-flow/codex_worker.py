#!/usr/bin/env python3
"""Run a scoped MIL Codex worker from a task payload."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from f.mil.codex_worker_contract import (
    ContractError,
    build_worker_plan,
    validate_allowed_changes,
)


def _load_json(path: str | Path) -> dict[str, Any]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


def _write_json(path: str | Path, payload: dict[str, Any]) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _run_command(
    command: list[str],
    *,
    cwd: str | Path,
    input_text: str | None = None,
) -> dict[str, Any]:
    completed = subprocess.run(
        command,
        cwd=str(cwd),
        input=input_text,
        text=True,
        capture_output=True,
        check=False,
    )
    return {
        "command": command,
        "returncode": completed.returncode,
        "stdout": completed.stdout[-12000:],
        "stderr": completed.stderr[-12000:],
        "ok": completed.returncode == 0,
    }


def _changed_files(worktree_path: str | Path) -> list[str]:
    completed = subprocess.run(
        ["git", "status", "--porcelain=v1"],
        cwd=str(worktree_path),
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr.strip() or "git status failed")

    changed: list[str] = []
    for line in completed.stdout.splitlines():
        if not line:
            continue
        path = line[3:].strip()
        if " -> " in path:
            path = path.split(" -> ", 1)[1]
        if path:
            changed.append(path)
    return sorted(set(changed))


def _self_test() -> None:
    task = {
        "task_id": "SELF-TEST",
        "title": "Codex worker self test",
        "goal": "Build a non-executing worker plan.",
        "acceptance_criteria": ["Worker is ready"],
        "allowed_files": ["docs/**", "tests/**"],
        "checks": ["git diff --check"],
        "restricted_changes": [],
    }
    plan = build_worker_plan(task)
    assert plan["decision"] == "CODEX_WORKER_READY"
    assert plan["execution"]["execute_agent"] is False
    validate_allowed_changes(
        ["docs/codex-worker-runner.md"],
        allowed_files=["docs/**"],
        out_of_scope_files=[],
    )


def run_worker(
    task: dict[str, Any],
    *,
    repo_root: str | Path,
    dry_run: bool,
    execute_agent: bool,
    push: bool,
    open_pr: bool,
    model: str | None,
    sandbox: str,
    approval: str,
    worktree_root: str,
    evidence_root: str,
) -> dict[str, Any]:
    repo = Path(repo_root).resolve()
    plan = build_worker_plan(
        task,
        repo_root=repo,
        worktree_root=worktree_root,
        evidence_root=evidence_root,
        execute_agent=execute_agent,
        push=push,
        open_pr=open_pr,
        model=model,
        sandbox=sandbox,
        approval=approval,
    )

    result: dict[str, Any] = {
        **{key: value for key, value in plan.items() if key != "prompt"},
        "status": "DRY_RUN" if dry_run else "RUNNING",
        "git": {
            "worktree_created": False,
            "changed_files": [],
            "committed": False,
            "pushed": False,
            "pr_url": "",
        },
        "commands": [],
        "checks": [],
    }
    if plan["decision"] != "CODEX_WORKER_READY":
        result["status"] = "BLOCKED"
        return result

    prompt_path = Path(str(plan["prompt_path"]))
    result_path = Path(str(plan["result_path"]))
    evidence_dir = Path(str(plan["evidence_dir"]))
    evidence_dir.mkdir(parents=True, exist_ok=True)
    prompt_path.write_text(str(plan["prompt"]), encoding="utf-8")

    if dry_run:
        result["status"] = "DRY_RUN"
        return result

    worktree_path = Path(str(plan["worktree_path"]))
    if worktree_path.exists():
        raise RuntimeError(f"worktree already exists: {worktree_path}")

    add_worktree = _run_command(
        [
            "git",
            "worktree",
            "add",
            "-b",
            str(plan["branch"]),
            str(worktree_path),
            str(plan["base_branch"]),
        ],
        cwd=repo,
    )
    result["commands"].append(add_worktree)
    if not add_worktree["ok"]:
        result["status"] = "FAILED_WORKTREE"
        _write_json(result_path, result)
        return result
    result["git"]["worktree_created"] = True

    if execute_agent:
        codex = _run_command(
            list(plan["codex_command"]),
            cwd=worktree_path,
            input_text=str(plan["prompt"]),
        )
        result["commands"].append(codex)
        if not codex["ok"]:
            result["status"] = "FAILED_CODEX"
            _write_json(result_path, result)
            return result
    else:
        result["status"] = "SKIPPED_AGENT_EXECUTION"

    if execute_agent:
        for check in plan["checks"]:
            check_result = _run_command(["bash", "-lc", str(check)], cwd=worktree_path)
            result["checks"].append(check_result)
            if not check_result["ok"]:
                result["status"] = "FAILED_CHECKS"
                _write_json(result_path, result)
                return result

    changed = _changed_files(worktree_path)
    result["git"]["changed_files"] = changed
    try:
        validate_allowed_changes(
            changed,
            allowed_files=list(plan["allowed_files"]),
            out_of_scope_files=list(plan["out_of_scope_files"]),
        )
    except ValueError as exc:
        result["status"] = "FAILED_SCOPE"
        result["blocking"] = True
        result["reasons"] = [str(exc)]
        _write_json(result_path, result)
        return result

    if execute_agent and changed:
        add_result = _run_command(["git", "add", "--all"], cwd=worktree_path)
        result["commands"].append(add_result)
        if not add_result["ok"]:
            result["status"] = "FAILED_GIT_ADD"
            _write_json(result_path, result)
            return result

        commit_result = _run_command(
            [
                "git",
                "commit",
                "-m",
                f"{plan['task_id']}: implement scoped Codex worker task",
            ],
            cwd=worktree_path,
        )
        result["commands"].append(commit_result)
        if not commit_result["ok"]:
            result["status"] = "FAILED_COMMIT"
            _write_json(result_path, result)
            return result
        result["git"]["committed"] = True

    if push and result["git"]["committed"]:
        push_result = _run_command(
            ["git", "push", "-u", "origin", str(plan["branch"])],
            cwd=worktree_path,
        )
        result["commands"].append(push_result)
        if not push_result["ok"]:
            result["status"] = "FAILED_PUSH"
            _write_json(result_path, result)
            return result
        result["git"]["pushed"] = True

    if open_pr and result["git"]["pushed"]:
        pr_result = _run_command(
            [
                "gh",
                "pr",
                "create",
                "--fill",
                "--base",
                str(plan["base_branch"]),
                "--head",
                str(plan["branch"]),
            ],
            cwd=worktree_path,
        )
        result["commands"].append(pr_result)
        if not pr_result["ok"]:
            result["status"] = "FAILED_PR_CREATE"
            _write_json(result_path, result)
            return result
        result["git"]["pr_url"] = pr_result["stdout"].strip()

    if execute_agent:
        result["status"] = "CODEX_WORKER_COMPLETED"
    _write_json(result_path, result)
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task", help="Path to a task JSON payload.")
    parser.add_argument("--repo", default=".", help="Repository root.")
    parser.add_argument("--worktree-root", default=".ai-factory/tmp/worktrees")
    parser.add_argument("--evidence-root", default=".ai-factory/qa/codex_worker")
    parser.add_argument("--execute-agent", action="store_true", help="Actually run codex exec.")
    parser.add_argument("--push", action="store_true", help="Push the worker branch after commit.")
    parser.add_argument("--open-pr", action="store_true", help="Open a PR after push.")
    parser.add_argument("--dry-run", action="store_true", help="Only produce the worker plan.")
    parser.add_argument("--model", help="Optional Codex model override.")
    parser.add_argument("--sandbox", default="workspace-write")
    parser.add_argument("--approval", default="never")
    parser.add_argument("--out", help="Write result JSON to this path.")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args(argv)

    if args.self_test:
        _self_test()
        print("codex_worker self-test passed")
        return 0

    if not args.task:
        parser.error("--task is required unless --self-test is used")

    try:
        result = run_worker(
            _load_json(args.task),
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
        )
    except (ContractError, OSError, RuntimeError, ValueError, json.JSONDecodeError) as exc:
        print(f"codex_worker failed: {exc}", file=sys.stderr)
        return 2

    output = json.dumps(result, indent=2, sort_keys=True)
    if args.out:
        _write_json(args.out, result)
    print(output)
    return 0 if result.get("status") in {"DRY_RUN", "CODEX_WORKER_COMPLETED", "SKIPPED_AGENT_EXECUTION"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
