#!/usr/bin/env python3
"""Build a GitHub commit status payload from a final AI gate result."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


DEFAULT_CONTEXT = "ai-gate/final-review"


def _decision(gate: dict[str, Any]) -> str:
    return str(gate.get("decision") or "BLOCKED_NEEDS_HUMAN").strip().upper()


def _state_for_gate(gate: dict[str, Any]) -> str:
    if gate.get("blocking") is True:
        return "failure"
    if _decision(gate) == "APPROVE_MERGE":
        return "success"
    return "failure"


def _description_for_gate(gate: dict[str, Any]) -> str:
    decision = _decision(gate)
    if _state_for_gate(gate) == "success":
        return f"{decision}: local AI gate passed."
    return f"{decision}: local AI gate requires attention."


def build_status_payload(
    gate: dict[str, Any],
    target_url: str,
    context: str = DEFAULT_CONTEXT,
) -> dict[str, str]:
    return {
        "state": _state_for_gate(gate),
        "context": context,
        "description": _description_for_gate(gate),
        "target_url": target_url,
    }


def read_gate(path: str | None) -> dict[str, Any]:
    raw = Path(path).read_text(encoding="utf-8") if path else sys.stdin.read()
    data = json.loads(raw)
    if not isinstance(data, dict):
        raise ValueError("gate result must be a JSON object")
    return data


def run_self_test() -> None:
    success = build_status_payload(
        {"decision": "APPROVE_MERGE", "blocking": False},
        "https://github.com/namlogan/MIL/pull/2",
    )
    assert success["state"] == "success"
    blocked = build_status_payload(
        {"decision": "BLOCKED_NEEDS_HUMAN", "blocking": True},
        "https://github.com/namlogan/MIL/pull/2",
    )
    assert blocked["state"] == "failure"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", nargs="?", help="Final gate JSON file. Defaults to stdin.")
    parser.add_argument("--target-url", required=False, help="URL shown on the GitHub status.")
    parser.add_argument("--context", default=DEFAULT_CONTEXT, help="GitHub status context.")
    parser.add_argument("--self-test", action="store_true", help="Run built-in tests.")
    args = parser.parse_args(argv)

    if args.self_test:
        run_self_test()
        print("github_status_payload self-test passed")
        return 0

    if not args.target_url:
        print("--target-url is required unless --self-test is used", file=sys.stderr)
        return 2

    try:
        payload = build_status_payload(read_gate(args.path), args.target_url, args.context)
    except (json.JSONDecodeError, ValueError) as exc:
        print(f"Invalid gate result: {exc}", file=sys.stderr)
        return 3

    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if payload["state"] == "success" else 1


if __name__ == "__main__":
    raise SystemExit(main())

