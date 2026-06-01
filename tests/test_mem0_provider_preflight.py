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

    def test_self_hosted_live_check_uses_health_endpoint_without_exposing_key(self) -> None:
        calls: list[tuple[str, dict[str, str], float]] = []

        def fake_get(url: str, headers: dict[str, str], timeout: float) -> tuple[int, bytes]:
            calls.append((url, headers, timeout))
            return 200, b'{"ok":true}'

        result = self.preflight.check_provider(
            {
                "MEM0_BASE_URL": "http://localhost:8888/",
                "MEM0_API_KEY": "secret-mem0-key",
            },
            live_check=True,
            http_get=fake_get,
        )

        self.assertTrue(result["ok"], result)
        self.assertEqual(result["live_check"]["url"], "http://localhost:8888/health")
        self.assertEqual(calls[0][1]["X-API-Key"], "secret-mem0-key")
        self.assertNotIn("secret-mem0-key", json.dumps(result))


if __name__ == "__main__":
    unittest.main()
