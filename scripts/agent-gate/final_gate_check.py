#!/usr/bin/env python3
"""Evaluate a parsed AI gate result and emit a final merge decision."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


APPROVE_VALUES = {"APPROVE_MERGE", "PASS", "PASSED", "APPROVED"}
REQUEST_CHANGES_VALUES = {"REQUEST_CHANGES", "CHANGES_REQUESTED", "FAIL", "FAILED"}
REJECT_VALUES = {"REJECT", "REJECTED"}
BLOCK_VALUES = {"BLOCKED", "BLOCKED_NEEDS_HUMAN", "NEEDS_HUMAN"}


def normalize_decision(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip().upper()


def evaluate_gate(gate: dict[str, Any]) -> dict[str, Any]:
    reasons = list(gate.get("reasons") or [])
    decision_value = normalize_decision(
        gate.get("decision") or gate.get("verdict") or gate.get("status")
    )
    blocking = bool(gate.get("blocking", False))

    if blocking:
        return {
            "decision": "BLOCKED_NEEDS_HUMAN",
            "pass": False,
            "reasons": reasons or ["gate result is blocking"],
        }

    if decision_value in APPROVE_VALUES:
        return {
            "decision": "APPROVE_MERGE",
            "pass": True,
            "reasons": reasons,
        }

    if decision_value in REQUEST_CHANGES_VALUES:
        return {
            "decision": "REQUEST_CHANGES",
            "pass": False,
            "reasons": reasons or ["gate requested changes"],
        }

    if decision_value in REJECT_VALUES:
        return {
            "decision": "REJECT",
            "pass": False,
            "reasons": reasons or ["gate rejected the change"],
        }

    if decision_value in BLOCK_VALUES:
        return {
            "decision": "BLOCKED_NEEDS_HUMAN",
            "pass": False,
            "reasons": reasons or ["gate needs human review"],
        }

    return {
        "decision": "BLOCKED_NEEDS_HUMAN",
        "pass": False,
        "reasons": reasons or [f"unknown or missing decision: {decision_value or '<empty>'}"],
    }


def read_gate(path: str | None) -> dict[str, Any]:
    raw = Path(path).read_text(encoding="utf-8") if path else sys.stdin.read()
    data = json.loads(raw)
    if not isinstance(data, dict):
        raise ValueError("gate result must be a JSON object")
    return data


def run_self_test() -> None:
    assert evaluate_gate({"decision": "APPROVE_MERGE", "blocking": False})["pass"]
    assert not evaluate_gate({"decision": "APPROVE_MERGE", "blocking": True})["pass"]
    assert evaluate_gate({"decision": "REQUEST_CHANGES"})["decision"] == "REQUEST_CHANGES"
    assert evaluate_gate({})["decision"] == "BLOCKED_NEEDS_HUMAN"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", nargs="?", help="Parsed gate JSON file. Defaults to stdin.")
    parser.add_argument("--self-test", action="store_true", help="Run built-in tests.")
    args = parser.parse_args()

    if args.self_test:
        run_self_test()
        print("final_gate_check self-test passed")
        return 0

    try:
        gate = read_gate(args.path)
        result = evaluate_gate(gate)
    except (json.JSONDecodeError, ValueError) as exc:
        print(f"Invalid gate result: {exc}", file=sys.stderr)
        return 3

    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

