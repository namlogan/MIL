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


github_check_payload = load_module(
    "github_check_payload",
    "scripts/agent-gate/github_check_payload.py",
)


class GitHubCheckPayloadTests(unittest.TestCase):
    def test_approve_merge_maps_to_success_check(self) -> None:
        payload = github_check_payload.build_check_payload(
            name="ai-gate/final-review",
            head_sha="abc123",
            gate={
                "decision": "APPROVE_MERGE",
                "pass": True,
                "reasons": [],
                "residual_risks": [],
            },
        )

        self.assertEqual(payload["name"], "ai-gate/final-review")
        self.assertEqual(payload["head_sha"], "abc123")
        self.assertEqual(payload["status"], "completed")
        self.assertEqual(payload["conclusion"], "success")
        self.assertEqual(payload["output"]["title"], "APPROVE_MERGE")

    def test_blocked_gate_maps_to_action_required_check(self) -> None:
        payload = github_check_payload.build_check_payload(
            name="ai-gate/final-review",
            head_sha="abc123",
            gate={
                "decision": "BLOCKED_NEEDS_HUMAN",
                "pass": False,
                "reasons": ["restricted change needs approval"],
                "residual_risks": ["branch protection unavailable"],
            },
        )

        self.assertEqual(payload["conclusion"], "action_required")
        self.assertIn("restricted change needs approval", payload["output"]["summary"])
        self.assertIn("branch protection unavailable", payload["output"]["summary"])


if __name__ == "__main__":
    unittest.main()
