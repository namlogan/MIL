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


class Mem0ProviderPreflightTests(unittest.TestCase):
    def setUp(self) -> None:
        self.preflight = load_module(
            "check_mem0_provider",
            "scripts/agent-memory/check_mem0_provider.py",
        )

    def test_local_adapter_is_ready_without_external_credentials(self) -> None:
        result = self.preflight.check_provider({})

        self.assertTrue(result["ok"])
        self.assertEqual(result["mode"], "local_jsonl")
        self.assertIn(".ai-factory/memory/local_memory.jsonl", result["store"])

    def test_self_hosted_mem0_requires_http_endpoint(self) -> None:
        result = self.preflight.check_provider({"MEM0_BASE_URL": "localhost:8888"})

        self.assertFalse(result["ok"])
        self.assertIn("MEM0_BASE_URL must start with http:// or https://", result["errors"])

    def test_self_hosted_mem0_is_detected_from_base_url(self) -> None:
        result = self.preflight.check_provider({"MEM0_BASE_URL": "http://localhost:8888"})

        self.assertTrue(result["ok"])
        self.assertEqual(result["mode"], "mem0_self_hosted")
        self.assertEqual(result["base_url"], "http://localhost:8888")


if __name__ == "__main__":
    unittest.main()
