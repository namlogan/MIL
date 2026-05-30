from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
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
final_gate_check = load_module(
    "final_gate_check",
    "scripts/agent-gate/final_gate_check.py",
)


FLOW_SAMPLE_FILES = {
    "issue_to_plan": ".ai-factory/gates/sample_issue_to_plan.json",
    "plan_to_pr": ".ai-factory/gates/sample_plan_to_pr.json",
    "pr_quality_gate": ".ai-factory/gates/sample_pr_quality_gate.json",
    "fix_ci_or_review": ".ai-factory/gates/sample_fix_ci_or_review.json",
}

ALLOWED_GATE_DECISIONS = {
    "APPROVE_MERGE",
    "REQUEST_CHANGES",
    "REJECT",
    "BLOCKED_NEEDS_HUMAN",
}


def read_json(relative_path: str) -> dict:
    return json.loads((REPO_ROOT / relative_path).read_text(encoding="utf-8"))


class AIFactoryContractTests(unittest.TestCase):
    def test_config_references_required_ai_factory_paths_and_controls(self) -> None:
        config = (REPO_ROOT / ".ai-factory/config.yaml").read_text(encoding="utf-8")
        required_paths = [
            ".ai-factory/DESCRIPTION.md",
            ".ai-factory/ARCHITECTURE.md",
            ".ai-factory/RULES.md",
            ".ai-factory/rules",
            ".ai-factory/plans",
            ".ai-factory/qa",
            ".ai-factory/gates",
            ".windmill",
            "docs",
        ]

        for relative_path in required_paths:
            with self.subTest(path=relative_path):
                self.assertTrue((REPO_ROOT / relative_path).exists())
                self.assertIn(relative_path, config)

        for control in [
            "require_pull_request: true",
            "require_human_for_release: true",
            "require_human_for_restricted_changes: true",
            "require_coding_agent_dispatch: true",
            "max_auto_fix_iterations: 2",
        ]:
            self.assertIn(control, config)

    def test_gate_decisions_are_aligned_between_rules_config_and_gate_evaluator(self) -> None:
        rules = (REPO_ROOT / ".ai-factory/RULES.md").read_text(encoding="utf-8")
        config = (REPO_ROOT / ".ai-factory/config.yaml").read_text(encoding="utf-8")

        for decision in ALLOWED_GATE_DECISIONS:
            with self.subTest(decision=decision):
                self.assertIn(decision, rules)
                self.assertIn(decision, config)

        self.assertTrue(final_gate_check.evaluate_gate({"decision": "APPROVE_MERGE"})["pass"])
        for decision in ["REQUEST_CHANGES", "REJECT", "BLOCKED_NEEDS_HUMAN"]:
            with self.subTest(decision=decision):
                self.assertFalse(final_gate_check.evaluate_gate({"decision": decision})["pass"])
        for alias in ["PASS", "PASSED", "APPROVED", "FAILED", "BLOCKED"]:
            with self.subTest(alias=alias):
                result = final_gate_check.evaluate_gate({"decision": alias})
                self.assertEqual(result["decision"], "BLOCKED_NEEDS_HUMAN")
                self.assertFalse(result["pass"])

    def test_flow_gate_samples_match_executable_flow_harness(self) -> None:
        task = mil_flow.load_task(REPO_ROOT / "tests/fixtures/agent_task.json")

        for flow, relative_path in FLOW_SAMPLE_FILES.items():
            with self.subTest(flow=flow):
                sample = read_json(relative_path)
                expected = mil_flow.run_flow(flow, task).to_dict()
                self.assertEqual(sample, expected)

    def test_plan_to_pr_sample_proves_coding_dispatch_before_implementation(self) -> None:
        sample = read_json(".ai-factory/gates/sample_plan_to_pr.json")
        calls = [
            f"{call['agent']}.{call['action']}"
            for call in sample["agent_calls"]
        ]

        self.assertEqual(calls[0], "windmill.dispatch_coding_agent")
        self.assertLess(calls.index("windmill.dispatch_coding_agent"), calls.index("codex.implement"))
        self.assertEqual(sample["artifacts"]["dispatch"]["developer_agent"], "codex")

    def test_pr_quality_gate_sample_is_accepted_by_final_gate_checker(self) -> None:
        sample = read_json(".ai-factory/gates/sample_pr_quality_gate.json")
        gate = sample["artifacts"]["aif_gate_result"]

        result = final_gate_check.evaluate_gate(gate)

        self.assertEqual(result["decision"], "APPROVE_MERGE")
        self.assertTrue(result["pass"])

    def test_ai_factory_validation_script_self_test_succeeds(self) -> None:
        script_path = REPO_ROOT / "scripts/agent-gate/validate_ai_factory.py"

        self.assertTrue(script_path.exists())
        completed = subprocess.run(
            [sys.executable, str(script_path), "--self-test"],
            cwd=REPO_ROOT,
            check=False,
            text=True,
            capture_output=True,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr + completed.stdout)


if __name__ == "__main__":
    unittest.main()
