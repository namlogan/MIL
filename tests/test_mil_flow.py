from __future__ import annotations

import importlib.util
import json
import tempfile
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


mil_flow = load_module("mil_flow", "scripts/agent-flow/mil_flow.py")


class MilFlowTests(unittest.TestCase):
    def setUp(self) -> None:
        self.task = mil_flow.load_task(REPO_ROOT / "tests/fixtures/agent_task.json")

    def test_issue_to_plan_routes_to_codex_and_auggie(self) -> None:
        result = mil_flow.run_flow("issue_to_plan", self.task)

        calls = [(call.agent, call.action) for call in result.agent_calls]
        self.assertEqual(calls, [("codex", "plan"), ("auggie", "validate_plan")])
        self.assertEqual(result.decision, "PLAN_READY_FOR_APPROVAL")

    def test_plan_to_pr_routes_to_implementation_review_and_tests(self) -> None:
        result = mil_flow.run_flow("plan_to_pr", self.task)

        calls = [(call.agent, call.action) for call in result.agent_calls]
        self.assertEqual(
            calls,
            [
                ("codex", "implement"),
                ("codex", "test"),
                ("auggie", "review"),
            ],
        )
        self.assertEqual(result.decision, "PR_READY_FOR_GATE")

    def test_pr_quality_gate_routes_to_codex_qa_and_approves_clean_task(self) -> None:
        result = mil_flow.run_flow("pr_quality_gate", self.task)

        calls = [(call.agent, call.action) for call in result.agent_calls]
        self.assertEqual(calls, [("codex", "qa")])
        self.assertEqual(result.decision, "APPROVE_MERGE")
        self.assertFalse(result.blocking)

    def test_fix_ci_or_review_routes_to_auggie_before_codex_fix(self) -> None:
        result = mil_flow.run_flow("fix_ci_or_review", self.task)

        calls = [(call.agent, call.action) for call in result.agent_calls]
        self.assertEqual(calls, [("auggie", "diagnose"), ("codex", "fix")])
        self.assertEqual(result.decision, "FIX_PUSH_READY")

    def test_cli_writes_flow_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            out_path = Path(tmpdir) / "artifact.json"
            exit_code = mil_flow.main(
                [
                    "--flow",
                    "pr_quality_gate",
                    "--task",
                    str(REPO_ROOT / "tests/fixtures/agent_task.json"),
                    "--out",
                    str(out_path),
                ]
            )

            self.assertEqual(exit_code, 0)
            artifact = json.loads(out_path.read_text(encoding="utf-8"))
            self.assertEqual(artifact["flow"], "pr_quality_gate")
            self.assertEqual(artifact["decision"], "APPROVE_MERGE")
            self.assertEqual(artifact["agent_calls"][0]["agent"], "codex")
            self.assertIn("aif_gate_result", artifact["artifacts"])


if __name__ == "__main__":
    unittest.main()

