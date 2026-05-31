from __future__ import annotations

import unittest
from pathlib import Path

from f.mil import codex_worker_contract


REPO_ROOT = Path(__file__).resolve().parents[1]


def sample_task() -> dict[str, object]:
    return {
        "task_id": "MIL-123",
        "issue_id": "https://github.com/namlogan/MIL/issues/123",
        "title": "Add scoped worker",
        "goal": "Implement a scoped Codex worker for MIL automation.",
        "acceptance_criteria": [
            "Worker creates an isolated branch",
            "Worker refuses out-of-scope file changes",
        ],
        "allowed_files": [
            "f/mil/**",
            "scripts/agent-flow/**",
            "tests/**",
        ],
        "out_of_scope_files": [
            ".env",
            ".ai-factory/secrets/**",
        ],
        "checks": [
            "python3 -m unittest discover -s tests -v",
            "git diff --check",
        ],
        "base_branch": "main",
        "developer_agent": "codex",
        "restricted_changes": [],
        "rollback_note": "Revert the PR branch.",
    }


class CodexWorkerContractTests(unittest.TestCase):
    def test_build_worker_plan_is_windmill_safe_and_non_executing_by_default(self) -> None:
        plan = codex_worker_contract.build_worker_plan(
            {
                **sample_task(),
                "memory_context": [
                    {
                        "memory_id": "mem_1",
                        "memory_type": "repo_convention",
                        "memory": "Use python3 -m unittest discover -s tests -v.",
                        "source_uri": "https://github.com/namlogan/MIL/pull/1",
                    }
                ],
                "augment_context": [
                    {
                        "source_uri": "augment://symbols/codex_worker",
                        "summary": "Runner must stay scoped to allowed_files.",
                    }
                ],
            },
            repo_root=REPO_ROOT,
        )

        self.assertEqual(plan["decision"], "CODEX_WORKER_READY")
        self.assertFalse(plan["execution"]["execute_agent"])
        self.assertFalse(plan["execution"]["push"])
        self.assertFalse(plan["execution"]["open_pr"])
        self.assertEqual(plan["branch"], "agent/mil-123-add-scoped-worker")
        self.assertEqual(plan["base_branch"], "main")
        self.assertIn(".ai-factory/tmp/worktrees/mil-123-add-scoped-worker", plan["worktree_path"])
        self.assertIn(".ai-factory/qa/codex_worker/MIL-123", plan["evidence_dir"])
        self.assertEqual(plan["codex_command"][0:2], ["codex", "exec"])
        self.assertIn("--ask-for-approval", plan["codex_command"])
        self.assertIn("never", plan["codex_command"])
        self.assertIn("--sandbox", plan["codex_command"])
        self.assertIn("workspace-write", plan["codex_command"])
        self.assertTrue(plan["codex_stdin_prompt"])
        self.assertIn("mem_1", plan["prompt"])
        self.assertIn("Runner must stay scoped", plan["prompt"])
        self.assertIn("Do not edit files outside allowed_files.", plan["prompt"])

    def test_worker_prompt_loads_ai_factory_v2_rule_sources(self) -> None:
        plan = codex_worker_contract.build_worker_plan(
            sample_task(),
            repo_root=REPO_ROOT,
        )

        rule_paths = [source["path"] for source in plan["rule_sources"]]
        self.assertEqual(rule_paths[0], ".ai-factory/RULES.md")
        for required in [
            ".ai-factory/rules/base.md",
            ".ai-factory/rules/implementation.md",
            ".ai-factory/rules/quality-gates.md",
            ".ai-factory/rules/security.md",
            ".ai-factory/rules/memory.md",
            ".ai-factory/rules/windmill.md",
        ]:
            with self.subTest(required=required):
                self.assertIn(required, rule_paths)

        prompt = plan["prompt"]
        self.assertIn("## AI Factory v2 Rule Hierarchy", prompt)
        self.assertIn("rules.<area> > rules/base.md > paths.rules_file", prompt)
        self.assertIn(".ai-factory/rules/implementation.md", prompt)
        self.assertIn("Run implementation through plan/checkpoint discipline", prompt)
        self.assertIn("schema_version", prompt)
        self.assertIn("gate", prompt)

    def test_restricted_changes_block_before_command_build(self) -> None:
        plan = codex_worker_contract.build_worker_plan(
            {
                **sample_task(),
                "restricted_changes": ["production deployment behavior"],
            },
            repo_root=REPO_ROOT,
        )

        self.assertEqual(plan["decision"], "CODEX_WORKER_BLOCKED")
        self.assertTrue(plan["blocking"])
        self.assertEqual(plan["codex_command"], [])
        self.assertIn("restricted_changes", plan["reasons"][0])

    def test_allowed_change_validation_rejects_out_of_scope_files(self) -> None:
        codex_worker_contract.validate_allowed_changes(
            ["f/mil/codex_worker.py", "tests/test_codex_worker_contract.py"],
            allowed_files=["f/mil/**", "tests/**"],
            out_of_scope_files=[".env", ".ai-factory/secrets/**"],
        )

        with self.assertRaisesRegex(ValueError, "outside allowed_files"):
            codex_worker_contract.validate_allowed_changes(
                ["README.md"],
                allowed_files=["f/mil/**", "tests/**"],
                out_of_scope_files=[],
            )

        with self.assertRaisesRegex(ValueError, "out_of_scope_files"):
            codex_worker_contract.validate_allowed_changes(
                [".ai-factory/secrets/token.txt"],
                allowed_files=[".ai-factory/**"],
                out_of_scope_files=[".ai-factory/secrets/**"],
            )

    def test_prompt_and_evidence_redact_secret_shapes(self) -> None:
        plan = codex_worker_contract.build_worker_plan(
            {
                **sample_task(),
                "goal": "Use accessToken: 13f6f4f5c84c0ce8ec2b780595dcb28ca2019c2f36f313ac8146497702999318",
                "memory_context": [
                    {
                        "memory_id": "mem_secret",
                        "memory": "Prior run used ghp_123456789012345678901234567890123456.",
                    }
                ],
            },
            repo_root=REPO_ROOT,
        )
        serialized = str(plan)

        self.assertNotIn("13f6f4f5c84c0ce8ec2b780595dcb28ca2019c2f36f313ac8146497702999318", serialized)
        self.assertNotIn("ghp_123456789012345678901234567890123456", serialized)
        self.assertIn("[REDACTED_TOKEN]", serialized)
        self.assertIn("[REDACTED_GITHUB_TOKEN]", serialized)


if __name__ == "__main__":
    unittest.main()
