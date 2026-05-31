#!/usr/bin/env python3
"""Validate the repo-local MIL AI Factory runtime install."""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import Any


RUNTIME_FILES = {
    "agents": ".ai-factory/runtime/agents.json",
    "workflows": ".ai-factory/runtime/workflows.json",
    "evidence": ".ai-factory/runtime/evidence.json",
    "environment": ".ai-factory/runtime/environment.json",
}

REQUIRED_AGENT_IDS = {
    "codex_developer",
    "codex_qa",
    "augment_context_provider",
    "auggie_advisory",
    "mem0_memory",
    "windmill_orchestrator",
    "github_merge_gate",
}

REQUIRED_DEFAULT_STAGES = [
    "issue_to_plan",
    "plan_to_pr",
    "control_plane_ci",
    "augment_context_review",
    "codex_qa_gate",
    "protected_merge",
]

REQUIRED_STATUS_CONTEXTS = {"control-plane", "ai-gate/final-review"}


def _read_json(repo_root: Path, relative_path: str) -> tuple[dict[str, Any] | None, str | None]:
    path = repo_root / relative_path
    if not path.exists():
        return None, f"missing runtime file: {relative_path}"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return None, f"invalid JSON in {relative_path}: {exc}"
    if not isinstance(data, dict):
        return None, f"{relative_path} must contain a JSON object"
    return data, None


def _require_list(value: Any, label: str, errors: list[str]) -> list[Any]:
    if not isinstance(value, list):
        errors.append(f"{label} must be a list")
        return []
    return value


def _validate_agents(agents: dict[str, Any], errors: list[str]) -> None:
    configured = agents.get("agents")
    if not isinstance(configured, dict):
        errors.append("agents.json missing agents object")
        return

    missing = sorted(REQUIRED_AGENT_IDS - set(configured))
    if missing:
        errors.append(f"agents.json missing agents: {', '.join(missing)}")

    for agent_id, spec in configured.items():
        if not isinstance(spec, dict):
            errors.append(f"agent {agent_id} must be an object")
            continue
        for field in ["role", "allowed_actions", "forbidden_actions"]:
            if field not in spec:
                errors.append(f"agent {agent_id} missing {field}")
        _require_list(spec.get("allowed_actions"), f"agent {agent_id}.allowed_actions", errors)
        _require_list(spec.get("forbidden_actions"), f"agent {agent_id}.forbidden_actions", errors)

    memory = configured.get("mem0_memory")
    if isinstance(memory, dict):
        if memory.get("runtime") != "mem0_optional":
            errors.append("mem0_memory.runtime must be mem0_optional")
        if memory.get("requires_sanitization") is not True:
            errors.append("mem0_memory must require sanitization")
        if memory.get("writes_code") is not False:
            errors.append("mem0_memory must not write code")
        forbidden = set(
            _require_list(
                memory.get("forbidden_actions"),
                "agent mem0_memory.forbidden_actions",
                errors,
            )
        )
        for action in ["implement_scoped_issue", "final_merge_approval", "merge_main"]:
            if action not in forbidden:
                errors.append(f"mem0_memory must forbid {action}")


def _validate_workflows(workflows: dict[str, Any], errors: list[str]) -> None:
    configured = workflows.get("workflows")
    if not isinstance(configured, dict):
        errors.append("workflows.json missing workflows object")
        return

    default = configured.get("default_issue_to_merge")
    if not isinstance(default, dict):
        errors.append("workflows.json missing default_issue_to_merge")
        return

    stages = _require_list(default.get("stages"), "default_issue_to_merge.stages", errors)
    if default.get("memory_provider") != "mem0_memory":
        errors.append("default_issue_to_merge.memory_provider must be mem0_memory")
    memory_checkpoints = set(
        _require_list(
            default.get("memory_checkpoints"),
            "default_issue_to_merge.memory_checkpoints",
            errors,
        )
    )
    if "issue_to_plan" not in memory_checkpoints or "codex_qa_gate" not in memory_checkpoints:
        errors.append("default_issue_to_merge must define memory checkpoints")
    stage_names = [stage.get("name") for stage in stages if isinstance(stage, dict)]
    if stage_names != REQUIRED_DEFAULT_STAGES:
        errors.append(
            "default_issue_to_merge stages must be: "
            + ", ".join(REQUIRED_DEFAULT_STAGES)
        )

    plan_to_pr = next(
        (stage for stage in stages if isinstance(stage, dict) and stage.get("name") == "plan_to_pr"),
        {},
    )
    if plan_to_pr.get("must_dispatch_exactly_one_coding_agent") is not True:
        errors.append("plan_to_pr must dispatch exactly one coding agent")

    protected_merge = next(
        (stage for stage in stages if isinstance(stage, dict) and stage.get("name") == "protected_merge"),
        {},
    )
    contexts = set(
        _require_list(
            protected_merge.get("requires_status_contexts"),
            "protected_merge.requires_status_contexts",
            errors,
        )
    )
    if not REQUIRED_STATUS_CONTEXTS.issubset(contexts):
        errors.append("protected_merge must require control-plane and ai-gate/final-review")


