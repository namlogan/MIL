#!/usr/bin/env python3
"""Bridge Windmill script inputs to the repo-local MIL AI Factory contract."""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _load_mil_flow():
    module_path = repo_root() / "scripts" / "agent-flow" / "mil_flow.py"
    spec = importlib.util.spec_from_file_location("mil_flow", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {module_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _normalize_task(task: dict[str, Any] | str) -> dict[str, Any]:
    if isinstance(task, str):
        data = json.loads(task)
    else:
        data = task
    if not isinstance(data, dict):
        raise ValueError("task must be a JSON object")
    if not data.get("task_id"):
        raise ValueError("task requires task_id")
    return data


def run_windmill_flow(flow: str, task: dict[str, Any] | str) -> dict[str, Any]:
    mil_flow = _load_mil_flow()
    normalized = _normalize_task(task)
    return mil_flow.run_flow(flow, normalized).to_dict()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--flow", required=True)
    parser.add_argument("--task-json", required=True)
    args = parser.parse_args(argv)

    try:
        result = run_windmill_flow(args.flow, args.task_json)
    except (json.JSONDecodeError, RuntimeError, ValueError) as exc:
        print(f"Windmill bridge failed: {exc}", file=sys.stderr)
        return 2

    print(json.dumps(result, indent=2, sort_keys=True))
    return 1 if result.get("blocking") else 0


if __name__ == "__main__":
    raise SystemExit(main())
