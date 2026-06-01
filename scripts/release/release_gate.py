#!/usr/bin/env python3
"""Evaluate release evidence before staging or production rollout."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


REQUIRED_FIELDS = [
    "release_id",
    "source_pr",
    "target_environment",
    "ci_status",
    "ai_gate_status",
    "staging_smoke",
    "rollback_plan",
    "human_approval",
    "monitoring_plan",
]

PASS_VALUES = {"passed", "pass", "success", "approved"}


def _missing(evidence: dict[str, Any]) -> list[str]:
    return [field for field in REQUIRED_FIELDS if not str(evidence.get(field, "")).strip()]


def evaluate_release_evidence(evidence: dict[str, Any]) -> dict[str, Any]:
    missing = _missing(evidence)
    errors: list[str] = []
    for status_field in ["ci_status", "ai_gate_status", "staging_smoke"]:
        value = str(evidence.get(status_field, "")).strip().lower()
        if value and value not in PASS_VALUES:
            errors.append(f"{status_field} must be passed before release")
    ok = not missing and not errors
    return {
        "ok": ok,
        "decision": "RELEASE_APPROVED" if ok else "RELEASE_BLOCKED",
        "missing": missing,
        "errors": errors,
        "required_fields": REQUIRED_FIELDS,
    }


def run_self_test() -> None:
    result = evaluate_release_evidence(
        {
            "release_id": "self-test",
            "source_pr": "https://github.com/namlogan/MIL/pull/1",
            "target_environment": "staging",
            "ci_status": "passed",
            "ai_gate_status": "passed",
            "staging_smoke": "passed",
            "rollback_plan": "Revert the merge commit.",
            "human_approval": "Owner approved.",
            "monitoring_plan": "Watch checks after rollout.",
        }
    )
    assert result["ok"], result
    blocked = evaluate_release_evidence({"release_id": "bad"})
    assert not blocked["ok"], blocked


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence", help="Path to release evidence JSON.")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args(argv)

    if args.self_test:
        run_self_test()
        print("release_gate self-test passed")
        return 0

    if not args.evidence:
        parser.error("--evidence is required unless --self-test is used")
    evidence = json.loads(Path(args.evidence).read_text(encoding="utf-8"))
    result = evaluate_release_evidence(evidence)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