def _validate_evidence(evidence: dict[str, Any], errors: list[str]) -> None:
    configured = evidence.get("required_evidence")
    if not isinstance(configured, dict):
        errors.append("evidence.json missing required_evidence object")
        return
    for section in ["issue_intake", "developer_handoff", "qa_gate", "memory_record", "merge_gate"]:
        values = _require_list(configured.get(section), f"required_evidence.{section}", errors)
        if not values:
            errors.append(f"required_evidence.{section} must not be empty")


def _validate_environment(
    environment: dict[str, Any],
    errors: list[str],
    check_tools: bool,
    tool_resolver: Any,
) -> None:
    tools = _require_list(environment.get("required_tools"), "environment.required_tools", errors)
    if check_tools:
        missing_tools = [
            tool for tool in tools if isinstance(tool, str) and tool_resolver(tool) is None
        ]
        if missing_tools:
            errors.append(f"missing local tools: {', '.join(missing_tools)}")

    contexts = set(
        _require_list(
            environment.get("required_github_contexts"),
            "environment.required_github_contexts",
            errors,
        )
    )
    if not REQUIRED_STATUS_CONTEXTS.issubset(contexts):
        errors.append("environment must require control-plane and ai-gate/final-review")

    windmill = environment.get("windmill")
    if not isinstance(windmill, dict):
        errors.append("environment.windmill must be an object")
        return
    scripts = set(
        _require_list(windmill.get("required_scripts"), "environment.windmill.required_scripts", errors)
    )
    if "f/mil/github_commit_status" not in scripts:
        errors.append("environment.windmill.required_scripts missing f/mil/github_commit_status")
    for script in ["f/mil/memory_contract", "f/mil/mem0_retrieve", "f/mil/mem0_writeback"]:
        if script not in scripts:
            errors.append(f"environment.windmill.required_scripts missing {script}")
    if windmill.get("scoped_sync_include") != "f/mil/**":
        errors.append("environment.windmill.scoped_sync_include must be f/mil/**")

    memory = environment.get("memory")
    if not isinstance(memory, dict):
        errors.append("environment.memory must be an object")
        return
    if memory.get("provider") != "mem0_optional":
        errors.append("environment.memory.provider must be mem0_optional")
    if memory.get("runtime_agent") != "mem0_memory":
        errors.append("environment.memory.runtime_agent must be mem0_memory")
    if memory.get("must_sanitize_before_write") is not True:
        errors.append("environment.memory must sanitize before write")
    if memory.get("store_secrets") is not False:
        errors.append("environment.memory.store_secrets must be false")
    if not memory.get("local_fallback_store"):
        errors.append("environment.memory.local_fallback_store is required")
    if memory.get("windmill_retrieve_script") != "f/mil/mem0_retrieve":
        errors.append("environment.memory.windmill_retrieve_script must be f/mil/mem0_retrieve")
    if memory.get("windmill_writeback_script") != "f/mil/mem0_writeback":
        errors.append("environment.memory.windmill_writeback_script must be f/mil/mem0_writeback")
    required_metadata = set(
        _require_list(
            memory.get("required_metadata_fields"),
            "environment.memory.required_metadata_fields",
            errors,
        )
    )
    for field in ["tenant_id", "repo_id", "source_uri", "confidence", "status", "visibility"]:
        if field not in required_metadata:
            errors.append(f"environment.memory.required_metadata_fields missing {field}")
    entity_fields = set(
        _require_list(
            memory.get("required_entity_scope_fields_any_of"),
            "environment.memory.required_entity_scope_fields_any_of",
            errors,
        )
    )
    if not {"user_id", "agent_id", "run_id"}.issubset(entity_fields):
        errors.append("environment.memory must define Mem0 entity scope fields")


def validate(
    repo_root: Path,
    check_tools: bool = False,
    tool_resolver: Any = shutil.which,
) -> list[str]:
    errors: list[str] = []
    loaded: dict[str, dict[str, Any]] = {}

    for key, relative_path in RUNTIME_FILES.items():
        data, error = _read_json(repo_root, relative_path)
        if error:
            errors.append(error)
        elif data is not None:
            loaded[key] = data

    if "agents" in loaded:
        _validate_agents(loaded["agents"], errors)
    if "workflows" in loaded:
        _validate_workflows(loaded["workflows"], errors)
    if "evidence" in loaded:
        _validate_evidence(loaded["evidence"], errors)
    if "environment" in loaded:
        _validate_environment(loaded["environment"], errors, check_tools, tool_resolver)

    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", default=".", help="Repository root.")
    parser.add_argument("--check", action="store_true", help="Validate the runtime install.")
    parser.add_argument(
        "--check-tools",
        action="store_true",
        help="Also require local workstation tools such as wmill to be installed.",
    )
    args = parser.parse_args(argv)

    if not args.check:
        parser.error("--check is required")

    errors = validate(Path(args.repo).resolve(), check_tools=args.check_tools)
    if errors:
        print(json.dumps({"ok": False, "errors": errors}, indent=2), file=sys.stderr)
        return 1

    print("AI Factory runtime check passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
