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


class BranchProtectionPolicyTests(unittest.TestCase):
    def setUp(self) -> None:
        self.policy = load_module(
            "check_branch_protection",
            "scripts/github/check_branch_protection.py",
        )

    def test_real_project_rejects_zero_reviews_when_required_checks_exist(self) -> None:
        result = self.policy.evaluate_branch_protection(
            {
                "required_status_checks": {
                    "strict": True,
                    "contexts": ["control-plane", "ai-gate/final-review"],
                },
                "required_pull_request_reviews": {"required_approving_review_count": 0},
            },
            allow_zero_reviews=False,
        )

        self.assertFalse(result["ok"])
        self.assertIn("zero required reviews require merge-controller-policy status check", result["errors"])

    def test_status_check_approval_mode_accepts_zero_reviews(self) -> None:
        result = self.policy.evaluate_branch_protection(
            {
                "required_status_checks": {
                    "strict": True,
                    "contexts": ["control-plane", "ai-gate/final-review", "merge-controller-policy"],
                },
                "required_pull_request_reviews": {"required_approving_review_count": 0},
            },
            allow_zero_reviews=False,
        )

        self.assertTrue(result["ok"])
        self.assertEqual(result["review_count"], 0)

    def test_explicit_override_accepts_zero_reviews_with_warning(self) -> None:
        result = self.policy.evaluate_branch_protection(
            {
                "required_status_checks": {
                    "strict": True,
                    "contexts": ["control-plane", "ai-gate/final-review", "merge-controller-policy"],
                },
                "required_pull_request_reviews": {"required_approving_review_count": 0},
            },
            allow_zero_reviews=True,
        )

        self.assertTrue(result["ok"])
        self.assertIn("zero required reviews accepted because merge-controller-policy is required", result["warnings"][0])

    def test_reviewed_branch_warns_without_codeowners_or_stale_dismissal(self) -> None:
        result = self.policy.evaluate_branch_protection(
            {
                "required_status_checks": {
                    "strict": True,
                    "contexts": ["control-plane", "ai-gate/final-review", "merge-controller-policy"],
                },
                "required_pull_request_reviews": {
                    "required_approving_review_count": 1,
                    "require_code_owner_reviews": False,
                    "dismiss_stale_reviews": False,
                    "require_last_push_approval": False,
                },
            },
            allow_zero_reviews=False,
        )

        self.assertTrue(result["ok"])
        self.assertIn("CODEOWNERS review is recommended", result["warnings"][0])
        self.assertIn(
            "last-push approval by a different actor is recommended",
            result["warnings"][-1],
        )


if __name__ == "__main__":
    unittest.main()
