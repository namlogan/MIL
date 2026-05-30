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


flow_sequence = load_module("flow_sequence", "scripts/agent-flow/flow_sequence.py")


class FlowSequenceTests(unittest.TestCase):
    def test_default_sequence_includes_coding_agent_dispatch_before_implementation(self) -> None:
        task_path = REPO_ROOT / "tests" / "fixtures" / "agent_task.json"

        result = flow_sequence.run_sequence(task_path)

        self.assertEqual(
            [item["flow"] for item in result["flows"]],
            ["issue_to_plan", "plan_to_pr", "pr_quality_gate"],
        )
        plan_to_pr = next(item for item in result["flows"] if item["flow"] == "plan_to_pr")
        calls = [
            f"{call['agent']}.{call['action']}"
            for call in plan_to_pr["agent_calls"]
        ]
        self.assertEqual(calls[0], "windmill.dispatch_coding_agent")
        self.assertLess(calls.index("windmill.dispatch_coding_agent"), calls.index("codex.implement"))
        self.assertEqual(plan_to_pr["artifacts"]["dispatch"]["developer_agent"], "codex")
        self.assertFalse(result["blocking"])

    def test_cli_writes_sequence_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            out_path = Path(tmpdir) / "sequence.json"
            exit_code = flow_sequence.main(
                [
                    "--task",
                    str(REPO_ROOT / "tests" / "fixtures" / "agent_task.json"),
                    "--out",
                    str(out_path),
                ]
            )

            self.assertEqual(exit_code, 0)
            payload = json.loads(out_path.read_text(encoding="utf-8"))
            self.assertEqual(payload["task_id"], "MIL-001")
            self.assertEqual(payload["flows"][-1]["decision"], "APPROVE_MERGE")
            self.assertNotIn(
                "fix_ci_or_review",
                [item["flow"] for item in payload["flows"]],
            )


if __name__ == "__main__":
    unittest.main()
