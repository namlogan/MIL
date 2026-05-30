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


check_agent_tools = load_module(
    "check_agent_tools",
    "scripts/agent-flow/check_agent_tools.py",
)


class AgentToolCheckTests(unittest.TestCase):
    def test_tool_check_reports_available_tools(self) -> None:
        def fake_runner(command: list[str]) -> tuple[int, str, str]:
            return 0, f"{command[0]} 1.0.0", ""

        result = check_agent_tools.check_tools(runner=fake_runner)

        self.assertTrue(result["ok"])
        self.assertTrue(result["tools"]["codex"]["available"])
        self.assertTrue(result["tools"]["auggie"]["available"])
        self.assertTrue(result["tools"]["wmill"]["available"])

    def test_tool_check_reports_missing_tools(self) -> None:
        def fake_runner(command: list[str]) -> tuple[int, str, str]:
            if command[0] == "auggie":
                return 127, "", "command not found"
            return 0, "codex-cli 1.0.0", ""

        result = check_agent_tools.check_tools(runner=fake_runner)

        self.assertFalse(result["ok"])
        self.assertTrue(result["tools"]["codex"]["available"])
        self.assertFalse(result["tools"]["auggie"]["available"])
        self.assertTrue(result["tools"]["wmill"]["available"])


if __name__ == "__main__":
    unittest.main()
