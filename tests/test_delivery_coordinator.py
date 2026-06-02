from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def load_module(name: str, relative_path: str):
    module_path = REPO_ROOT / relative_path
    spec = importlib.util.spec_from_file_location(name, module_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def ready_issue(labels: list[str] | None = None) -> dict:
    return {
        "number": 101,
        "title": "MIL-101 Routine ready task",
        "labels": [{"name": label} for label in (labels or [])],
        "body": "\n".join(
            [
                "### Task ID",
                "MIL-101",
                "",
                "### User or business goal",
                "Ship a routine docs change.",
                "",
                "### Acceptance criteria",
                "- Change is documented.",
                "",
                "### Allowed files and out-of-scope files",
                "Allowed:",
                "- docs/**",
                "",
                "Out of scope:",
                "- secrets/**",
                "",
                "### Required checks",
                "- git diff --check",
                "",
                "### Restricted change check",
                "- [x] none of the above",
                "",
                "### Rollback note",
                "Revert the PR.",
                "",
                "### Memory preflight",
                "Query: project=MIL task=MIL-101",
            ]
        ),
    }


def clean_pr(labels: list[str] | None = None) -> dict:
    return {
        "number": 44,
        "isDraft": False,
        "baseRefName": "main",
        "headRefName": "agent/mil-101-routine-ready-task",
        "mergeStateStatus": "CLEAN",
        "reviewDecision": "",
        "additions": 12,
        "deletions": 2,
        "labels": [{"name": label} for label in (labels or ["agent:auto-build"])],
        "files": [{"path": "docs/routine.md"}],
        "statusCheckRollup": {
            "contexts": {
                "nodes": [
                    {"context": "control-plane", "state": "SUCCESS"},
                    {"context": "ai-gate/final-review", "state": "SUCCESS"},
                    {"context": "merge-controller-policy", "state": "SUCCESS"},
                ]
            }
        },
        "body": "## Summary\nx\n## Evidence\nx\n## Restricted Change Check\nx\nRollback: revert.",
    }


class DeliveryCoordinatorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.coordinator = load_module(
            "delivery_coordinator",
            "scripts/agent-flow/delivery_coordinator.py",
        )

    def test_ready_routine_issue_gets_auto_dispatch_without_owner_review(self) -> None:
        decision = self.coordinator.coordinate_issue(ready_issue())

        self.assertEqual(decision["decision"], "ROUTINE_AUTO_DISPATCH")
        self.assertFalse(decision["human_required"])
        self.assertEqual(decision["labels_to_add"], ["agent:auto-build"])
        self.assertIn("definition_of_ready_present", decision["reasons"])

    def test_restricted_issue_escalates_to_owner_instead_of_dispatching(self) -> None:
        decision = self.coordinator.coordinate_issue(ready_issue(labels=["security-review"]))

        self.assertEqual(decision["decision"], "ESCALATE_HUMAN")
        self.assertTrue(decision["human_required"])
        self.assertEqual(decision["labels_to_add"], [])
        self.assertIn("restricted_or_block_label: security-review", decision["reasons"])

    def test_clean_routine_pr_gets_automerge_candidate_without_owner_review(self) -> None:
        decision = self.coordinator.coordinate_pr(clean_pr())

        self.assertEqual(decision["decision"], "ROUTINE_AUTOMERGE_CANDIDATE")
        self.assertFalse(decision["human_required"])
        self.assertEqual(decision["labels_to_add"], ["automerge:candidate"])
        self.assertEqual(decision["merge_policy_decision"], "AUTO_APPROVE_AND_MERGE")

    def test_restricted_pr_escalates_to_owner(self) -> None:
        decision = self.coordinator.coordinate_pr(clean_pr(labels=["restricted-change"]))

        self.assertEqual(decision["decision"], "ESCALATE_HUMAN")
        self.assertTrue(decision["human_required"])
        self.assertEqual(decision["labels_to_add"], [])
        self.assertIn(
            "restricted label requires owner approval: restricted-change",
            decision["reasons"],
        )


if __name__ == "__main__":
    unittest.main()
