#!/usr/bin/env python3
"""Validate MIL Windmill project files without requiring workspace credentials."""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any


FLOW_NAMES = (
    "flow_contract",
    "issue_to_plan",
    "plan_to_pr",
    "pr_quality_gate",
    "fix_ci_or_review",
    "auggie_supervised_advisory",
    "github_commit_status",
    "github_webhook_router",
)


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


def validate(repo_root: Path) -> list[str]:
    errors: list[str] = []
    wmill_yaml = repo_root / "wmill.yaml"
    lock = repo_root / "wmill-lock.yaml"

    if not wmill_yaml.exists():
        errors.append("missing wmill.yaml")
    else:
        config = wmill_yaml.read_text(encoding="utf-8")
        for required in ['"f/**"', "skipSecrets: true", "nonDottedPaths: true"]:
            if required not in config:
                errors.append(f"wmill.yaml missing {required}")

    if not lock.exists():
        errors.append("missing wmill-lock.yaml")

    for name in FLOW_NAMES:
        script = repo_root / "f" / "mil" / f"{name}.py"
        metadata = repo_root / "f" / "mil" / f"{name}.script.yaml"
        if not script.exists():
            errors.append(f"missing Windmill script: f/mil/{name}.py")
        if not metadata.exists():
            errors.append(f"missing Windmill metadata: f/mil/{name}.script.yaml")
        elif "kind: script" not in metadata.read_text(encoding="utf-8"):
            errors.append(f"metadata is not script kind: f/mil/{name}.script.yaml")

    try:
        contract = _load_module(
            "windmill_flow_contract",
            repo_root / "f" / "mil" / "flow_contract.py",
        )
        mil_flow = _load_module(
            "mil_flow",
            repo_root / "scripts" / "agent-flow" / "mil_flow.py",
        )
        task = _load_json(repo_root / "tests" / "fixtures" / "agent_task.json")
        for flow in FLOW_NAMES:
            if flow in {
                "flow_contract",
                "auggie_supervised_advisory",
                "github_commit_status",
                "github_webhook_router",
            }:
                continue
            expected = mil_flow.run_flow(flow, task).to_dict()
            observed = contract.run_flow(flow, task)
            if observed != expected:
                errors.append(f"Windmill contract drift for {flow}")
    except (OSError, RuntimeError, ValueError, json.JSONDecodeError) as exc:
        errors.append(f"contract validation failed: {exc}")

    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", default=".")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args(argv)

    errors = validate(Path(args.repo).resolve())
    if errors:
        print(json.dumps({"ok": False, "errors": errors}, indent=2), file=sys.stderr)
        return 1
    print("Windmill project validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
