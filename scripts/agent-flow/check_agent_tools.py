#!/usr/bin/env python3
"""Check local availability of MIL agent worker CLIs."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from typing import Callable


Runner = Callable[[list[str]], tuple[int, str, str]]


TOOLS = {
    "codex": ["codex", "--version"],
    "auggie": ["auggie", "--version"],
}


def subprocess_runner(command: list[str]) -> tuple[int, str, str]:
    try:
        completed = subprocess.run(
            command,
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except FileNotFoundError as exc:
        return 127, "", str(exc)

    return completed.returncode, completed.stdout.strip(), completed.stderr.strip()


def check_tools(runner: Runner = subprocess_runner) -> dict[str, object]:
    tools: dict[str, dict[str, object]] = {}
    for name, command in TOOLS.items():
        returncode, stdout, stderr = runner(command)
        tools[name] = {
            "available": returncode == 0,
            "command": command,
            "returncode": returncode,
            "version": stdout.splitlines()[0] if stdout else "",
            "error": stderr,
        }

    return {
        "ok": all(tool["available"] for tool in tools.values()),
        "tools": tools,
    }


def run_self_test() -> None:
    def fake_runner(command: list[str]) -> tuple[int, str, str]:
        return 0, f"{command[0]} 1.0.0", ""

    result = check_tools(runner=fake_runner)
    assert result["ok"] is True
    assert result["tools"]["codex"]["available"] is True  # type: ignore[index]
    assert result["tools"]["auggie"]["available"] is True  # type: ignore[index]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true", help="Run built-in tests.")
    parser.add_argument(
        "--allow-missing",
        action="store_true",
        help="Return success even when a tool is missing.",
    )
    args = parser.parse_args(argv)

    if args.self_test:
        run_self_test()
        print("check_agent_tools self-test passed")
        return 0

    result = check_tools()
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["ok"] or args.allow_missing else 1


if __name__ == "__main__":
    raise SystemExit(main())

