import asyncio
import json
import subprocess
import sys
import unittest

from apps.flange_qc_v2.asgi import app
from apps.flange_qc_v2.health import build_health_snapshot


class HealthSnapshotTests(unittest.TestCase):
    def test_default_snapshot_reports_safe_bootstrap_states(self) -> None:
        snapshot = build_health_snapshot()

        self.assertEqual(snapshot["service"], "flange-qc-v2")
        self.assertEqual(snapshot["status"], "degraded")
        self.assertEqual(snapshot["mode"], "bootstrap")
        self.assertEqual(snapshot["version"], "0.1.0")
        self.assertEqual(snapshot["subsystems"]["camera"], "unavailable")
        self.assertEqual(snapshot["subsystems"]["gpu"], "unavailable")
        self.assertEqual(snapshot["subsystems"]["model"], "unavailable")
        self.assertEqual(
            snapshot["subsystems"]["product_specs"],
            "draft_requires_qc_owner_approval",
        )
        self.assertEqual(snapshot["subsystems"]["sop_decision_engine"], "not_implemented")
        self.assertEqual(snapshot["decision_authority"], "none")
        self.assertEqual(snapshot["model_boundary"]["contract_version"], "model.artifact.v1")
        self.assertEqual(snapshot["model_boundary"]["state"], "manifest_ready_shadow_only")
        self.assertFalse(snapshot["model_boundary"]["production_authority"])
        self.assertIn("qc_product_spec_approval_missing", snapshot["blockers"])


class AsgiHealthEndpointTests(unittest.TestCase):
    def test_health_endpoint_returns_json_snapshot(self) -> None:
        messages = []

        async def receive():
            return {"type": "http.request", "body": b"", "more_body": False}

        async def send(message):
            messages.append(message)

        scope = {"type": "http", "method": "GET", "path": "/health"}
        asyncio.run(app(scope, receive, send))

        start = messages[0]
        body = json.loads(messages[1]["body"].decode("utf-8"))
        headers = dict(start["headers"])

        self.assertEqual(start["status"], 200)
        self.assertEqual(headers[b"content-type"], b"application/json")
        self.assertEqual(body["service"], "flange-qc-v2")
        self.assertEqual(body["decision_authority"], "none")


class HealthCliTests(unittest.TestCase):
    def test_module_cli_prints_health_json(self) -> None:
        completed = subprocess.run(
            [sys.executable, "-m", "apps.flange_qc_v2"],
            check=True,
            text=True,
            capture_output=True,
        )

        body = json.loads(completed.stdout)
        self.assertEqual(body["service"], "flange-qc-v2")
        self.assertEqual(body["status"], "degraded")
