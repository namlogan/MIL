"""Self-contained MIL flow contract for Windmill script execution."""

from __future__ import annotations

from typing import Any


FLOW_STEPS: dict[str, list[tuple[str, str]]] = {
    "issue_to_plan": [
        ("codex", "plan"),
        ("auggie", "validate_plan"),
    ],
    "plan_to_pr": [
        ("windmill", "dispatch_coding_agent"),
        ("developer", "create_branch"),
        ("developer", "implement"),
        ("developer", "test"),
        ("developer", "open_pr"),
        ("auggie", "review"),
    ],
    "pr_quality_gate": [
        ("codex", "qa"),
    ],
    "fix_ci_or_review": [
        ("auggie", "diagnose"),
        ("codex", "fix"),
    ],
}

ROLES = {
    "codex": "implementation_test_and_qa_worker",
    "auggie_supervised": "supervised_interactive_developer_worker",
    "auggie": "advisory_review_and_diagnosis_worker",
    "windmill": "cockpit_and_orchestrator",
}


def _developer_agent_for_task(task: dict[str, Any]) -> str:
    configured = str(task.get("developer_agent") or "codex").strip()
    if configured not in {"codex", "auggie_supervised"}:
        raise ValueError(f"unsupported developer_agent: {configured}")
    if configured == "auggie_supervised" and not task.get("allow_auggie_implementation"):
        raise ValueError(
            "developer_agent auggie_supervised requires allow_auggie_implementation=true"
        )
    return configured


def _decision_for_flow(flow: str, task: dict[str, Any]) -> tuple[str, bool]:
    if task.get("restricted_changes"):
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


def _agent_calls(flow: str, task: dict[str, Any], blocking: bool) -> list[dict[str, str]]:
    if blocking:
        return []

    calls: list[dict[str, str]] = []
    for agent, action in FLOW_STEPS[flow]:
        selected_agent = _developer_agent_for_task(task) if agent == "developer" else agent
        calls.append(
            {
                "agent": selected_agent,
                "action": action,
                "task_id": str(task["task_id"]),
                "role": ROLES[selected_agent],
            }
        )
    return calls


def _artifacts(flow: str, task: dict[str, Any], decision: str, blocking: bool) -> dict[str, Any]:
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
            "branch": f"agent/{task_id.lower()}",
            "requires_pull_request": True,
            "supervised": developer == "auggie_supervised",
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


def run_flow(flow: str, task: dict[str, Any]) -> dict[str, Any]:
    if flow not in FLOW_STEPS:
        raise ValueError(f"unknown flow: {flow}")
    if not isinstance(task, dict) or not task.get("task_id"):
        raise ValueError("task requires task_id")

    decision, blocking = _decision_for_flow(flow, task)
    return {
        "flow": flow,
        "task_id": str(task["task_id"]),
        "decision": decision,
        "blocking": blocking,
        "agent_calls": _agent_calls(flow, task, blocking),
        "artifacts": _artifacts(flow, task, decision, blocking),
    }


def run_auggie_supervised_advisory(target: dict[str, Any]) -> dict[str, Any]:
    task_id = str(target.get("task_id") or target.get("issue") or target.get("pr") or "UNKNOWN")
    return {
        "flow": "auggie_supervised_advisory",
        "task_id": task_id,
        "decision": "AUGMENT_REVIEW_QUEUED",
        "blocking": False,
        "agent_calls": [
            {
                "agent": "windmill",
                "action": "queue_auggie_supervised_advisory",
                "task_id": task_id,
                "role": ROLES["windmill"],
            }
        ],
        "artifacts": {
            "summary": f"auggie_supervised_advisory queued for {task_id}",
            "requires_operator": True,
            "runner": "scripts/agent-flow/auggie_interactive.sh",
            "allowed_verdicts": [
                "AUGMENT_REVIEW_PASS",
                "AUGMENT_REVIEW_NOTES",
                "AUGMENT_REVIEW_CHANGES_RECOMMENDED",
                "AUGMENT_REVIEW_BLOCKED",
            ],
        },
    }


def main(flow: str, task: dict[str, Any]) -> dict[str, Any]:
    """Generic Windmill script entrypoint for manual flow smoke runs."""

    return run_flow(flow, task)
