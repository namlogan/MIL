#!/usr/bin/env python3
"""Run the MIL repo-local flow sequence against a task JSON."""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any


FLOW_SEQUENCE = (
    "issue_to_plan",
    "plan_to_pr",
    "pr_quality_gate",
    "fix_ci_or_review",
)


def _load_mil_flow():
    module_path = Path(__file__).with_name("mil_flow.py")
    spec = importlib.util.spec_from_file_location("mil_flow", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {module_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run_sequence(task_path: str | Path) -> dict[str, Any]:
    mil_flow = _load_mil_flow()
    task = mil_flow.load_task(task_path)
    flows: list[dict[str, Any]] = []
    blocking = False

    for flow in FLOW_SEQUENCE:
        result = mil_flow.run_flow(flow, task)
        payload = result.to_dict()
        flows.append(payload)
        blocking = blocking or bool(payload["blocking"])
        if blocking:
            break

    return {
        "task_id": str(task["task_id"]),
        "blocking": blocking,
        "flows": flows,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task", required=True, help="Path to task JSON.")
    parser.add_argument("--out", help="Optional path for JSON artifact output.")
    args = parser.parse_args(argv)

    try:
        payload = run_sequence(args.task)
    except (json.JSONDecodeError, ValueError, RuntimeError) as exc:
        print(f"Flow sequence failed: {exc}", file=sys.stderr)
        return 2

    output = json.dumps(payload, indent=2, sort_keys=True)
    if args.out:
        out_path = Path(args.out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(output + "\n", encoding="utf-8")
    else:
        print(output)

    return 1 if payload["blocking"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
