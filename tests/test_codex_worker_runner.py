from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
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
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


class CodexWorkerRunnerTests(unittest.TestCase):
    def test_dry_run_cli_writes_non_executing_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "codex-worker-result.json"
            evidence_root = Path(tmpdir) / "codex-worker-evidence"
            completed = subprocess.run(
                [
                    sys.executable,
                    "scripts/agent-flow/codex_worker.py",
                    "--repo",
                    str(REPO_ROOT),
                    "--task",
                    str(REPO_ROOT / "tests" / "fixtures" / "agent_task.json"),
                    "--evidence-root",
                    str(evidence_root),
                    "--dry-run",
                    "--out",
                    str(output_path),
                ],
                cwd=REPO_ROOT,
                check=False,
                text=True,
                capture_output=True,
            )

            self.assertEqual(completed.returncode, 0, completed.stderr + completed.stdout)
            result = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertEqual(result["decision"], "CODEX_WORKER_READY")
            self.assertEqual(result["status"], "DRY_RUN")
            self.assertFalse(result["execution"]["execute_agent"])
            self.assertFalse(result["git"]["worktree_created"])
            self.assertFalse(result["git"]["committed"])
            self.assertIn("codex", result["codex_command"])
            self.assertFalse(evidence_root.exists())

    def test_self_test_uses_contract_without_running_codex(self) -> None:
        runner = load_module("codex_worker_runner", "scripts/agent-flow/codex_worker.py")

        self.assertEqual(runner.main(["--self-test"]), 0)

    def test_pr_create_command_propagates_safe_labels(self) -> None:
        runner = load_module("codex_worker_runner_labels", "scripts/agent-flow/codex_worker.py")

        command = runner._pr_create_command(
            {"base_branch": "main", "branch": "agent/mil-041"},
            {
                "pr_labels": [
                    "agent:auto-build",
                    "automerge:candidate",
                    "bad label",
                    "owner:auto-approve",
                ]
            },
        )

        self.assertIn("--label", command)
        self.assertIn("agent:auto-build", command)
        self.assertIn("automerge:candidate", command)
        self.assertIn("owner:auto-approve", command)
        self.assertNotIn("bad label", command)


if __name__ == "__main__":
    unittest.main()
