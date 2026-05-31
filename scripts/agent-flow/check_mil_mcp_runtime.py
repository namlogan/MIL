#!/usr/bin/env python3
"""Check that Codex can see a MIL-scoped Augment MCP server."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


SERVER_NAME = "mil-auggie-local"
WRAPPER_RELATIVE_PATH = "scripts/agent-flow/auggie_mcp_server.sh"
TOOL_NAME = "codebase-retrieval"


def _expected_command(repo_root: Path) -> str:
    return str((repo_root / WRAPPER_RELATIVE_PATH).resolve())


def parse_codex_mcp_list(output: str, repo_root: Path) -> dict[str, bool]:
    expected = _expected_command(repo_root)
    server_line = next(
        (line.strip() for line in output.splitlines() if line.strip().startswith(SERVER_NAME)),
        "",
    )
    return {
        "server_present": bool(server_line),
        "server_enabled": " enabled " in f" {server_line} ",
        "command_matches_repo": expected in server_line,
    }


def _json_lines(output: str) -> list[dict[str, Any]]:
    values: list[dict[str, Any]] = []
    for line in output.splitlines():
        stripped = line.strip()
        if not stripped.startswith("{"):
            continue
        try:
            value = json.loads(stripped)
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            values.append(value)
    return values


def parse_mcp_smoke(stdout: str, stderr: str, repo_root: Path) -> dict[str, bool]:
    tools: list[dict[str, Any]] = []
    for item in _json_lines(stdout):
        result = item.get("result")
        if isinstance(result, dict) and isinstance(result.get("tools"), list):
            tools = [tool for tool in result["tools"] if isinstance(tool, dict)]

    tool_available = any(tool.get("name") == TOOL_NAME for tool in tools)
    workspace_marker = f"Workspace indexing complete: {repo_root.resolve()}"
    mil_workspace_indexed = workspace_marker in stderr
    return {
        "tool_available": tool_available,
        "mil_workspace_indexed": mil_workspace_indexed,
        "ok": tool_available and mil_workspace_indexed,
    }


def run_codex_mcp_list(repo_root: Path) -> dict[str, bool]:
    completed = subprocess.run(
        ["codex", "mcp", "list"],
        cwd=repo_root,
        text=True,
        capture_output=True,
        check=False,
    )
    result = parse_codex_mcp_list(completed.stdout + completed.stderr, repo_root)
    result["command_succeeded"] = completed.returncode == 0
    return result


def run_mcp_smoke(repo_root: Path, timeout_seconds: int = 15) -> dict[str, bool]:
    wrapper = repo_root / WRAPPER_RELATIVE_PATH
    messages = "\n".join(
        [
            json.dumps(
                {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "initialize",
                    "params": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {},
                        "clientInfo": {"name": "mil-mcp-runtime-check", "version": "1.0"},
                    },
                }
            ),
            json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}}),
            json.dumps({"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}),
            "",
        ]
    )
    try:
        completed = subprocess.run(
            [str(wrapper)],
            cwd=repo_root,
            input=messages,
            text=True,
            capture_output=True,
            timeout=timeout_seconds,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout if isinstance(exc.stdout, str) else ""
        stderr = exc.stderr if isinstance(exc.stderr, str) else ""
        result = parse_mcp_smoke(stdout, stderr, repo_root)
        result["command_succeeded"] = False
        result["timed_out"] = True
        return result

    result = parse_mcp_smoke(completed.stdout, completed.stderr, repo_root)
    result["command_succeeded"] = completed.returncode == 0
    result["timed_out"] = False
    return result


def check_runtime(repo_root: Path, include_mcp_smoke: bool = False) -> dict[str, Any]:
    mcp_list = run_codex_mcp_list(repo_root)
    checks: dict[str, Any] = {"codex_mcp_list": mcp_list}
    ok = all(mcp_list.values())

    if include_mcp_smoke:
        smoke = run_mcp_smoke(repo_root)
        checks["mcp_smoke"] = smoke
        ok = ok and bool(smoke.get("ok"))

    return {"ok": ok, "checks": checks}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", default=".")
    parser.add_argument(
        "--mcp-smoke",
        action="store_true",
        help="Start the MIL Auggie MCP wrapper and verify codebase-retrieval is listed.",
    )
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args(argv)

    repo_root = Path(args.repo).resolve()
    result = check_runtime(repo_root, include_mcp_smoke=args.mcp_smoke)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
