from __future__ import annotations

import importlib.util
import json
import re
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


def read_json(relative_path: str) -> dict:
    return json.loads((REPO_ROOT / relative_path).read_text(encoding="utf-8"))


class AIFactoryRuntimeConfigTests(unittest.TestCase):
    def test_runtime_config_files_define_agents_workflows_and_evidence(self) -> None:
        agents = read_json(".ai-factory/runtime/agents.json")
        workflows = read_json(".ai-factory/runtime/workflows.json")
        evidence = read_json(".ai-factory/runtime/evidence.json")
        environment = read_json(".ai-factory/runtime/environment.json")

        self.assertEqual(agents["version"], 1)
        for agent in [
            "codex_developer",
            "codex_qa",
            "augment_context_provider",
            "auggie_advisory",
            "mem0_memory",
            "windmill_orchestrator",
            "github_merge_gate",
        ]:
            with self.subTest(agent=agent):
                self.assertIn(agent, agents["agents"])
                self.assertIn("allowed_actions", agents["agents"][agent])
                self.assertIn("forbidden_actions", agents["agents"][agent])

        self.assertNotIn("auggie_supervised_developer", agents["agents"])
        augment = agents["agents"]["augment_context_provider"]
        self.assertEqual(augment["runtime"], "augment_mcp")
        self.assertIn("provide_codebase_context", augment["allowed_actions"])
        for forbidden in [
            "implement_scoped_issue",
            "create_branch",
            "open_pr",
            "write_pr_evidence",
        ]:
            self.assertIn(forbidden, augment["forbidden_actions"])

        memory = agents["agents"]["mem0_memory"]
        self.assertEqual(memory["runtime"], "mem0_optional")
        self.assertFalse(memory["writes_code"])
        self.assertTrue(memory["requires_sanitization"])
        self.assertIn("retrieve_project_memory", memory["allowed_actions"])
        for forbidden in [
            "store_secrets",
            "implement_scoped_issue",
            "final_merge_approval",
            "merge_main",
        ]:
            self.assertIn(forbidden, memory["forbidden_actions"])

        default_flow = workflows["workflows"]["default_issue_to_merge"]["stages"]
        stage_names = [stage["name"] for stage in default_flow]
        self.assertEqual(
            stage_names,
            [
                "issue_to_plan",
                "plan_to_pr",
                "control_plane_ci",
                "augment_context_review",
                "codex_qa_gate",
                "protected_merge",
            ],
        )
        self.assertLess(
            stage_names.index("plan_to_pr"),
            stage_names.index("control_plane_ci"),
        )
        self.assertEqual(
            workflows["workflows"]["default_issue_to_merge"]["memory_provider"],
            "mem0_memory",
        )
        self.assertIn(
            "codex_qa_gate",
            workflows["workflows"]["default_issue_to_merge"]["memory_checkpoints"],
        )

        self.assertIn("developer_handoff", evidence["required_evidence"])
        self.assertIn("qa_gate", evidence["required_evidence"])
        self.assertIn("memory_record", evidence["required_evidence"])
        self.assertEqual(evidence["artifact_paths"]["memory"], ".ai-factory/memory")
        self.assertIn("wmill", environment["required_tools"])
        self.assertIn(
            "f/mil/github_status_token",
            environment["windmill"]["required_secret_references"],
        )
        self.assertEqual(environment["augment"]["context_provider"], "augment_mcp")
        self.assertFalse(environment["augment"]["coding_allowed"])
        self.assertIn("AUGMENT_MCP_TOKEN", environment["augment"]["required_local_env"])
        self.assertEqual(environment["memory"]["provider"], "mem0_optional")
        self.assertEqual(environment["memory"]["runtime_agent"], "mem0_memory")
        self.assertTrue(environment["memory"]["must_sanitize_before_write"])
        self.assertFalse(environment["memory"]["store_secrets"])
        self.assertEqual(
            environment["memory"]["local_fallback_store"],
            ".ai-factory/memory/local_memory.jsonl",
        )
        self.assertIsNone(
            re.search(
                r"(gho_|ghp_|github_pat_|accessToken|sk-)",
                json.dumps(environment),
            )
        )

    def test_bootstrap_runtime_validator_accepts_current_install(self) -> None:
        bootstrap = load_module(
            "bootstrap_runtime",
            "scripts/ai-factory/bootstrap_runtime.py",
        )

        self.assertEqual(bootstrap.validate(REPO_ROOT), [])

    def test_bootstrap_runtime_tool_check_is_explicit(self) -> None:
        bootstrap = load_module(
            "bootstrap_runtime",
            "scripts/ai-factory/bootstrap_runtime.py",
        )

        self.assertEqual(bootstrap.validate(REPO_ROOT, check_tools=False), [])
        self.assertIn(
            "missing local tools: wmill",
            bootstrap.validate(
                REPO_ROOT,
                check_tools=True,
                tool_resolver=lambda tool: None if tool == "wmill" else f"/usr/bin/{tool}",
            ),
        )

    def test_bootstrap_runtime_cli_self_test_passes(self) -> None:
        completed = subprocess.run(
            [
                sys.executable,
                "scripts/ai-factory/bootstrap_runtime.py",
                "--check",
            ],
            cwd=REPO_ROOT,
            check=False,
            text=True,
            capture_output=True,
        )

        self.assertEqual(completed.returncode, 0, completed.stderr + completed.stdout)
        self.assertIn("AI Factory runtime check passed", completed.stdout)


if __name__ == "__main__":
    unittest.main()
