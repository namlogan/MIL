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


def sample_task() -> dict[str, object]:
    return {
        "task_id": "MIL-321",
        "issue_id": "https://github.com/namlogan/MIL/issues/321",
        "title": "Wire real plan to PR dispatch",
        "goal": "Dispatch a scoped Codex worker with Augment codebase context.",
        "acceptance_criteria": [
            "Windmill returns a Codex command pack",
            "Augment context is included in the worker prompt",
        ],
        "allowed_files": [
            "f/mil/**",
            "scripts/agent-flow/**",
            "tests/**",
            "docs/**",
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


class PlanToPrOrchestratorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.plan_to_pr = load_module("plan_to_pr", "f/mil/plan_to_pr.py")

    def test_dispatch_builds_codex_worker_command_pack_with_augment_context(self) -> None:
        result = self.plan_to_pr.main(
            {
                "task": sample_task(),
                "options": {
                    "repo_root": str(REPO_ROOT),
                    "execute_agent": False,
                    "push": False,
                    "open_pr": False,
                },
                "memory_context": [
                    {
                        "memory_id": "mem-plan-1",
                        "memory_type": "framework_rule",
                        "memory": "Use python3 -m unittest discover -s tests -v.",
                        "source_ref": "https://github.com/namlogan/MIL/pull/29",
                        "status": "approved",
                    }
                ],
                "augment_context": [
                    {
                        "source_uri": "augment://codebase/f/mil/plan_to_pr.py",
                        "summary": "plan_to_pr must dispatch through codex_worker.",
                    }
                ],
            }
        )

        self.assertEqual(result["decision"], "PLAN_TO_PR_COMMAND_PACK_READY")
        self.assertFalse(result["blocking"])
        calls = [f"{call['agent']}.{call['action']}" for call in result["agent_calls"]]
        self.assertEqual(
            calls,
            [
                "mem0_memory.wm_task_context_pack",
                "augment_context.provide_codebase_context",
                "windmill.dispatch_coding_agent",
                "codex.prepare_command_pack",
            ],
        )

        worker = result["artifacts"]["codex_worker"]
        self.assertEqual(worker["decision"], "CODEX_WORKER_READY")
        self.assertFalse(worker["execution"]["execute_agent"])
        self.assertFalse(worker["execution"]["push"])
        self.assertFalse(worker["execution"]["open_pr"])
        self.assertEqual(worker["codex_command"][0:2], ["codex", "exec"])
        self.assertIn("mem-plan-1", worker["prompt"])
        self.assertIn("plan_to_pr must dispatch through codex_worker", worker["prompt"])
        self.assertIn("## AI Factory v2 Rule Hierarchy", worker["prompt"])

    def test_dispatch_blocks_when_task_scope_is_not_worker_ready(self) -> None:
        result = self.plan_to_pr.main(
            {
                "task": {
                    "task_id": "MIL-322",
                    "title": "Missing scope",
                    "goal": "Try to dispatch without allowed files.",
                    "checks": ["git diff --check"],
                    "restricted_changes": [],
                },
                "options": {"repo_root": str(REPO_ROOT)},
            }
        )

        self.assertEqual(result["decision"], "PLAN_TO_PR_BLOCKED")
        self.assertTrue(result["blocking"])
        self.assertEqual(result["artifacts"]["codex_worker"]["decision"], "CODEX_WORKER_BLOCKED")
        self.assertIn("allowed_files", result["reasons"][0])

    def test_dispatch_builds_readonly_augment_context_request_without_context(self) -> None:
        result = self.plan_to_pr.main(
            {
                "task": sample_task(),
                "options": {"repo_root": str(REPO_ROOT)},
            }
        )

        augment = result["artifacts"]["augment_context"]
        self.assertEqual(augment["provider"], "augment_mcp")
        self.assertEqual(augment["mcp_server"], "mil-auggie-local")
        self.assertEqual(augment["tool"], "codebase-retrieval")
        self.assertEqual(augment["mode"], "readonly")
        self.assertEqual(augment["context_pack"], [])
        self.assertIn("Wire real plan to PR dispatch", augment["query"])
        self.assertIn("f/mil/**", augment["query"])

    def test_dispatch_rejects_non_codex_developer_agent(self) -> None:
        result = self.plan_to_pr.main(
            {
                "task": {
                    **sample_task(),
                    "developer_agent": "auggie_supervised",
                },
                "options": {"repo_root": str(REPO_ROOT)},
            }
        )

        self.assertEqual(result["decision"], "PLAN_TO_PR_BLOCKED")
        self.assertTrue(result["blocking"])
        self.assertIn("Codex is the only supported coding agent", result["reasons"][0])

    def test_dispatch_redacts_secret_shapes_from_context(self) -> None:
        result = self.plan_to_pr.main(
            {
                "task": sample_task(),
                "options": {"repo_root": str(REPO_ROOT)},
                "augment_context": [
                    {
                        "source_uri": "augment://secret",
                        "summary": "accessToken: 13f6f4f5c84c0ce8ec2b780595dcb28ca2019c2f36f313ac8146497702999318",
                    }
                ],
            }
        )
        serialized = str(result)

        self.assertNotIn(
            "13f6f4f5c84c0ce8ec2b780595dcb28ca2019c2f36f313ac8146497702999318",
            serialized,
        )
        self.assertIn("[REDACTED_TOKEN]", serialized)


if __name__ == "__main__":
    unittest.main()
