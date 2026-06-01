#!/usr/bin/env python3
"""One-command operator dashboard for the MIL real-project agent factory."""

from __future__ import annotations

import argparse
import json
import subprocess
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable, NamedTuple


REPO_SLUG = "namlogan/MIL"
REQUIRED_PR_CONTEXTS = {"control-plane", "ai-gate/final-review", "merge-controller-policy"}
PUBLIC_TUNNEL_SESSION_MARKERS = (
    "mil-webhook-ngrok",
    "mil-webhook-cloudflared",
    "mil-webhook-cloudflare",
)
BLOCKING_QUEUE_DECISIONS = {"AUTO_DISPATCH_BLOCKED", "AUTO_DISPATCH_FAILED"}


class CommandResult(NamedTuple):
    returncode: int
    stdout: str
    stderr: str


Runner = Callable[[list[str], Path], CommandResult]


def run_command(command: list[str], cwd: Path) -> CommandResult:
    completed = subprocess.run(
        command,
        cwd=str(cwd),
        text=True,
        capture_output=True,
        check=False,
    )
    return CommandResult(
        returncode=completed.returncode,
        stdout=completed.stdout,
        stderr=completed.stderr,
    )


def _command_check(
    *,
    name: str,
    command: list[str],
    repo_root: Path,
    runner: Runner,
) -> dict[str, Any]:
    result = runner(command, repo_root)
    output = (result.stdout or result.stderr).strip()
    return {
        "name": name,
        "ok": result.returncode == 0,
        "returncode": result.returncode,
        "summary": output.splitlines()[0] if output else "ok",
        "command": command,
    }


def _parse_json(raw: str, default: Any) -> Any:
    try:
        return json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return default


def _git_clean_check(repo_root: Path, runner: Runner) -> dict[str, Any]:
    result = runner(["git", "status", "--short", "--branch"], repo_root)
    lines = [line for line in result.stdout.splitlines() if line.strip()]
    changes = [line for line in lines if not line.startswith("## ")]
    ok = result.returncode == 0 and not changes
    return {
        "name": "git_clean",
        "ok": ok,
        "returncode": result.returncode,
        "summary": "clean" if ok else "workspace has uncommitted changes",
        "branch": lines[0] if lines else "",
        "changes": changes,
        "command": ["git", "status", "--short", "--branch"],
    }


def _agent_tools_check(repo_root: Path, runner: Runner) -> dict[str, Any]:
    command = ["python3", "scripts/agent-flow/check_agent_tools.py"]
    result = runner(command, repo_root)
    output = (result.stdout or result.stderr).strip()
    check = {
        "name": "agent_tools",
        "ok": result.returncode == 0,
        "returncode": result.returncode,
        "summary": output.splitlines()[0] if output else "ok",
        "command": command,
    }
    if check["ok"]:
        try:
            parsed = json.loads(result.stdout)
        except (json.JSONDecodeError, TypeError):
            parsed = {}
        check["tools"] = parsed.get("tools", {})
        if isinstance(check["tools"], dict):
            missing = [
                name
                for name, tool in check["tools"].items()
                if isinstance(tool, dict) and not tool.get("available")
            ]
            check["summary"] = (
                "all agent tools available"
                if not missing
                else "missing tools: " + ", ".join(sorted(missing))
            )
    return check


def _runtime_sessions_check(repo_root: Path, runner: Runner) -> dict[str, Any]:
    command = ["tmux", "list-sessions"]
    result = runner(command, repo_root)
    sessions = [line.split(":", 1)[0] for line in result.stdout.splitlines() if line.strip()]
    relay_present = "mil-webhook-relay" in sessions
    tunnel_present = any(marker in sessions for marker in PUBLIC_TUNNEL_SESSION_MARKERS)
    ok = result.returncode == 0 and relay_present and tunnel_present
    if ok:
        summary = "relay and public tunnel sessions running"
    elif result.returncode != 0:
        summary = "tmux session check failed"
    elif not relay_present:
        summary = "relay session missing"
    else:
        summary = "public tunnel session missing"
    return {
        "name": "runtime_sessions",
        "ok": ok,
        "returncode": result.returncode,
        "summary": summary,
        "sessions": sessions,
        "relay_present": relay_present,
        "public_tunnel_present": tunnel_present,
        "command": command,
    }


