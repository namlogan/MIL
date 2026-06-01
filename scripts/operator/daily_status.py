#!/usr/bin/env python3
"""One-command operator dashboard for the MIL solo-agent factory."""

from __future__ import annotations

import argparse
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, NamedTuple


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
    return check


def build_daily_status(repo_root: str | Path, runner: Runner = run_command) -> dict[str, Any]:
    root = Path(repo_root).resolve()
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
        "agent_tools": _agent_tools_check(root, runner),
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
            ("python3", "scripts/agent-flow/check_agent_tools.py"): (0, '{"ok": true, "tools": {}}\n', ""),
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
