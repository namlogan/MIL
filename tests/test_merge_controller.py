from __future__ import annotations

import importlib.util
import io
import unittest
from contextlib import redirect_stdout
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


class MergeControllerPolicyTests(unittest.TestCase):
    def setUp(self) -> None:
        self.merge_controller = load_module(
            "merge_controller",
            "scripts/github/merge_controller.py",
        )
        self.config = self.merge_controller.default_config()

    def _pr(self, **overrides):
        pr = {
            "number": 12,
            "isDraft": False,
            "baseRefName": "main",
            "headRefName": "codex/update-docs",
            "mergeStateStatus": "CLEAN",
            "reviewDecision": "REVIEW_REQUIRED",
            "additions": 40,
            "deletions": 3,
            "labels": {"nodes": [{"name": "agent:auto-build"}]},
            "statusCheckRollup": {
                "contexts": {
                    "nodes": [
                        {"context": "control-plane", "state": "SUCCESS"},
                        {"context": "ai-gate/final-review", "state": "SUCCESS"},
                        {"context": "merge-controller-policy", "state": "SUCCESS"},
                    ]
                }
            },
            "files": [
                {"path": "docs/project/PRD.md"},
                {"path": "tests/test_project_intake.py"},
            ],
            "body": (
                "## Summary\nUpdate docs.\n\n"
                "## Evidence\n- tests\n\n"
                "## Restricted Change Check\nNo restricted changes.\n\n"
                "Rollback: revert the PR."
            ),
        }
        pr.update(overrides)
        return pr

    def test_low_risk_pr_can_be_auto_approved_and_merged(self) -> None:
        result = self.merge_controller.evaluate_pr(self._pr(), self.config)

        self.assertEqual(result.decision, "AUTO_APPROVE_AND_MERGE")
        self.assertEqual(result.blockers, [])

    def test_review_required_merge_state_still_allows_bot_approval(self) -> None:
        result = self.merge_controller.evaluate_pr(
            self._pr(mergeStateStatus="BLOCKED", reviewDecision="REVIEW_REQUIRED"),
            self.config,
        )

        self.assertEqual(result.decision, "AUTO_APPROVE_AND_MERGE")
        self.assertEqual(result.blockers, [])

    def test_missing_required_check_waits_instead_of_approving(self) -> None:
        result = self.merge_controller.evaluate_pr(
            self._pr(
                statusCheckRollup={
                    "contexts": {
                        "nodes": [
                            {"context": "control-plane", "state": "SUCCESS"},
                            {"context": "ai-gate/final-review", "state": "PENDING"},
                            {"context": "merge-controller-policy", "state": "SUCCESS"},
                        ]
                    }
                }
            ),
            self.config,
        )

        self.assertEqual(result.decision, "WAITING_FOR_CHECKS")
        self.assertIn("ai-gate/final-review is PENDING", result.blockers)

    def test_owner_hold_label_blocks_automation(self) -> None:
        result = self.merge_controller.evaluate_pr(
            self._pr(labels={"nodes": [{"name": "hold"}]}),
            self.config,
        )

        self.assertEqual(result.decision, "BLOCKED")
        self.assertIn("blocked by label: hold", result.blockers)

    def test_app_code_requires_explicit_auto_merge_label(self) -> None:
        result = self.merge_controller.evaluate_pr(
            self._pr(
                headRefName="agent/add-feature",
                labels={"nodes": []},
                files=[{"path": "apps/web/src/App.tsx"}],
            ),
            self.config,
        )

        self.assertEqual(result.decision, "NEEDS_OWNER_APPROVAL")
        self.assertIn("app-code PR requires an allow label", result.blockers)

    def test_restricted_path_requires_owner_approval_label(self) -> None:
        result = self.merge_controller.evaluate_pr(
            self._pr(
                labels={"nodes": [{"name": "agent:auto-build"}]},
                files=[{"path": ".github/workflows/ci.yml"}],
            ),
            self.config,
        )

        self.assertEqual(result.decision, "NEEDS_OWNER_APPROVAL")
        self.assertIn("restricted path changed: .github/workflows/ci.yml", result.blockers)

    def test_owner_approval_label_allows_restricted_path_with_warning(self) -> None:
        result = self.merge_controller.evaluate_pr(
            self._pr(
                labels={"nodes": [{"name": "owner:auto-approve"}]},
                files=[{"path": ".github/workflows/ci.yml"}],
            ),
            self.config,
        )

        self.assertEqual(result.decision, "AUTO_APPROVE_AND_MERGE")
        self.assertEqual(result.blockers, [])
        self.assertIn("restricted path changed: .github/workflows/ci.yml", result.warnings)

    def test_owner_approval_label_from_gh_list_shape_is_recognized(self) -> None:
        result = self.merge_controller.evaluate_pr(
            self._pr(
                labels=[
                    {
                        "id": "LA_1",
                        "name": "owner:auto-approve",
                        "description": "Owner explicitly approved restricted auto-merge risk",
                        "color": "0E8A16",
                    }
                ],
                files=[{"path": ".github/workflows/ci.yml"}],
            ),
            self.config,
        )

        self.assertEqual(result.decision, "AUTO_APPROVE_AND_MERGE")
        self.assertIn("owner:auto-approve", result.labels)

    def test_policy_only_mode_does_not_wait_for_other_required_checks(self) -> None:
        result = self.merge_controller.evaluate_pr(
            self._pr(
                statusCheckRollup={
                    "contexts": {
                        "nodes": [
                            {"context": "control-plane", "state": "PENDING"},
                            {"context": "ai-gate/final-review", "state": "PENDING"},
                            {"context": "merge-controller-policy", "state": "PENDING"},
                        ]
                    }
                },
                mergeStateStatus="UNKNOWN",
            ),
            self.config,
            check_required_contexts=False,
            check_merge_state=False,
        )

        self.assertEqual(result.decision, "AUTO_APPROVE_AND_MERGE")

    def test_same_actor_for_pusher_and_reviewer_is_rejected(self) -> None:
        result = self.merge_controller.evaluate_pr(
            self._pr(author={"login": "mil-agent-bot"}, latestPusher="mil-agent-bot"),
            {
                **self.config,
                "identities": {
                    "coding_bot": "mil-agent-bot",
                    "merge_bot": "mil-agent-bot",
                    "owner": "namlogan",
                },
            },
        )

        self.assertEqual(result.decision, "BLOCKED")
        self.assertIn("merge bot must be separate from latest pusher", result.blockers)

    def test_scan_open_with_no_prs_exits_zero(self) -> None:
        original = self.merge_controller._open_pr_numbers
        self.merge_controller._open_pr_numbers = lambda repo: []
        try:
            output = io.StringIO()
            with redirect_stdout(output):
                exit_code = self.merge_controller.main(["--repo", "namlogan/MIL", "--scan-open"])
        finally:
            self.merge_controller._open_pr_numbers = original

        self.assertEqual(exit_code, 0)
        self.assertIn('"open_prs": []', output.getvalue())


if __name__ == "__main__":
    unittest.main()
