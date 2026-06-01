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

    def _healthy_responses(self) -> dict[tuple[str, ...], tuple[int, str, str]]:
        return {
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
            ("python3", "scripts/delivery/validate_delivery_os.py", "--self-test"): (
                0,
                "validate_delivery_os self-test passed\n",
                "",
            ),
            ("python3", "scripts/contracts/validate_contracts.py", "--self-test"): (
                0,
                "validate_contracts self-test passed\n",
                "",
            ),
            ("python3", "scripts/operator/sdlc_metrics_report.py", "--self-test"): (
                0,
                "sdlc_metrics_report self-test passed\n",
                "",
            ),
            ("python3", "scripts/agent-flow/check_agent_tools.py"): (
                0,
                json.dumps({"ok": True, "tools": {"codex": {"available": True}}}),
                "",
            ),
            ("tmux", "list-sessions"): (
                0,
                "mil-webhook-relay: 1 windows\nmil-webhook-ngrok: 1 windows\n",
                "",
            ),
            (
                "gh",
                "pr",
                "list",
                "--repo",
                "namlogan/MIL",
                "--state",
                "open",
                "--json",
                "number,title,url,mergeStateStatus,statusCheckRollup",
                "--limit",
                "20",
            ): (0, "[]\n", ""),
            (
                "gh",
                "run",
                "list",
                "--repo",
                "namlogan/MIL",
                "--branch",
                "main",
                "--limit",
                "3",
                "--json",
                "conclusion,status,databaseId,displayTitle,createdAt,url",
            ): (
                0,
                json.dumps(
                    [
                        {
                            "conclusion": "success",
                            "status": "completed",
                            "databaseId": 1,
                            "displayTitle": "main",
                            "createdAt": "2026-06-01T00:00:00Z",
                            "url": "https://github.com/namlogan/MIL/actions/runs/1",
                        }
                    ]
                ),
                "",
            ),
            (
                "wmill",
                "--workspace",
                "mil-local",
                "job",
                "list",
                "--failed",
                "--limit",
                "5",
                "--json",
            ): (0, "[]\n", ""),
            ("python3", "scripts/agent-flow/check_augment_config.py"): (
                0,
                json.dumps({"ok": True, "warnings": []}),
                "",
            ),
            ("python3", "scripts/agent-memory/check_mem0_provider.py"): (
                0,
                json.dumps({"ok": True, "mode": "local_jsonl", "warnings": []}),
                "",
            ),
            ("python3", "scripts/github/check_branch_protection.py"): (
                0,
                json.dumps({"ok": True, "warnings": []}),
                "",
            ),
        }

    def test_build_daily_status_reports_ready_when_core_checks_pass(self) -> None:
        runner = self._runner(self._healthy_responses())

        result = self.daily_status.build_daily_status(REPO_ROOT, runner=runner)

        self.assertEqual(result["overall"], "ready")
        self.assertTrue(result["checks"]["git_clean"]["ok"])
        self.assertTrue(result["checks"]["agent_tools"]["ok"])
        for check_name in [
            "runtime_sessions",
            "github_open_prs",
            "github_main_ci",
            "windmill_failed_jobs",
            "delivery_os",
            "contract_skeletons",
            "sdlc_metrics",
            "augment_config",
            "mem0_provider",
            "branch_protection",
            "dispatch_queue",
        ]:
            with self.subTest(check=check_name):
                self.assertIn(check_name, result["checks"])
                self.assertTrue(result["checks"][check_name]["ok"], result["checks"][check_name])

    def test_build_daily_status_blocks_when_workspace_is_dirty(self) -> None:
        responses = self._healthy_responses()
        responses[("git", "status", "--short", "--branch")] = (
            0,
            "## main...origin/main\n M AGENTS.md\n",
            "",
        )
        runner = self._runner(responses)

        result = self.daily_status.build_daily_status(REPO_ROOT, runner=runner)

        self.assertEqual(result["overall"], "attention")
        self.assertFalse(result["checks"]["git_clean"]["ok"])
        self.assertIn("workspace has uncommitted changes", result["checks"]["git_clean"]["summary"])

    def test_build_daily_status_reports_attention_when_relay_session_missing(self) -> None:
        responses = self._healthy_responses()
        responses[("tmux", "list-sessions")] = (0, "mil-webhook-ngrok: 1 windows\n", "")
        runner = self._runner(responses)

        result = self.daily_status.build_daily_status(REPO_ROOT, runner=runner)

        self.assertEqual(result["overall"], "attention")
        self.assertFalse(result["checks"]["runtime_sessions"]["ok"])
        self.assertIn("relay session missing", result["checks"]["runtime_sessions"]["summary"])

    def test_build_daily_status_reports_attention_when_latest_main_ci_failed(self) -> None:
        responses = self._healthy_responses()
        responses[
            (
                "gh",
                "run",
                "list",
                "--repo",
                "namlogan/MIL",
                "--branch",
                "main",
                "--limit",
                "3",
                "--json",
                "conclusion,status,databaseId,displayTitle,createdAt,url",
            )
        ] = (
            0,
            json.dumps(
                [
                    {
                        "conclusion": "failure",
                        "status": "completed",
                        "databaseId": 2,
                        "displayTitle": "main",
                        "createdAt": "2026-06-01T00:00:00Z",
                        "url": "https://github.com/namlogan/MIL/actions/runs/2",
                    }
                ]
            ),
            "",
        )
        runner = self._runner(responses)

        result = self.daily_status.build_daily_status(REPO_ROOT, runner=runner)

        self.assertEqual(result["overall"], "attention")
        self.assertFalse(result["checks"]["github_main_ci"]["ok"])
        self.assertIn("latest main CI is failure", result["checks"]["github_main_ci"]["summary"])

    def test_dispatch_queue_check_reports_blocking_results(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            queue = root / ".ai-factory/queue/webhooks"
            queue.mkdir(parents=True)
            (queue / "blocked.result.json").write_text(
                json.dumps({"decision": "AUTO_DISPATCH_BLOCKED", "reason": "scope missing"}),
                encoding="utf-8",
            )
            runner = self._runner(self._healthy_responses())

            result = self.daily_status.build_daily_status(root, runner=runner)

        self.assertEqual(result["overall"], "attention")
        self.assertFalse(result["checks"]["dispatch_queue"]["ok"])
        self.assertEqual(result["checks"]["dispatch_queue"]["blocking_count"], 1)


if __name__ == "__main__":
    unittest.main()
