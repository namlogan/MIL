#!/usr/bin/env python3
"""Coordinate routine MIL issue and PR progression without owner micromanagement."""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
MERGE_CONTROLLER_PATH = REPO_ROOT / "scripts" / "github" / "merge_controller.py"

ISSUE_DOR_MARKERS = [
    "### Task ID",
    "### User or business goal",
    "### Acceptance criteria",
    "### Allowed files and out-of-scope files",
    "### Required checks",
    "### Restricted change check",
    "### Rollback note",
    "### Memory preflight",
]
ROUTINE_ISSUE_LABEL = "agent:auto-build"
ROUTINE_PR_LABEL = "automerge:candidate"
HUMAN_BLOCK_LABELS = {
    "hold",
    "owner-review",
    "do-not-merge",
    "blocked",
    "security-review",
    "restricted-change",
    "production-deploy",
    "secrets",
    "customer-data",
    "auth-boundary",
    "destructive-migration",
    "legal-compliance",
    "safety-critical",
}


def _load_merge_controller():
    spec = importlib.util.spec_from_file_location("mil_merge_controller", MERGE_CONTROLLER_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load merge controller from {MERGE_CONTROLLER_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _label_names(item: dict[str, Any]) -> set[str]:
    labels = item.get("labels") or []
    names: set[str] = set()
    if isinstance(labels, dict):
        labels = labels.get("nodes") or []
    for label in labels:
        if isinstance(label, dict) and label.get("name"):
            names.add(str(label["name"]).strip())
        elif isinstance(label, str):
            names.add(label.strip())
    return {name for name in names if name}


def _missing_markers(body: str, markers: list[str]) -> list[str]:
    return [marker for marker in markers if marker not in body]


def _decision_payload(
    *,
    decision: str,
    human_required: bool,
    labels_to_add: list[str],
    reasons: list[str],
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload = {
        "decision": decision,
        "human_required": human_required,
        "labels_to_add": labels_to_add,
        "reasons": reasons,
    }
    if extra:
        payload.update(extra)
    return payload


def coordinate_issue(issue: dict[str, Any]) -> dict[str, Any]:
    labels = _label_names(issue)
    restricted = sorted(labels.intersection(HUMAN_BLOCK_LABELS))
    if restricted:
        return _decision_payload(
            decision="ESCALATE_HUMAN",
            human_required=True,
            labels_to_add=[],
            reasons=[f"restricted_or_block_label: {label}" for label in restricted],
        )

    body = str(issue.get("body") or "")
    missing = _missing_markers(body, ISSUE_DOR_MARKERS)
    if missing:
        return _decision_payload(
            decision="WAITING_FOR_DEFINITION_OF_READY",
            human_required=False,
            labels_to_add=[],
            reasons=[f"missing DoR marker: {marker}" for marker in missing],
        )

    labels_to_add = [] if ROUTINE_ISSUE_LABEL in labels else [ROUTINE_ISSUE_LABEL]
    return _decision_payload(
        decision="ROUTINE_AUTO_DISPATCH",
        human_required=False,
        labels_to_add=labels_to_add,
        reasons=["definition_of_ready_present", "no_restricted_labels"],
    )


def coordinate_pr(pr: dict[str, Any], config: dict[str, Any] | None = None) -> dict[str, Any]:
    merge_controller = _load_merge_controller()
    policy_config = config or merge_controller.default_config(REPO_ROOT)
    policy = merge_controller.evaluate_pr(
        pr,
        policy_config,
        check_required_contexts=True,
        check_merge_state=True,
    )

    labels = _label_names(pr)
    if policy.decision == "AUTO_APPROVE_AND_MERGE":
        labels_to_add = [] if ROUTINE_PR_LABEL in labels else [ROUTINE_PR_LABEL]
        return _decision_payload(
            decision="ROUTINE_AUTOMERGE_CANDIDATE",
            human_required=False,
            labels_to_add=labels_to_add,
            reasons=["merge_controller_policy_passed"],
            extra={
                "merge_policy_decision": policy.decision,
                "required_contexts": policy.required_contexts,
                "warnings": policy.warnings,
            },
        )

    if policy.decision == "WAITING_FOR_CHECKS":
        return _decision_payload(
            decision="WAIT_FOR_CHECKS",
            human_required=False,
            labels_to_add=[],
            reasons=policy.blockers,
            extra={"merge_policy_decision": policy.decision},
        )

    return _decision_payload(
        decision="ESCALATE_HUMAN",
        human_required=True,
        labels_to_add=[],
        reasons=policy.blockers,
        extra={
            "merge_policy_decision": policy.decision,
            "warnings": policy.warnings,
        },
    )


def run_self_test() -> None:
    issue = {
        "labels": [],
        "body": "\n".join(ISSUE_DOR_MARKERS),
    }
    issue_decision = coordinate_issue(issue)
    assert issue_decision["decision"] == "ROUTINE_AUTO_DISPATCH", issue_decision
    assert issue_decision["labels_to_add"] == [ROUTINE_ISSUE_LABEL], issue_decision

    restricted_issue = {**issue, "labels": [{"name": "security-review"}]}
    restricted_decision = coordinate_issue(restricted_issue)
    assert restricted_decision["decision"] == "ESCALATE_HUMAN", restricted_decision


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--issue-json")
    parser.add_argument("--pr-json")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args(argv)

    if args.self_test:
        run_self_test()
        print("delivery_coordinator self-test passed")
        return 0

    if args.issue_json:
        print(json.dumps(coordinate_issue(json.loads(Path(args.issue_json).read_text())), indent=2, sort_keys=True))
        return 0

    if args.pr_json:
        print(json.dumps(coordinate_pr(json.loads(Path(args.pr_json).read_text())), indent=2, sort_keys=True))
        return 0

    raise SystemExit("--issue-json, --pr-json, or --self-test is required")


if __name__ == "__main__":
    raise SystemExit(main())
