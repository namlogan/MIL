#!/usr/bin/env python3
"""Build a GitHub Checks API payload from a final AI gate result."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


CONCLUSIONS_BY_DECISION = {
    "APPROVE_MERGE": "success",
    "REQUEST_CHANGES": "failure",
    "REJECT": "failure",
    "BLOCKED_NEEDS_HUMAN": "action_required",
}


def build_summary(gate: dict[str, Any]) -> str:
    lines: list[str] = []

    reasons = gate.get("reasons") or []
    residual_risks = gate.get("residual_risks") or []
    tests = gate.get("tests") or []

    if reasons:
        lines.append("Reasons:")
        lines.extend(f"- {reason}" for reason in reasons)

    if tests:
        if lines:
            lines.append("")
        lines.append("Tests:")
        lines.extend(f"- {test}" for test in tests)

    if residual_risks:
        if lines:
            lines.append("")
        lines.append("Residual risks:")
        lines.extend(f"- {risk}" for risk in residual_risks)

    return "\n".join(lines) if lines else "No blocking reasons or residual risks reported."


def build_check_payload(name: str, head_sha: str, gate: dict[str, Any]) -> dict[str, Any]:
    decision = str(gate.get("decision") or "BLOCKED_NEEDS_HUMAN").strip().upper()
    if gate.get("blocking") is True and decision == "APPROVE_MERGE":
        decision = "BLOCKED_NEEDS_HUMAN"

    conclusion = CONCLUSIONS_BY_DECISION.get(decision, "action_required")

    return {
        "name": name,
        "head_sha": head_sha,
        "status": "completed",
        "conclusion": conclusion,
        "output": {
            "title": decision,
            "summary": build_summary(gate),
        },
    }


def read_gate(path: str | None) -> dict[str, Any]:
    raw = Path(path).read_text(encoding="utf-8") if path else sys.stdin.read()
    data = json.loads(raw)
    if not isinstance(data, dict):
        raise ValueError("gate result must be a JSON object")
    return data


def run_self_test() -> None:
    payload = build_check_payload(
        "ai-gate/final-review",
        "abc123",
        {"decision": "APPROVE_MERGE", "pass": True},
    )
    assert payload["conclusion"] == "success"
    blocked = build_check_payload(
        "ai-gate/final-review",
        "abc123",
        {"decision": "APPROVE_MERGE", "blocking": True},
    )
    assert blocked["conclusion"] == "action_required"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", nargs="?", help="Final gate JSON file. Defaults to stdin.")
    parser.add_argument("--name", default="ai-gate/final-review", help="GitHub check name.")
    parser.add_argument("--head-sha", required=False, help="Commit SHA for the check run.")
    parser.add_argument("--self-test", action="store_true", help="Run built-in tests.")
    args = parser.parse_args()

    if args.self_test:
        run_self_test()
        print("github_check_payload self-test passed")
        return 0

    if not args.head_sha:
        print("--head-sha is required unless --self-test is used", file=sys.stderr)
        return 2

    try:
        gate = read_gate(args.path)
        payload = build_check_payload(args.name, args.head_sha, gate)
    except (json.JSONDecodeError, ValueError) as exc:
        print(f"Invalid gate result: {exc}", file=sys.stderr)
        return 3

    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if payload["conclusion"] == "success" else 1


if __name__ == "__main__":
    raise SystemExit(main())

