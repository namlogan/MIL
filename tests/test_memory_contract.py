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


memory_contract = load_module("memory_contract", "scripts/agent-memory/memory_contract.py")


def required_metadata(**overrides: object) -> dict[str, object]:
    metadata: dict[str, object] = {
        "tenant_id": "org_mil",
        "workspace_id": "engineering",
        "repo": "MIL",
        "repo_id": "github:namlogan/MIL",
        "user_id": "repo:github:namlogan/MIL",
        "agent_id": "codex",
        "run_id": "windmill-job-123",
        "source_uri": "https://github.com/namlogan/MIL/pull/26",
        "confidence": 0.82,
        "status": "active",
        "visibility": "repo",
        "created_by": "agent",
    }
    metadata.update(overrides)
    return metadata


class MemoryContractTests(unittest.TestCase):
    def test_build_memory_record_sanitizes_text_and_metadata(self) -> None:
        record = memory_contract.build_memory_record(
            project="MIL",
            task_id="MEM-001",
            memory_type="operator_note",
            text="ngrok authtoken: 3EU0LPOk9SAsOmGvcR4XsCwcbDq_7819BPj7BSFG13Wc7fwPs",
            metadata=required_metadata(token="ghp_123456789012345678901234567890123456"),
        )

        serialized = json.dumps(record, sort_keys=True)
        self.assertNotIn("3EU0LPOk9SAsOmGvcR4XsCwcbDq_7819BPj7BSFG13Wc7fwPs", serialized)
        self.assertNotIn("ghp_123456789012345678901234567890123456", serialized)
        self.assertTrue(record["sanitized"])
        self.assertEqual(record["metadata"]["source"], "mil-ai-factory")
        self.assertEqual(record["metadata"]["repo_id"], "github:namlogan/MIL")
        self.assertEqual(record["entity_scope"]["user_id"], "repo:github:namlogan/MIL")

    def test_requires_provenance_metadata(self) -> None:
        with self.assertRaisesRegex(ValueError, "metadata.tenant_id is required"):
            memory_contract.build_memory_record(
                project="MIL",
                task_id="MEM-001",
                memory_type="ci_pattern",
                text="CI failed because Windmill secret was missing",
                metadata={"repo_id": "github:namlogan/MIL"},
            )

    def test_requires_mem0_entity_scope(self) -> None:
        metadata = required_metadata()
        for field in ["user_id", "agent_id", "run_id"]:
            metadata.pop(field)

        with self.assertRaisesRegex(ValueError, "at least one Mem0 entity scope"):
            memory_contract.build_memory_record(
                project="MIL",
                task_id="MEM-001",
                memory_type="ci_pattern",
                text="CI failed because Windmill secret was missing",
                metadata=metadata,
            )

    def test_approval_required_memory_requires_human_approval(self) -> None:
        with self.assertRaisesRegex(ValueError, "requires approval"):
            memory_contract.build_memory_record(
                project="MIL",
                task_id="MEM-001",
                memory_type="architecture_decision",
                text="Billing must use PaymentGateway only.",
                metadata=required_metadata(created_by="agent"),
            )

        record = memory_contract.build_memory_record(
            project="MIL",
            task_id="MEM-001",
            memory_type="architecture_decision",
            text="Billing must use PaymentGateway only.",
            metadata=required_metadata(created_by="human", approved_by="logan"),
            approved=True,
        )

        self.assertEqual(record["write_policy"], "approval_required")
        self.assertEqual(record["metadata"]["approved_by"], "logan")

    def test_build_search_filters_rejects_global_search(self) -> None:
        with self.assertRaisesRegex(ValueError, "tenant_id is required"):
            memory_contract.build_search_filters(
                repo_id="github:namlogan/MIL",
                memory_types=["ci_pattern"],
                user_id="repo:github:namlogan/MIL",
            )
        with self.assertRaisesRegex(ValueError, "repo_id is required"):
            memory_contract.build_search_filters(
                tenant_id="org_mil",
                memory_types=["ci_pattern"],
                user_id="repo:github:namlogan/MIL",
            )
        with self.assertRaisesRegex(ValueError, "at least one Mem0 entity scope"):
            memory_contract.build_search_filters(
                tenant_id="org_mil",
                repo_id="github:namlogan/MIL",
                memory_types=["ci_pattern"],
            )

        filters = memory_contract.build_search_filters(
            tenant_id="org_mil",
            repo_id="github:namlogan/MIL",
            memory_types=["ci_pattern", "review_rule"],
            user_id="repo:github:namlogan/MIL",
        )

        serialized = json.dumps(filters, sort_keys=True)
        self.assertIn("org_mil", serialized)
        self.assertIn("github:namlogan/MIL", serialized)
        self.assertIn("ci_pattern", serialized)
        self.assertIn("repo:github:namlogan/MIL", serialized)

    def test_rejects_unsupported_memory_type(self) -> None:
        with self.assertRaisesRegex(ValueError, "unsupported memory_type"):
            memory_contract.build_memory_record(
                project="MIL",
                task_id="MEM-001",
                memory_type="raw_chat_log",
                text="do not store raw chat logs",
                metadata=required_metadata(),
            )

    def test_local_store_add_and_project_scoped_search(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            store = memory_contract.LocalJsonlMemoryStore(Path(tmpdir) / "memory.jsonl")
            store.add(
                memory_contract.build_memory_record(
                    project="MIL",
                    task_id="MEM-001",
                    memory_type="ci_pattern",
                    text="control-plane failure was caused by missing Windmill secret",
                    metadata=required_metadata(),
                )
            )
            store.add(
                memory_contract.build_memory_record(
                    project="OTHER",
                    task_id="MEM-002",
                    memory_type="ci_pattern",
                    text="different project memory",
                    metadata=required_metadata(
                        tenant_id="org_other",
                        repo="OTHER",
                        repo_id="github:namlogan/OTHER",
                        user_id="repo:github:namlogan/OTHER",
                    ),
                )
            )

            filters = memory_contract.build_search_filters(
                tenant_id="org_mil",
                repo_id="github:namlogan/MIL",
                memory_types=["ci_pattern"],
                user_id="repo:github:namlogan/MIL",
            )
            results = store.search("Windmill secret", filters=filters)

            self.assertEqual(len(results), 1)
            self.assertEqual(results[0]["project"], "MIL")
            self.assertEqual(results[0]["task_id"], "MEM-001")

    def test_local_store_rejects_unscoped_search(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            store = memory_contract.LocalJsonlMemoryStore(Path(tmpdir) / "memory.jsonl")

            with self.assertRaisesRegex(ValueError, "strict filters are required"):
                store.search("Windmill secret")

    def test_mem0_payloads_keep_curated_summary_and_filters(self) -> None:
        record = memory_contract.build_memory_record(
            project="MIL",
            task_id="MEM-001",
            memory_type="failure_pattern",
            text="Prior CI failures in this area were caused by non-idempotent retries.",
            metadata=required_metadata(),
        )

        add_payload = memory_contract.build_mem0_add_payload(record)
        search_payload = memory_contract.build_mem0_search_payload(
            "non-idempotent retries",
            filters=memory_contract.build_search_filters(
                tenant_id="org_mil",
                repo_id="github:namlogan/MIL",
                memory_types=["failure_pattern"],
                user_id="repo:github:namlogan/MIL",
            ),
            limit=3,
        )

        self.assertFalse(add_payload["infer"])
        self.assertEqual(add_payload["user_id"], "repo:github:namlogan/MIL")
        self.assertEqual(add_payload["metadata"]["memory_type"], "failure_pattern")
        self.assertEqual(search_payload["limit"], 3)
        self.assertIn("filters", search_payload)

    def test_cli_self_test_passes(self) -> None:
        completed = subprocess.run(
            [sys.executable, "scripts/agent-memory/memory_contract.py", "--self-test"],
            cwd=REPO_ROOT,
            check=False,
            text=True,
            capture_output=True,
        )

        self.assertEqual(completed.returncode, 0, completed.stderr + completed.stdout)
        self.assertIn("memory_contract self-test passed", completed.stdout)


if __name__ == "__main__":
    unittest.main()
