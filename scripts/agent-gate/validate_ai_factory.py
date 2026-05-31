#!/usr/bin/env python3
"""Validate MIL AI Factory artifacts against the executable flow contract."""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any


FLOW_SAMPLE_FILES = {
    "issue_to_plan": ".ai-factory/gates/sample_issue_to_plan.json",
    "plan_to_pr": ".ai-factory/gates/sample_plan_to_pr.json",
    "pr_quality_gate": ".ai-factory/gates/sample_pr_quality_gate.json",
    "fix_ci_or_review": ".ai-factory/gates/sample_fix_ci_or_review.json",
}

REQUIRED_PATHS = [
    ".ai-factory/DESCRIPTION.md",
    ".ai-factory/ARCHITECTURE.md",
    ".ai-factory/RULES.md",
    ".ai-factory/rules",
    ".ai-factory/runtime/agents.json",
    ".ai-factory/runtime/workflows.json",
    ".ai-factory/runtime/evidence.json",
    ".ai-factory/runtime/environment.json",
    ".ai-factory/plans",
    ".ai-factory/qa",
    ".ai-factory/gates",
    ".windmill",
    "docs",
    "docs/ai-factory-setup.md",
    "scripts/ai-factory/bootstrap_runtime.py",
]

REQUIRED_CONTROLS = [
    "require_pull_request: true",
    "require_human_for_release: true",
    "require_human_for_restricted_changes: true",
    "require_coding_agent_dispatch: true",
    "max_auto_fix_iterations: 2",
    "runtime_check_command: python3 scripts/ai-factory/bootstrap_runtime.py --check",
    "ai-gate/final-review",
]

ALLOWED_GATE_DECISIONS = {
    "APPROVE_MERGE",
    "REQUEST_CHANGES",
    "REJECT",
    "BLOCKED_NEEDS_HUMAN",
}


def _load_module(repo_root: Path, name: str, relative_path: str):
    module_path = repo_root / relative_path
    spec = importlib.util.spec_from_file_location(name, module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {module_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _read_json(repo_root: Path, relative_path: str) -> dict[str, Any]:
    data = json.loads((repo_root / relative_path).read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{relative_path} must contain a JSON object")
    return data


def validate(repo_root: Path) -> list[str]:
    errors: list[str] = []
    config_path = repo_root / ".ai-factory/config.yaml"
    rules_path = repo_root / ".ai-factory/RULES.md"
    config = config_path.read_text(encoding="utf-8") if config_path.exists() else ""
    rules = rules_path.read_text(encoding="utf-8") if rules_path.exists() else ""

    for relative_path in REQUIRED_PATHS:
        if not (repo_root / relative_path).exists():
            errors.append(f"missing required path: {relative_path}")
        if relative_path not in config:
            errors.append(f"config.yaml does not reference: {relative_path}")

    for control in REQUIRED_CONTROLS:
        if control not in config:
            errors.append(f"config.yaml missing control: {control}")

    for decision in sorted(ALLOWED_GATE_DECISIONS):
        if decision not in rules:
            errors.append(f"RULES.md missing gate decision: {decision}")
        if decision not in config:
            errors.append(f"config.yaml missing gate decision: {decision}")

    try:
        mil_flow = _load_module(repo_root, "mil_flow", "scripts/agent-flow/mil_flow.py")
        final_gate_check = _load_module(
            repo_root,
            "final_gate_check",
            "scripts/agent-gate/final_gate_check.py",
        )
        bootstrap_runtime = _load_module(
            repo_root,
            "bootstrap_runtime",
            "scripts/ai-factory/bootstrap_runtime.py",
        )
        task = mil_flow.load_task(repo_root / "tests/fixtures/agent_task.json")

        runtime_errors = bootstrap_runtime.validate(repo_root)
        if runtime_errors:
            errors.extend(f"runtime install invalid: {error}" for error in runtime_errors)

        for flow, relative_path in FLOW_SAMPLE_FILES.items():
            sample = _read_json(repo_root, relative_path)
            expected = mil_flow.run_flow(flow, task).to_dict()
            if sample != expected:
                errors.append(f"{relative_path} does not match executable flow output")

        plan_to_pr = _read_json(repo_root, FLOW_SAMPLE_FILES["plan_to_pr"])
        calls = [
            f"{call['agent']}.{call['action']}"
            for call in plan_to_pr.get("agent_calls", [])
        ]
        if not calls or calls[0] != "windmill.dispatch_coding_agent":
            errors.append("sample_plan_to_pr must start with windmill.dispatch_coding_agent")
        elif "codex.implement" in calls and calls.index("windmill.dispatch_coding_agent") > calls.index("codex.implement"):
            errors.append("sample_plan_to_pr dispatch must occur before codex.implement")

        pr_quality_gate = _read_json(repo_root, FLOW_SAMPLE_FILES["pr_quality_gate"])
        gate = pr_quality_gate.get("artifacts", {}).get("aif_gate_result")
        if not isinstance(gate, dict):
            errors.append("sample_pr_quality_gate missing artifacts.aif_gate_result")
        else:
            gate_result = final_gate_check.evaluate_gate(gate)
            if gate_result.get("decision") != "APPROVE_MERGE" or not gate_result.get("pass"):
                errors.append("sample_pr_quality_gate is not accepted by final_gate_check")
    except (json.JSONDecodeError, OSError, RuntimeError, ValueError, KeyError) as exc:
        errors.append(f"validation failed: {exc}")

    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", default=".", help="Repository root to validate.")
    parser.add_argument("--self-test", action="store_true", help="Validate the current repo.")
    args = parser.parse_args(argv)

    repo_root = Path(args.repo).resolve()
    errors = validate(repo_root)
    if errors:
        print(json.dumps({"ok": False, "errors": errors}, indent=2), file=sys.stderr)
        return 1

    message = "validate_ai_factory self-test passed" if args.self_test else "AI Factory validation passed"
    print(message)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
