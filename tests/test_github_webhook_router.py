from __future__ import annotations

import hashlib
import hmac
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


def compact_json(data: dict) -> str:
    return json.dumps(data, separators=(",", ":"), sort_keys=True)


def signed_headers(secret: str, raw_string: str, event: str) -> dict[str, str]:
    digest = hmac.new(
        secret.encode("utf-8"),
        raw_string.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    return {
        "X-GitHub-Event": event,
        "X-GitHub-Delivery": "delivery-123",
        "X-Hub-Signature-256": f"sha256={digest}",
    }


class GitHubWebhookRouterTests(unittest.TestCase):
    def setUp(self) -> None:
        self.router = load_module(
            "github_webhook_router",
            "f/mil/github_webhook_router.py",
        )
        self.secret = "local-webhook-secret"
        self.router._get_secret_variable = lambda path: self.secret

    def preprocess(self, event: str, payload: dict) -> dict:
        raw_string = compact_json(payload)
        return self.router.preprocessor(
            {
                "kind": "http",
                "headers": signed_headers(self.secret, raw_string, event),
                "raw_string": raw_string,
                "body": payload,
                "method": "POST",
            }
        )

    def test_preprocessor_verifies_github_signature_without_leaking_secret(self) -> None:
        payload = {"action": "opened", "repository": {"full_name": "namlogan/MIL"}}
        raw_string = compact_json(payload)
        event = {
            "kind": "http",
            "headers": {
                **signed_headers(self.secret, raw_string, "issues"),
                "X-Hub-Signature-256": "sha256=bad",
            },
            "raw_string": raw_string,
            "body": payload,
        }

        with self.assertRaisesRegex(ValueError, "invalid GitHub webhook signature") as ctx:
            self.router.preprocessor(event)

        self.assertNotIn(self.secret, str(ctx.exception))

    def test_issue_agent_plan_label_routes_to_issue_to_plan(self) -> None:
        payload = {
            "action": "labeled",
            "repository": {"full_name": "namlogan/MIL"},
            "issue": {
                "number": 4,
                "title": "MIL-004 Provision Windmill workspace and secrets",
                "body": "Goal: wire Windmill.",
                "labels": [{"name": "agent:plan"}],
            },
        }

        request = self.preprocess("issues", payload)["request"]
        result = self.router.main(request)

        self.assertEqual(result["route"]["flow"], "issue_to_plan")
        self.assertEqual(result["route"]["task"]["task_id"], "MIL-004")
        self.assertEqual(result["result"]["flow"], "issue_to_plan")
        self.assertEqual(result["result"]["agent_calls"][0]["agent"], "augment_context")
        self.assertEqual(result["result"]["agent_calls"][-1]["agent"], "codex")

    def test_pull_request_event_routes_to_codex_quality_gate(self) -> None:
        payload = {
            "action": "synchronize",
            "repository": {"full_name": "namlogan/MIL"},
            "pull_request": {
                "number": 18,
                "title": "MIL-004 Add webhook routing",
                "head": {"sha": "abc123", "ref": "agent/4-github-webhook-routing"},
                "html_url": "https://github.com/namlogan/MIL/pull/18",
            },
        }

        request = self.preprocess("pull_request", payload)["request"]
        result = self.router.main(request)

        self.assertEqual(result["route"]["flow"], "pr_quality_gate")
        self.assertEqual(result["route"]["task"]["task_id"], "MIL-004")
        self.assertEqual(result["route"]["github"]["pr_number"], 18)
        self.assertEqual(result["result"]["agent_calls"][0]["action"], "provide_gate_context")
        self.assertEqual(result["result"]["agent_calls"][-1]["action"], "qa")

    def test_failed_workflow_run_routes_to_fix_flow(self) -> None:
        payload = {
            "action": "completed",
            "repository": {"full_name": "namlogan/MIL"},
            "workflow_run": {
                "conclusion": "failure",
                "head_sha": "abc123",
                "pull_requests": [{"number": 18}],
            },
        }

        request = self.preprocess("workflow_run", payload)["request"]
        result = self.router.main(request)

        self.assertEqual(result["route"]["flow"], "fix_ci_or_review")
        self.assertEqual(
            [call["agent"] for call in result["result"]["agent_calls"]],
            ["augment_context", "codex"],
        )

    def test_issue_comment_commands_route_to_requested_flow(self) -> None:
        payload = {
            "action": "created",
            "repository": {"full_name": "namlogan/MIL"},
            "issue": {"number": 4, "title": "MIL-004 Windmill"},
            "comment": {"body": "/agent qa"},
        }

        request = self.preprocess("issue_comment", payload)["request"]
        result = self.router.main(request)

        self.assertEqual(result["route"]["flow"], "pr_quality_gate")

    def test_unmatched_webhook_is_ignored_without_agent_calls(self) -> None:
        payload = {
            "action": "labeled",
            "repository": {"full_name": "namlogan/MIL"},
            "issue": {
                "number": 4,
                "title": "MIL-004 Provision Windmill workspace and secrets",
                "labels": [{"name": "documentation"}],
            },
        }

        request = self.preprocess("issues", payload)["request"]
        result = self.router.main(request)

        self.assertFalse(result["route"]["matched"])
        self.assertEqual(result["decision"], "IGNORED_NO_ROUTE")
        self.assertNotIn("result", result)

    def test_http_trigger_config_routes_github_webhooks_to_router(self) -> None:
        trigger = (
            REPO_ROOT / "f" / "mil" / "github_webhook.http_trigger.yaml"
        ).read_text(encoding="utf-8")

        self.assertIn("script_path: f/mil/github_webhook_router", trigger)
        self.assertIn("route_path: mil/github-webhook", trigger)
        self.assertIn("http_method: post", trigger)
        self.assertIn("raw_string: true", trigger)
        self.assertIn("authentication_method: none", trigger)


if __name__ == "__main__":
    unittest.main()
