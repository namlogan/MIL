from __future__ import annotations

import hashlib
import hmac
import importlib.util
import json
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
    spec.loader.exec_module(module)
    return module


class GitHubWebhookPublicRelayTests(unittest.TestCase):
    def setUp(self) -> None:
        self.relay = load_module(
            "github_webhook_public_relay",
            "scripts/windmill/github_webhook_public_relay.py",
        )

    def _signature(self, body: bytes, secret: str = "secret") -> str:
        digest = hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()
        return f"sha256={digest}"

    def test_relay_verifies_signature_before_forwarding(self) -> None:
        body = b'{"zen":"Keep it logically awesome."}'
        headers = {
            "X-Hub-Signature-256": self._signature(body),
            "X-GitHub-Event": "ping",
            "X-GitHub-Delivery": "delivery-1",
            "Content-Type": "application/json",
        }

        decision = self.relay.evaluate_request(
            method="POST",
            path="/mil/github-webhook",
            headers=headers,
            body=body,
            secret="secret",
        )

        self.assertTrue(decision.forward)
        self.assertEqual(decision.status_code, 200)

    def test_relay_rejects_bad_signature_without_forwarding(self) -> None:
        decision = self.relay.evaluate_request(
            method="POST",
            path="/mil/github-webhook",
            headers={"X-Hub-Signature-256": "sha256=bad"},
            body=b"{}",
            secret="secret",
        )

        self.assertFalse(decision.forward)
        self.assertEqual(decision.status_code, 401)
        self.assertIn("signature", decision.message)

    def test_relay_exposes_only_configured_webhook_route(self) -> None:
        for method, path, expected_status in [
            ("GET", "/mil/github-webhook", 405),
            ("POST", "/api/version", 404),
            ("POST", "/api/r/admins/mil/github-webhook", 404),
        ]:
            with self.subTest(method=method, path=path):
                decision = self.relay.evaluate_request(
                    method=method,
                    path=path,
                    headers={"X-Hub-Signature-256": "sha256=bad"},
                    body=b"{}",
                    secret="secret",
                )

                self.assertFalse(decision.forward)
                self.assertEqual(decision.status_code, expected_status)

    def test_forward_headers_are_allowlisted(self) -> None:
        headers = {
            "X-Hub-Signature-256": "sha256=sig",
            "X-GitHub-Event": "issues",
            "X-GitHub-Delivery": "delivery-1",
            "Content-Type": "application/json",
            "Authorization": "Bearer must-not-forward",
            "Cookie": "must-not-forward",
        }

        observed = self.relay.build_forward_headers(headers, body_length=2)

        self.assertEqual(observed["X-GitHub-Event"], "issues")
        self.assertEqual(observed["X-GitHub-Delivery"], "delivery-1")
        self.assertEqual(observed["X-Hub-Signature-256"], "sha256=sig")
        self.assertEqual(observed["Content-Type"], "application/json")
        self.assertEqual(observed["Content-Length"], "2")
        self.assertNotIn("Authorization", observed)
        self.assertNotIn("Cookie", observed)

    def test_builds_auto_dispatch_request_from_verified_webhook(self) -> None:
        body = json.dumps(
            {
                "action": "labeled",
                "repository": {"full_name": "namlogan/MIL"},
                "issue": {
                    "number": 41,
                    "title": "MIL-041 Auto",
                    "labels": [{"name": "agent:auto-build"}],
                },
            }
        ).encode("utf-8")
        headers = {
            "X-GitHub-Event": "issues",
            "X-GitHub-Delivery": "delivery-1",
            "X-Hub-Signature-256": self._signature(body),
        }

        request = self.relay.build_auto_dispatch_request(headers, body)

        self.assertEqual(request["github_event"], "issues")
        self.assertEqual(request["delivery"], "delivery-1")
        self.assertEqual(request["payload"]["issue"]["number"], 41)

    def test_auto_dispatch_launch_is_opt_in_and_backgrounded(self) -> None:
        calls: list[dict] = []
        body = b'{"action":"labeled","issue":{"number":41}}'
        headers = {
            "X-GitHub-Event": "issues",
            "X-GitHub-Delivery": "delivery-1",
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            disabled = self.relay.maybe_launch_auto_dispatch(
                headers=headers,
                body=body,
                enabled=False,
                repo_root=str(REPO_ROOT),
                queue_root=Path(tmpdir),
                launcher=lambda **kwargs: calls.append(kwargs),
            )
            enabled = self.relay.maybe_launch_auto_dispatch(
                headers=headers,
                body=body,
                enabled=True,
                repo_root=str(REPO_ROOT),
                queue_root=Path(tmpdir),
                launcher=lambda **kwargs: calls.append(kwargs),
            )

        self.assertFalse(disabled["launched"])
        self.assertTrue(enabled["launched"])
        self.assertEqual(len(calls), 1)
        self.assertIn("auto_dispatcher.py", " ".join(calls[0]["command"]))
        self.assertIn("--preload-augment-context", calls[0]["command"])
        self.assertTrue(calls[0]["log_path"].endswith(".log"))


if __name__ == "__main__":
    unittest.main()
