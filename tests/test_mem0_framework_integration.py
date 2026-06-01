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


class FakeMem0Memory:
    def __init__(self) -> None:
        self.add_calls: list[dict[str, object]] = []
        self.search_calls: list[dict[str, object]] = []
        self.records: list[dict[str, object]] = []

    def add(self, **kwargs):
        self.add_calls.append(kwargs)
        memory = kwargs["messages"][0]["content"]
        record = {
            "id": "mem_fake_1",
            "memory": memory,
            "metadata": kwargs["metadata"],
            "user_id": kwargs.get("user_id"),
            "agent_id": kwargs.get("agent_id"),
            "run_id": kwargs.get("run_id"),
        }
        self.records.append(record)
        return {"results": [record]}

    def search(self, query: str, **kwargs):
        self.search_calls.append({"query": query, **kwargs})
        return {"results": self.records}


class Mem0FrameworkIntegrationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.integration = load_module(
            "mem0_framework_integration",
            "scripts/agent-memory/mem0_framework_integration.py",
        )

    def test_builds_python_mem0_add_kwargs_from_framework_writeback_record(self) -> None:
        record = self.integration.sample_writeback_record()["record"]

        kwargs = self.integration.build_python_mem0_add_kwargs(record)

        self.assertEqual(kwargs["messages"][0]["content"], record["memory"])
        self.assertFalse(kwargs["infer"])
        self.assertEqual(kwargs["memory_type"], "framework_rule")
        self.assertEqual(kwargs["user_id"], "repo:github:namlogan/MIL")
        self.assertEqual(kwargs["agent_id"], "codex")
        self.assertEqual(kwargs["run_id"], "mem0-integration-smoke")
        self.assertNotIn("app_id", kwargs)
        self.assertEqual(kwargs["metadata"]["app_id"], "mil-framework")

    def test_add_and_search_use_mem0_library_shape_for_approved_memory(self) -> None:
        fake = FakeMem0Memory()
        record = self.integration.sample_writeback_record(
            text="Framework memory uses scoped context packs before Codex work."
        )["record"]

        add_result = self.integration.add_record_to_mem0(fake, record)
        context_pack = self.integration.search_mem0_context(
            fake,
            query="context packs",
            filters=self.integration.sample_filters(),
            limit=3,
        )

        serialized = json.dumps({"add": add_result, "context": context_pack}, sort_keys=True)
        self.assertEqual(fake.add_calls[0]["memory_type"], "framework_rule")
        self.assertEqual(fake.search_calls[0]["top_k"], 3)
        self.assertEqual(context_pack[0]["memory_id"], "mem_fake_1")
        self.assertIn("context packs", context_pack[0]["memory"])
        self.assertIn("source_ref", serialized)

    def test_writeback_rejects_secret_payload_before_mem0_adapter(self) -> None:
        with self.assertRaisesRegex(ValueError, "restricted memory payload"):
            self.integration.sample_writeback_record(
                text="Repo uses mem0ai library. token: ghp_123456789012345678901234567890123456"
            )

    def test_framework_smoke_routes_mem0_context_into_plan_to_pr(self) -> None:
        result = self.integration.run_framework_smoke(repo_root=REPO_ROOT)

        self.assertTrue(result["ok"], result)
        self.assertEqual(result["writeback_decision"], "MEMORY_WRITE_RECORDED")
        self.assertEqual(result["mem0_add_calls"], 1)
        self.assertEqual(result["mem0_search_calls"], 1)
        self.assertEqual(result["context_pack_count"], 1)
        self.assertEqual(result["plan_to_pr_decision"], "PLAN_TO_PR_COMMAND_PACK_READY")
        self.assertIn("library-first Mem0", result["codex_prompt_excerpt"])


if __name__ == "__main__":
    unittest.main()
