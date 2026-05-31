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


class MemoryContractTests(unittest.TestCase):
    def test_build_memory_record_sanitizes_text_and_metadata(self) -> None:
        record = memory_contract.build_memory_record(
            project="MIL",
            task_id="MEM-001",
            memory_type="operator_note",
            text="ngrok authtoken: 3EU0LPOk9SAsOmGvcR4XsCwcbDq_7819BPj7BSFG13Wc7fwPs",
            metadata={"token": "ghp_123456789012345678901234567890123456"},
        )

        serialized = json.dumps(record, sort_keys=True)
        self.assertNotIn("3EU0LPOk9SAsOmGvcR4XsCwcbDq_7819BPj7BSFG13Wc7fwPs", serialized)
        self.assertNotIn("ghp_123456789012345678901234567890123456", serialized)
        self.assertTrue(record["sanitized"])
        self.assertEqual(record["metadata"]["source"], "mil-ai-factory")

    def test_rejects_unsupported_memory_type(self) -> None:
        with self.assertRaisesRegex(ValueError, "unsupported memory_type"):
            memory_contract.build_memory_record(
                project="MIL",
                task_id="MEM-001",
                memory_type="raw_chat_log",
                text="do not store raw chat logs",
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
                )
            )
            store.add(
                memory_contract.build_memory_record(
                    project="OTHER",
                    task_id="MEM-002",
                    memory_type="ci_pattern",
                    text="different project memory",
                )
            )

            results = store.search("Windmill secret", project="MIL")

            self.assertEqual(len(results), 1)
            self.assertEqual(results[0]["project"], "MIL")
            self.assertEqual(results[0]["task_id"], "MEM-001")

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
