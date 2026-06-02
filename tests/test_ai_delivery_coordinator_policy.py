from __future__ import annotations

import json
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


class AIDeliveryCoordinatorPolicyTests(unittest.TestCase):
    def test_runtime_agents_define_delivery_coordinator_without_code_or_merge_power(self) -> None:
        agents = json.loads((REPO_ROOT / ".ai-factory/runtime/agents.json").read_text(encoding="utf-8"))
        coordinator = agents["agents"]["ai_delivery_coordinator"]

        self.assertEqual(coordinator["role"], "routine_delivery_coordinator")
        self.assertIn("label_auto_dispatch_ready_issue", coordinator["allowed_actions"])
        self.assertIn("label_automerge_candidate_pr", coordinator["allowed_actions"])
        self.assertIn("author_app_code", coordinator["forbidden_actions"])
        self.assertIn("merge_main", coordinator["forbidden_actions"])
        self.assertIn("approve_restricted_change", coordinator["forbidden_actions"])

    def test_default_workflow_uses_coordinator_before_owner_escalation(self) -> None:
        workflows = json.loads(
            (REPO_ROOT / ".ai-factory/runtime/workflows.json").read_text(encoding="utf-8")
        )
        workflow = workflows["workflows"]["default_issue_to_merge"]

        self.assertEqual(workflow["routine_coordinator"], "ai_delivery_coordinator")
        self.assertEqual(
            workflow["routine_auto_labels"],
            ["agent:auto-build", "automerge:candidate"],
        )
        self.assertIn("restricted_changes", workflow["human_escalation_only_for"])
        self.assertIn("production_release", workflow["human_escalation_only_for"])

    def test_docs_say_routine_prs_do_not_need_owner_review(self) -> None:
        doc = (REPO_ROOT / "docs/ai-delivery-coordinator.md").read_text(encoding="utf-8")

        self.assertIn("Routine PRs do not ask the owner for manual review", doc)
        self.assertIn("restricted changes", doc)
        self.assertIn("production release", doc)


if __name__ == "__main__":
    unittest.main()
