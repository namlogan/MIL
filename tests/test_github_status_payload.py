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


github_status_payload = load_module(
    "github_status_payload",
    "scripts/agent-gate/github_status_payload.py",
)


class GitHubStatusPayloadTests(unittest.TestCase):
    def test_approve_merge_maps_to_success_status(self) -> None:
        payload = github_status_payload.build_status_payload(
            gate={"decision": "APPROVE_MERGE", "pass": True},
            target_url="https://github.com/namlogan/MIL/pull/2",
        )

        self.assertEqual(payload["state"], "success")
        self.assertEqual(payload["context"], "ai-gate/final-review")
        self.assertIn("APPROVE_MERGE", payload["description"])

    def test_blocked_gate_maps_to_failure_status(self) -> None:
        payload = github_status_payload.build_status_payload(
            gate={"decision": "BLOCKED_NEEDS_HUMAN", "blocking": True},
            target_url="https://github.com/namlogan/MIL/pull/2",
        )

        self.assertEqual(payload["state"], "failure")
        self.assertIn("BLOCKED_NEEDS_HUMAN", payload["description"])


if __name__ == "__main__":
    unittest.main()

