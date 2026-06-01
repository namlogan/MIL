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


class PublicEndpointCheckTests(unittest.TestCase):
    def setUp(self) -> None:
        self.checker = load_module(
            "check_public_endpoint",
            "scripts/windmill/check_public_endpoint.py",
        )

    def test_accepts_ngrok_webhook_url_pointing_to_relay(self) -> None:
        result = self.checker.evaluate_endpoint_config(
            public_url="https://sublease-malformed-tribune.ngrok-free.dev/mil/github-webhook",
            relay_url="http://127.0.0.1:18090",
        )

        self.assertTrue(result["ok"], result)
        self.assertEqual(result["health_url"], "https://sublease-malformed-tribune.ngrok-free.dev/healthz")

    def test_rejects_public_url_that_exposes_windmill_or_wrong_path(self) -> None:
        result = self.checker.evaluate_endpoint_config(
            public_url="https://sublease-malformed-tribune.ngrok-free.dev/api/r/admins/mil/github-webhook",
            relay_url="http://127.0.0.1:8090",
        )

        self.assertFalse(result["ok"])
        self.assertIn("public URL path must be /mil/github-webhook", result["errors"])
        self.assertIn("relay URL must not point at the Windmill port", result["errors"])

    def test_health_check_calls_local_and_public_healthz(self) -> None:
        calls: list[str] = []

        def fake_get(url: str, timeout: float) -> tuple[int, bytes]:
            calls.append(url)
            return 200, b'{"ok": true}'

        result = self.checker.run_health_checks(
            public_url="https://sublease-malformed-tribune.ngrok-free.dev/mil/github-webhook",
            relay_url="http://127.0.0.1:18090",
            http_get=fake_get,
        )

        self.assertTrue(result["ok"], result)
        self.assertEqual(
            calls,
            [
                "http://127.0.0.1:18090/healthz",
                "https://sublease-malformed-tribune.ngrok-free.dev/healthz",
            ],
        )


if __name__ == "__main__":
    unittest.main()