def _github_open_prs_check(repo_root: Path, runner: Runner) -> dict[str, Any]:
    command = [
        "gh",
        "pr",
        "list",
        "--repo",
        REPO_SLUG,
        "--state",
        "open",
        "--json",
        "number,title,url,mergeStateStatus,statusCheckRollup",
        "--limit",
        "20",
    ]
    result = runner(command, repo_root)
    prs = _parse_json(result.stdout, [])
    actionable: list[dict[str, Any]] = []
    for pr in prs if isinstance(prs, list) else []:
        contexts = _status_contexts(pr.get("statusCheckRollup", []))
        missing_or_bad = sorted(
            context
            for context in REQUIRED_PR_CONTEXTS
            if contexts.get(context) not in {"SUCCESS", "success"}
        )
        merge_state = pr.get("mergeStateStatus", "")
        if missing_or_bad or merge_state not in {"CLEAN", "UNKNOWN"}:
            actionable.append(
                {
                    "number": pr.get("number"),
                    "url": pr.get("url"),
                    "mergeStateStatus": merge_state,
                    "missing_or_bad_contexts": missing_or_bad,
                }
            )
    ok = result.returncode == 0 and not actionable
    if result.returncode != 0:
        summary = "GitHub PR check failed"
    elif not prs:
        summary = "no open PRs"
    else:
        summary = (
            f"{len(actionable)} open PRs need attention "
            f"out of {len(prs) if isinstance(prs, list) else 0}"
        )
    return {
        "name": "github_open_prs",
        "ok": ok,
        "returncode": result.returncode,
        "summary": summary,
        "open_count": len(prs) if isinstance(prs, list) else 0,
        "actionable": actionable,
        "command": command,
    }


def _status_contexts(status_rollup: Any) -> dict[str, str]:
    contexts: dict[str, str] = {}
    if not isinstance(status_rollup, list):
        return contexts
    for item in status_rollup:
        if not isinstance(item, dict):
            continue
        name = item.get("context") or item.get("name")
        state = item.get("state") or item.get("conclusion")
        if name and state:
            contexts[str(name)] = str(state)
    return contexts


def _github_main_ci_check(repo_root: Path, runner: Runner) -> dict[str, Any]:
    command = [
        "gh",
        "run",
        "list",
        "--repo",
        REPO_SLUG,
        "--branch",
        "main",
        "--limit",
        "3",
        "--json",
        "conclusion,status,databaseId,displayTitle,createdAt,url",
    ]
    result = runner(command, repo_root)
    runs = _parse_json(result.stdout, [])
    latest = runs[0] if isinstance(runs, list) and runs else {}
    status = latest.get("status", "") if isinstance(latest, dict) else ""
    conclusion = latest.get("conclusion", "") if isinstance(latest, dict) else ""
    ok = result.returncode == 0 and status == "completed" and conclusion == "success"
    if result.returncode != 0:
        summary = "GitHub Actions check failed"
    elif not latest:
        summary = "no main CI runs found"
    elif not ok:
        summary = f"latest main CI is {conclusion or status}"
    else:
        summary = "latest main CI passed"
    return {
        "name": "github_main_ci",
        "ok": ok,
        "returncode": result.returncode,
        "summary": summary,
        "latest": latest,
        "recent_runs": runs if isinstance(runs, list) else [],
        "command": command,
    }


