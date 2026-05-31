#!/usr/bin/env python3
"""Local executable contract for MIL agent factory flows.

This is a dry-run harness for the Windmill cockpit. It proves the routing,
artifacts, and gate decisions expected from each flow before real Windmill
workers and credentials are configured.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, NamedTuple


FLOW_STEPS: dict[str, list[tuple[str, str]]] = {
    "issue_to_plan": [
        ("augment_context", "provide_issue_context"),
        ("codex", "plan"),
    ],
    "plan_to_pr": [
        ("windmill", "dispatch_coding_agent"),
        ("developer", "create_branch"),
        ("developer", "implement"),
        ("developer", "test"),
        ("developer", "open_pr"),
        ("augment_context", "provide_review_context"),
    ],
    "pr_quality_gate": [
        ("augment_context", "provide_gate_context"),
        ("codex", "qa"),
    ],
    "fix_ci_or_review": [
        ("augment_context", "provide_ci_context"),
        ("codex", "fix"),
    ],
}


class AgentCall(NamedTuple):
    agent: str
    action: str
    task_id: str
    role: str

    def to_dict(self) -> dict[str, str]:
        return {
            "agent": self.agent,
            "action": self.action,
            "task_id": self.task_id,
            "role": self.role,
        }


class FlowResult(NamedTuple):
    flow: str
    task_id: str
    decision: str
    blocking: bool
    agent_calls: list[AgentCall]
    artifacts: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "flow": self.flow,
            "task_id": self.task_id,
            "decision": self.decision,
            "blocking": self.blocking,
            "agent_calls": [call.to_dict() for call in self.agent_calls],
            "artifacts": self.artifacts,
        }


class DryRunAgentAdapter:
    """Records intended agent calls without invoking external CLIs."""

    roles = {
        "codex": "implementation_test_and_qa_worker",
        "augment_context": "codebase_index_and_context_provider",
        "auggie": "supervised_advisory_context_reviewer",
        "windmill": "cockpit_and_orchestrator",
    }

    def __init__(self) -> None:
        self.calls: list[AgentCall] = []

    def call(self, agent: str, action: str, task: dict[str, Any]) -> AgentCall:
        if agent == "developer":
            agent = _developer_agent_for_task(task)
        if agent not in self.roles:
            raise ValueError(f"unknown agent: {agent}")
        task_id = str(task.get("task_id") or "UNKNOWN")
        call = AgentCall(
            agent=agent,
            action=action,
            task_id=task_id,
            role=self.roles[agent],
        )
        self.calls.append(call)
        return call


def load_task(path: str | Path) -> dict[str, Any]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("task fixture must be a JSON object")
    if not data.get("task_id"):
        raise ValueError("task fixture requires task_id")
    return data


def _has_restricted_changes(task: dict[str, Any]) -> bool:
    return bool(task.get("restricted_changes"))


def _developer_agent_for_task(task: dict[str, Any]) -> str:
    configured = str(task.get("developer_agent") or "codex").strip()
    if configured != "codex":
        raise ValueError(
            f"Codex is the only supported coding agent; got developer_agent={configured}"
        )
    return configured


def _decision_for_flow(flow: str, task: dict[str, Any]) -> tuple[str, bool]:
    if _has_restricted_changes(task):
        return "BLOCKED_NEEDS_HUMAN", True

    if flow == "issue_to_plan":
        return "PLAN_READY_FOR_APPROVAL", False
    if flow == "plan_to_pr":
        return "PR_READY_FOR_GATE", False
    if flow == "pr_quality_gate":
        return "APPROVE_MERGE", False
    if flow == "fix_ci_or_review":
        return "FIX_PUSH_READY", False
    raise ValueError(f"unknown flow: {flow}")


def _artifacts_for_flow(
    flow: str,
    task: dict[str, Any],
    decision: str,
    blocking: bool,
) -> dict[str, Any]:
    task_id = str(task["task_id"])
    artifacts: dict[str, Any] = {
        "summary": f"{flow} completed for {task_id}",
        "required_checks": task.get("checks", []),
    }

    if flow == "issue_to_plan":
        artifacts["plan"] = {
            "task_id": task_id,
            "goal": task.get("goal", ""),
            "acceptance_criteria": task.get("acceptance_criteria", []),
            "allowed_files": task.get("allowed_files", []),
        }

    if flow == "plan_to_pr" and not blocking:
        developer = _developer_agent_for_task(task)
        artifacts["dispatch"] = {
            "developer_agent": developer,
            "context_provider": "augment_context",
            "branch": f"agent/{task_id.lower()}",
            "requires_pull_request": True,
        }

    if flow == "pr_quality_gate":
        artifacts["aif_gate_result"] = {
            "decision": decision,
            "blocking": blocking,
            "reasons": [] if not blocking else ["restricted change requires human approval"],
            "tests": task.get("checks", []),
            "residual_risks": task.get("residual_risks", []),
        }

    return artifacts


def run_flow(
    flow: str,
    task: dict[str, Any],
    adapter: DryRunAgentAdapter | None = None,
) -> FlowResult:
    if flow not in FLOW_STEPS:
        raise ValueError(f"unknown flow: {flow}")

    decision, blocking = _decision_for_flow(flow, task)
    if blocking:
        return FlowResult(
            flow=flow,
            task_id=str(task["task_id"]),
            decision=decision,
            blocking=blocking,
            agent_calls=[],
            artifacts=_artifacts_for_flow(flow, task, decision, blocking),
        )

    agent_adapter = adapter or DryRunAgentAdapter()
    for agent, action in FLOW_STEPS[flow]:
        agent_adapter.call(agent, action, task)

    return FlowResult(
        flow=flow,
        task_id=str(task["task_id"]),
        decision=decision,
        blocking=blocking,
        agent_calls=agent_adapter.calls,
        artifacts=_artifacts_for_flow(flow, task, decision, blocking),
    )


def run_self_test() -> None:
    task = {
        "task_id": "SELF-TEST",
        "checks": ["python3 -m unittest discover -s tests -v"],
        "restricted_changes": [],
    }
    expected_calls = {
        "issue_to_plan": [("augment_context", "provide_issue_context"), ("codex", "plan")],
        "plan_to_pr": [
            ("windmill", "dispatch_coding_agent"),
            ("codex", "create_branch"),
            ("codex", "implement"),
            ("codex", "test"),
            ("codex", "open_pr"),
            ("augment_context", "provide_review_context"),
        ],
        "pr_quality_gate": [("augment_context", "provide_gate_context"), ("codex", "qa")],
        "fix_ci_or_review": [("augment_context", "provide_ci_context"), ("codex", "fix")],
    }

    for flow, expected in expected_calls.items():
        result = run_flow(flow, task)
        calls = [(call.agent, call.action) for call in result.agent_calls]
        assert calls == expected
        assert result.task_id == "SELF-TEST"

    gate_result = run_flow("pr_quality_gate", task)
    assert gate_result.decision == "APPROVE_MERGE"
    assert "aif_gate_result" in gate_result.artifacts


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--flow", choices=sorted(FLOW_STEPS), help="Flow to run.")
    parser.add_argument("--task", help="Path to task JSON.")
    parser.add_argument("--out", help="Optional path for JSON artifact output.")
    parser.add_argument("--self-test", action="store_true", help="Run built-in tests.")
    args = parser.parse_args(argv)

    if args.self_test:
        run_self_test()
        print("mil_flow self-test passed")
        return 0

    if not args.flow or not args.task:
        parser.error("--flow and --task are required unless --self-test is used")

    try:
        result = run_flow(args.flow, load_task(args.task))
    except (json.JSONDecodeError, ValueError) as exc:
        print(f"Flow failed: {exc}", file=sys.stderr)
        return 2

    payload = result.to_dict()
    output = json.dumps(payload, indent=2, sort_keys=True)
    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(output + "\n", encoding="utf-8")
    else:
        print(output)

    return 1 if result.blocking else 0


if __name__ == "__main__":
    raise SystemExit(main())
