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


class ReleaseGateTests(unittest.TestCase):
    def setUp(self) -> None:
        self.release_gate = load_module("release_gate", "scripts/release/release_gate.py")

    def test_release_template_is_versioned(self) -> None:
        self.assertTrue((REPO_ROOT / "docs/templates/release/RELEASE_CHECKLIST.md").exists())

    def test_release_gate_approves_complete_release_evidence(self) -> None:
        result = self.release_gate.evaluate_release_evidence(
            {
                "release_id": "2026-06-01-demo",
                "source_pr": "https://github.com/namlogan/MIL/pull/1",
                "target_environment": "staging",
                "ci_status": "passed",
                "ai_gate_status": "passed",
                "staging_smoke": "passed",
                "rollback_plan": "Revert merge commit and restore previous Windmill variables.",
                "human_approval": "PM_Logan approved in PR comment.",
                "monitoring_plan": "Watch GitHub Actions and Windmill jobs for 30 minutes.",
            }
        )

        self.assertEqual(result["decision"], "RELEASE_APPROVED")
        self.assertTrue(result["ok"])

    def test_release_gate_blocks_without_smoke_and_rollback(self) -> None:
        result = self.release_gate.evaluate_release_evidence(
            {
                "release_id": "2026-06-01-demo",
                "source_pr": "https://github.com/namlogan/MIL/pull/1",
                "target_environment": "production",
                "ci_status": "passed",
                "ai_gate_status": "passed",
                "human_approval": "PM_Logan approved in PR comment.",
            }
        )

        self.assertEqual(result["decision"], "RELEASE_BLOCKED")
        self.assertFalse(result["ok"])
        self.assertIn("staging_smoke", result["missing"])
        self.assertIn("rollback_plan", result["missing"])


if __name__ == "__main__":
    unittest.main()