def _windmill_failed_jobs_check(
    repo_root: Path,
    runner: Runner,
    now: datetime,
    recent_window: timedelta = timedelta(hours=6),
) -> dict[str, Any]:
    command = [
        "wmill",
        "--workspace",
        "mil-local",
        "job",
        "list",
        "--failed",
        "--limit",
        "5",
        "--json",
    ]
    result = runner(command, repo_root)
    jobs = _parse_json(result.stdout, [])
    recent_failed = []
    for job in jobs if isinstance(jobs, list) else []:
        created_at = _parse_datetime(job.get("created_at") or job.get("createdAt"))
        if created_at and now - created_at <= recent_window:
            recent_failed.append(job)
    ok = result.returncode == 0 and not recent_failed
    if result.returncode != 0:
        summary = "Windmill failed-job check failed"
    elif recent_failed:
        hours = int(recent_window.total_seconds() // 3600)
        summary = f"{len(recent_failed)} failed Windmill jobs in the last {hours}h"
    else:
        summary = "no recent failed Windmill jobs"
    return {
        "name": "windmill_failed_jobs",
        "ok": ok,
        "returncode": result.returncode,
        "summary": summary,
        "failed_count": len(jobs) if isinstance(jobs, list) else 0,
        "recent_failed_count": len(recent_failed),
        "recent_failed": [
            {
                "id": job.get("id"),
                "script_path": job.get("script_path"),
                "created_at": job.get("created_at"),
            }
            for job in recent_failed
        ],
        "command": command,
    }


def _parse_datetime(raw: Any) -> datetime | None:
    if not raw:
        return None
    value = str(raw).replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _json_health_check(
    *,
    name: str,
    command: list[str],
    repo_root: Path,
    runner: Runner,
) -> dict[str, Any]:
    result = runner(command, repo_root)
    parsed = _parse_json(result.stdout, {})
    ok = result.returncode == 0 and bool(parsed.get("ok")) if isinstance(parsed, dict) else False
    warnings = parsed.get("warnings", []) if isinstance(parsed, dict) else []
    errors = parsed.get("errors", []) if isinstance(parsed, dict) else []
    summary = (
        "ok"
        if ok and not warnings
        else "; ".join(str(item) for item in warnings[:2])
        if ok
        else "; ".join(str(item) for item in errors[:2]) or "check failed"
    )
    return {
        "name": name,
        "ok": ok,
        "returncode": result.returncode,
        "summary": summary,
        "warnings": warnings,
        "errors": errors,
        "details": parsed if isinstance(parsed, dict) else {},
        "command": command,
    }


def _dispatch_queue_check(repo_root: Path, limit: int = 10) -> dict[str, Any]:
    queue_root = repo_root / ".ai-factory" / "queue" / "webhooks"
    if not queue_root.exists():
        return {
            "name": "dispatch_queue",
            "ok": True,
            "summary": "queue directory absent",
            "checked_count": 0,
            "blocking_count": 0,
            "blocking": [],
        }

    result_files = sorted(
        queue_root.glob("*.result.json"),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )[:limit]
    blocking: list[dict[str, Any]] = []
    for path in result_files:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as exc:
            blocking.append({"file": str(path), "decision": "UNREADABLE", "reason": str(exc)})
            continue
        decision = str(data.get("decision", ""))
        if decision in BLOCKING_QUEUE_DECISIONS:
            blocking.append(
                {
                    "file": str(path),
                    "decision": decision,
                    "reason": data.get("reason") or data.get("error") or "",
                }
            )
    return {
        "name": "dispatch_queue",
        "ok": not blocking,
        "summary": "queue recent results clear" if not blocking else f"{len(blocking)} blocking queue results",
        "checked_count": len(result_files),
        "blocking_count": len(blocking),
        "blocking": blocking,
    }


def build_daily_status(
    repo_root: str | Path,
    runner: Runner = run_command,
    now: datetime | None = None,
) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    current_time = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    checks = {
        "git_clean": _git_clean_check(root, runner),
        "ai_factory_runtime": _command_check(
            name="ai_factory_runtime",
            command=["python3", "scripts/ai-factory/bootstrap_runtime.py", "--check"],
            repo_root=root,
            runner=runner,
        ),
        "windmill_project": _command_check(
            name="windmill_project",
            command=["python3", "scripts/windmill/validate_windmill_project.py", "--self-test"],
            repo_root=root,
            runner=runner,
        ),
        "delivery_os": _command_check(
            name="delivery_os",
            command=["python3", "scripts/delivery/validate_delivery_os.py", "--self-test"],
            repo_root=root,
            runner=runner,
        ),
        "contract_skeletons": _command_check(
            name="contract_skeletons",
            command=["python3", "scripts/contracts/validate_contracts.py", "--self-test"],
            repo_root=root,
            runner=runner,
        ),
        "sdlc_metrics": _command_check(
            name="sdlc_metrics",
            command=["python3", "scripts/operator/sdlc_metrics_report.py", "--self-test"],
            repo_root=root,
            runner=runner,
        ),
        "product_ci": _json_health_check(
            name="product_ci",
            command=["python3", "scripts/product-ci/run_product_checks.py"],
            repo_root=root,
            runner=runner,
        ),
        "agent_tools": _agent_tools_check(root, runner),
        "runtime_sessions": _runtime_sessions_check(root, runner),
        "github_open_prs": _github_open_prs_check(root, runner),
        "github_main_ci": _github_main_ci_check(root, runner),
        "windmill_failed_jobs": _windmill_failed_jobs_check(root, runner, current_time),
        "augment_config": _json_health_check(
            name="augment_config",
            command=["python3", "scripts/agent-flow/check_augment_config.py"],
            repo_root=root,
            runner=runner,
        ),
        "mem0_provider": _json_health_check(
            name="mem0_provider",
            command=["python3", "scripts/agent-memory/check_mem0_provider.py"],
            repo_root=root,
            runner=runner,
        ),
        "branch_protection": _json_health_check(
            name="branch_protection",
            command=["python3", "scripts/github/check_branch_protection.py"],
            repo_root=root,
            runner=runner,
        ),
        "merge_controller": _command_check(
            name="merge_controller",
            command=["python3", "scripts/github/merge_controller.py", "--self-test"],
            repo_root=root,
            runner=runner,
        ),
        "dispatch_queue": _dispatch_queue_check(root),
    }
    overall = "ready" if all(check["ok"] for check in checks.values()) else "attention"
    return {
        "schema_version": "1.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "repo": str(root),
        "overall": overall,
        "checks": checks,
        "next_action": "dispatch agent tasks" if overall == "ready" else "inspect failing checks before dispatch",
    }


def _print_text(status: dict[str, Any]) -> None:
    print(f"MIL daily status: {status['overall']}")
    for name, check in status["checks"].items():
        marker = "OK" if check["ok"] else "ATTENTION"
        print(f"- {name}: {marker} - {check['summary']}")
    print(f"Next action: {status['next_action']}")


def run_self_test() -> None:
    def fake_runner(command: list[str], cwd: Path) -> CommandResult:
        responses = {
            ("git", "status", "--short", "--branch"): (0, "## main...origin/main\n", ""),
            ("python3", "scripts/ai-factory/bootstrap_runtime.py", "--check"): (0, "ok\n", ""),
            ("python3", "scripts/windmill/validate_windmill_project.py", "--self-test"): (0, "ok\n", ""),
            ("python3", "scripts/delivery/validate_delivery_os.py", "--self-test"): (0, "ok\n", ""),
            ("python3", "scripts/contracts/validate_contracts.py", "--self-test"): (0, "ok\n", ""),
            ("python3", "scripts/operator/sdlc_metrics_report.py", "--self-test"): (0, "ok\n", ""),
            ("python3", "scripts/agent-flow/check_agent_tools.py"): (0, '{"ok": true, "tools": {}}\n', ""),
            ("tmux", "list-sessions"): (
                0,
                "mil-webhook-relay: 1 windows\nmil-webhook-ngrok: 1 windows\n",
                "",
            ),
            (
                "gh",
                "pr",
                "list",
                "--repo",
                REPO_SLUG,
                "--state",
                "open",
                "--json",
                "number,title,url,mergeStateStatus,statusCheckRollup",
                "--limit",
                "20",
            ): (0, "[]\n", ""),
            (
                "gh",
                "run",
                "list",
                "--repo",
                REPO_SLUG,
                "--branch",
                "main",
                "--limit",
                "3",
                "--json",
                "conclusion,status,databaseId,displayTitle,createdAt,url",
            ): (
                0,
                '[{"status":"completed","conclusion":"success","databaseId":1}]\n',
                "",
            ),
            (
                "wmill",
                "--workspace",
                "mil-local",
                "job",
                "list",
                "--failed",
                "--limit",
                "5",
                "--json",
            ): (0, "[]\n", ""),
            ("python3", "scripts/agent-flow/check_augment_config.py"): (0, '{"ok": true}\n', ""),
            ("python3", "scripts/agent-memory/check_mem0_provider.py"): (0, '{"ok": true}\n', ""),
            (
                "python3",
                "scripts/product-ci/run_product_checks.py",
            ): (0, '{"ok": true, "status": "skipped", "checks": [], "errors": []}\n', ""),
            ("python3", "scripts/github/check_branch_protection.py"): (0, '{"ok": true}\n', ""),
            (
                "python3",
                "scripts/github/merge_controller.py",
                "--self-test",
            ): (0, "merge_controller self-test passed\n", ""),
        }
        return CommandResult(*responses[tuple(command)])

    status = build_daily_status(Path(__file__).resolve().parents[2], runner=fake_runner)
    assert status["overall"] == "ready", status


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", default=str(Path(__file__).resolve().parents[2]))
    parser.add_argument("--json", action="store_true", help="Print JSON instead of text.")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args(argv)

    if args.self_test:
        run_self_test()
        print("daily_status self-test passed")
        return 0

    status = build_daily_status(args.repo)
    if args.json:
        print(json.dumps(status, indent=2, sort_keys=True))
    else:
        _print_text(status)
    return 0 if status["overall"] == "ready" else 1


if __name__ == "__main__":
    raise SystemExit(main())
