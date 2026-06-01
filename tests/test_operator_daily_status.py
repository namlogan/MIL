from __future__ import annotations

import importlib.util
import json
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


class FakeRunner:
    def __init__(self, responses: dict[tuple[str, ...], tuple[int, str, str]]) -> None:
        self.responses = responses
        self.commands: list[tuple[str, ...]] = []

    def __call__(self, command: list[str], cwd: Path) -> object:
        key = tuple(command)
        self.commands.append(key)
        return self.daily_status.CommandResult(
            returncode=self.responses.get(key, (127, "", "missing fake command"))[0],
            stdout=self.responses.get(key, (127, "", "missing fake command"))[1],
            stderr=self.responses.get(key, (127, "", "missing fake command"))[2],
        )


class OperatorDailyStatusTests(unittest.TestCase):
    def setUp(self) -> None:
        self.daily_status = load_module(
            "daily_status",
            "scripts/operator/daily_status.py",
        )

    def _runner(self, responses: dict[tuple[str, ...], tuple[int, str, str]]) -> FakeRunner:
        runner = FakeRunner(responses)
        runner.daily_status = self.daily_status
        return runner

    def test_build_daily_status_reports_ready_when_core_checks_pass(self) -> None:
        runner = self._runner(
            {
                ("git", "status", "--short", "--branch"): (0, "## main...origin/main\n", ""),
                ("python3", "scripts/ai-factory/bootstrap_runtime.py", "--check"): (
                    0,
                    "AI Factory runtime check passed\n",
                    "",
                ),
                ("python3", "scripts/windmill/validate_windmill_project.py", "--self-test"): (
                    0,
                    "Windmill project validation passed\n",
                    "",
                ),
                ("python3", "scripts/agent-flow/check_agent_tools.py"): (
                    0,
                    json.dumps({"ok": True, "tools": {"codex": {"available": True}}}),
                    "",
                ),
            }
        )

        result = self.daily_status.build_daily_status(REPO_ROOT, runner=runner)

        self.assertEqual(result["overall"], "ready")
        self.assertTrue(result["checks"]["git_clean"]["ok"])
        self.assertTrue(result["checks"]["agent_tools"]["ok"])

    def test_build_daily_status_blocks_when_workspace_is_dirty(self) -> None:
        runner = self._runner(
            {
                ("git", "status", "--short", "--branch"): (
                    0,
                    "## main...origin/main\n M AGENTS.md\n",
                    "",
                ),
                ("python3", "scripts/ai-factory/bootstrap_runtime.py", "--check"): (0, "ok", ""),
                ("python3", "scripts/windmill/validate_windmill_project.py", "--self-test"): (
                    0,
                    "ok",
                    "",
                ),
                ("python3", "scripts/agent-flow/check_agent_tools.py"): (
                    0,
                    json.dumps({"ok": True}),
                    "",
                ),
            }
        )

        result = self.daily_status.build_daily_status(REPO_ROOT, runner=runner)

        self.assertEqual(result["overall"], "attention")
        self.assertFalse(result["checks"]["git_clean"]["ok"])
        self.assertIn("workspace has uncommitted changes", result["checks"]["git_clean"]["summary"])


if __name__ == "__main__":
    unittest.main()
