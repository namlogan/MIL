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
        self.assertEqual(result["result"]["agent_calls"][-1]["agent"], "mem0_memory")

    def test_issue_agent_build_label_dispatches_real_plan_to_pr(self) -> None:
        payload = {
            "action": "labeled",
            "repository": {"full_name": "namlogan/MIL"},
            "issue": {
                "number": 31,
                "title": "MIL-031 Route webhook build to worker",
                "body": "\n".join(
                    [
                        "### Task ID",
                        "MIL-031",
                        "",
                        "### User or business goal",
                        "Route build requests into the real Codex worker dispatcher.",
                        "",
                        "### Acceptance criteria",
                        "- Router calls real plan_to_pr orchestration.",
                        "- Codex worker prompt includes Augment codebase context.",
                        "",
                        "### Allowed files and out-of-scope files",
                        "Allowed:",
                        "- f/mil/github_webhook_router.py",
                        "- tests/test_github_webhook_router.py",
                        "",
                        "Out of scope:",
                        "- secrets/**",
                        "",
                        "### Required checks",
                        "- python3 -m unittest tests.test_github_webhook_router -v",
                        "- git diff --check",
                        "",
                        "### Restricted change check",
                        "- [x] none of the above",
                        "",
                        "### Rollback note",
                        "Revert the webhook router change.",
                    ]
                ),
                "labels": [{"name": "agent:build"}],
            },
        }

        request = self.preprocess("issues", payload)["request"]
        result = self.router.main(request)

        self.assertEqual(result["route"]["flow"], "plan_to_pr")
        self.assertEqual(result["route"]["task"]["task_id"], "MIL-031")
        self.assertEqual(
            result["result"]["decision"],
            "PLAN_TO_PR_COMMAND_PACK_READY",
        )
        self.assertEqual(
            [call["agent"] for call in result["result"]["agent_calls"]],
            ["mem0_memory", "augment_context", "windmill", "codex"],
        )
        codex_worker = result["result"]["artifacts"]["codex_worker"]
        self.assertEqual(codex_worker["decision"], "CODEX_WORKER_READY")
        self.assertIn("Augment Codebase Context", codex_worker["prompt"])
        self.assertIn(
            "f/mil/github_webhook_router.py",
            result["route"]["task"]["allowed_files"],
        )

    def test_issue_agent_build_works_when_windmill_repo_is_not_mounted(self) -> None:
        payload = {
            "action": "labeled",
            "repository": {"full_name": "namlogan/MIL"},
            "issue": {
                "number": 32,
                "title": "MIL-032 Hosted Windmill build dispatch",
                "body": "\n".join(
                    [
                        "### Task ID",
                        "MIL-032",
                        "",
                        "### User or business goal",
                        "Dispatch build requests from hosted Windmill without repo mounts.",
                        "",
                        "### Acceptance criteria",
                        "- Router calls real plan_to_pr orchestration.",
                        "- Worker prompt includes AI Factory rules.",
                        "",
                        "### Allowed files and out-of-scope files",
                        "Allowed:",
                        "- f/mil/github_webhook_router.py",
                        "- tests/test_github_webhook_router.py",
                        "",
                        "Out of scope:",
                        "- secrets/**",
                        "",
                        "### Required checks",
                        "- python3 -m unittest tests.test_github_webhook_router -v",
                        "",
                        "### Restricted change check",
                        "- [x] none of the above",
                        "",
                        "### Rollback note",
                        "Revert the webhook router change.",
                    ]
                ),
                "labels": [{"name": "agent:build"}],
            },
        }

        request = self.preprocess("issues", payload)["request"]
        request["options"] = {"repo_root": "/tmp/mil-hosted-windmill-no-repo"}
        result = self.router.main(request)

        self.assertEqual(
            result["result"]["decision"],
            "PLAN_TO_PR_COMMAND_PACK_READY",
        )
        rule_paths = {
            source["path"]
            for source in result["result"]["artifacts"]["codex_worker"]["rule_sources"]
        }
        self.assertIn(".ai-factory/RULES.md", rule_paths)
        self.assertIn(".ai-factory/rules/windmill.md", rule_paths)

    def test_hosted_rule_sources_match_repo_ai_factory_rules(self) -> None:
        for source in self.router.HOSTED_AI_FACTORY_RULE_SOURCES:
            with self.subTest(path=source["path"]):
                expected = (REPO_ROOT / source["path"]).read_text(encoding="utf-8")
                self.assertEqual(source["content"], expected.strip())

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
        self.assertEqual(result["result"]["agent_calls"][-1]["action"], "store_qa_memory")

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
            ["augment_context", "mem0_memory", "codex", "mem0_memory"],
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
