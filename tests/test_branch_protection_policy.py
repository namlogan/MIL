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

    def test_solo_pilot_accepts_zero_reviews_when_required_checks_exist(self) -> None:
        result = self.policy.evaluate_branch_protection(
            {
                "required_status_checks": {
                    "strict": True,
                    "contexts": ["control-plane", "ai-gate/final-review"],
                },
                "required_pull_request_reviews": {"required_approving_review_count": 0},
            },
            solo_pilot=True,
        )

        self.assertTrue(result["ok"])
        self.assertIn("solo-owner pilot", result["warnings"][0])

    def test_team_mode_requires_at_least_one_review(self) -> None:
        result = self.policy.evaluate_branch_protection(
            {
                "required_status_checks": {
                    "strict": True,
                    "contexts": ["control-plane", "ai-gate/final-review"],
                },
                "required_pull_request_reviews": {"required_approving_review_count": 0},
            },
            solo_pilot=False,
        )

        self.assertFalse(result["ok"])
        self.assertIn("team mode requires at least one approving review", result["errors"])


if __name__ == "__main__":
    unittest.main()
