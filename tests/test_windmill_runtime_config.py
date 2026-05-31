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


class WindmillRuntimeConfigTests(unittest.TestCase):
    def test_wmill_project_files_exist_and_sync_only_safe_paths(self) -> None:
        config = (REPO_ROOT / "wmill.yaml").read_text(encoding="utf-8")

        self.assertIn('includes:', config)
        self.assertIn('"f/**"', config)
        self.assertIn("skipSecrets: true", config)
        self.assertIn("nonDottedPaths: true", config)
        self.assertTrue((REPO_ROOT / "wmill-lock.yaml").exists())

    def test_runtime_scripts_exist_with_metadata(self) -> None:
        folder_metadata = REPO_ROOT / "f" / "mil" / "folder.meta.yaml"

        self.assertTrue(folder_metadata.exists())
        self.assertIn("owners:", folder_metadata.read_text(encoding="utf-8"))

        for name in [
            "codex_worker_contract",
            "codex_worker",
            "plan_to_pr_contract",
            "issue_to_plan",
            "plan_to_pr",
            "pr_quality_gate",
            "fix_ci_or_review",
            "mem0_retrieve",
            "mem0_writeback",
            "auggie_supervised_advisory",
            "github_commit_status",
            "github_webhook_router",
        ]:
            with self.subTest(name=name):
                script = REPO_ROOT / "f" / "mil" / f"{name}.py"
                metadata = REPO_ROOT / "f" / "mil" / f"{name}.script.yaml"

                self.assertTrue(script.exists())
                self.assertTrue(metadata.exists())
                self.assertIn("kind: script", metadata.read_text(encoding="utf-8"))

    def test_windmill_wrappers_use_workspace_imports(self) -> None:
        for name in [
            "codex_worker",
            "issue_to_plan",
            "plan_to_pr",
            "pr_quality_gate",
            "fix_ci_or_review",
            "mem0_retrieve",
            "mem0_writeback",
            "auggie_supervised_advisory",
            "github_webhook_router",
        ]:
            with self.subTest(name=name):
                script = (REPO_ROOT / "f" / "mil" / f"{name}.py").read_text(
                    encoding="utf-8"
                )

                self.assertRegex(script, r"from f\.mil\.(codex_worker_contract|flow_contract|memory_contract|plan_to_pr_contract) import")
                self.assertNotIn("from codex_worker_contract import", script)
                self.assertNotIn("from flow_contract import", script)
                self.assertNotIn("from memory_contract import", script)

    def test_github_webhook_http_trigger_is_versioned(self) -> None:
        trigger = REPO_ROOT / "f" / "mil" / "github_webhook.http_trigger.yaml"

        self.assertTrue(trigger.exists())
        contents = trigger.read_text(encoding="utf-8")
        self.assertIn("script_path: f/mil/github_webhook_router", contents)
        self.assertIn("route_path: mil/github-webhook", contents)
        self.assertIn("http_method: post", contents)
        self.assertIn("raw_string: true", contents)
        self.assertIn("authentication_method: none", contents)

    def test_windmill_worker_bridge_reuses_ai_factory_contract(self) -> None:
        bridge = load_module(
            "mil_windmill_bridge",
            "scripts/windmill/mil_windmill_bridge.py",
        )

        result = bridge.run_windmill_flow(
            "plan_to_pr",
            {
                "task_id": "MIL-LOCAL",
                "checks": ["git diff --check"],
                "restricted_changes": [],
            },
        )

        self.assertEqual(result["flow"], "plan_to_pr")
        calls = [f"{call['agent']}.{call['action']}" for call in result["agent_calls"]]
        self.assertEqual(calls[0], "mem0_memory.retrieve_plan_memory")
        self.assertIn("windmill.dispatch_coding_agent", calls)
        self.assertLess(calls.index("windmill.dispatch_coding_agent"), calls.index("codex.implement"))

    def test_windmill_codex_worker_wrapper_returns_command_pack_not_execution(self) -> None:
        codex_worker = load_module("codex_worker", "f/mil/codex_worker.py")

        result = codex_worker.main(
            {
                "task": {
                    "task_id": "MIL-LOCAL",
                    "title": "Local dispatch",
                    "goal": "Prepare a scoped local Codex worker run.",
                    "acceptance_criteria": ["Worker produces evidence"],
                    "allowed_files": ["docs/**"],
                    "checks": ["git diff --check"],
                    "restricted_changes": [],
                },
                "options": {
                    "repo_root": str(REPO_ROOT),
                },
            }
        )

        self.assertEqual(result["decision"], "CODEX_WORKER_READY")
        self.assertFalse(result["execution"]["execute_agent"])
        self.assertFalse(result["execution"]["push"])
        self.assertFalse(result["execution"]["open_pr"])
        self.assertEqual(result["source_of_truth"], "github_issue_or_explicit_task")
        self.assertIn("codex", result["codex_command"])

    def test_windmill_codex_worker_accepts_preloaded_rule_sources(self) -> None:
        codex_worker = load_module("codex_worker_preloaded_rules", "f/mil/codex_worker.py")

        result = codex_worker.main(
            {
                "task": {
                    "task_id": "MIL-LOCAL",
                    "title": "Local dispatch",
                    "goal": "Prepare a scoped local Codex worker run.",
                    "acceptance_criteria": ["Worker produces evidence"],
                    "allowed_files": ["docs/**"],
                    "checks": ["git diff --check"],
                    "restricted_changes": [],
                },
                "options": {
                    "repo_root": "/tmp/mil-repo-not-mounted",
                    "rule_sources": [
                        {
                            "name": "paths.rules_file",
                            "path": ".ai-factory/RULES.md",
                            "content": "## Rules\nAI Factory 2.x baseline.",
                        },
                        {
                            "name": "rules.base",
                            "path": ".ai-factory/rules/base.md",
                            "content": "Base AI Factory worker boundaries.",
                        },
                        {
                            "name": "rules.implementation",
                            "path": ".ai-factory/rules/implementation.md",
                            "content": "Run implementation through plan/checkpoint discipline.",
                        },
                        {
                            "name": "rules.quality_gates",
                            "path": ".ai-factory/rules/quality-gates.md",
                            "content": "Emit schema_version and gate evidence.",
                        },
                        {
                            "name": "rules.security",
                            "path": ".ai-factory/rules/security.md",
                            "content": "Do not expose secrets.",
                        },
                        {
                            "name": "rules.memory",
                            "path": ".ai-factory/rules/memory.md",
                            "content": "Memory writeback must be scoped.",
                        },
                        {
                            "name": "rules.windmill",
                            "path": ".ai-factory/rules/windmill.md",
                            "content": "Windmill must not bypass gates.",
                        },
                    ],
                },
            }
        )

        self.assertEqual(result["decision"], "CODEX_WORKER_READY")
        self.assertEqual(result["rule_sources"][0]["path"], ".ai-factory/RULES.md")
        self.assertIn(".ai-factory/rules/implementation.md", result["prompt"])

    def test_windmill_memory_scripts_enforce_scope_and_policy(self) -> None:
        mem0_retrieve = load_module("mem0_retrieve", "f/mil/mem0_retrieve.py")
        mem0_writeback = load_module("mem0_writeback", "f/mil/mem0_writeback.py")

        with self.assertRaisesRegex(ValueError, "tenant_id is required"):
            mem0_retrieve.main(
                {
                    "query": "how to fix tests",
                    "repo_id": "github:namlogan/MIL",
                    "memory_types": ["ci_pattern"],
                    "user_id": "repo:github:namlogan/MIL",
                }
            )

        retrieved = mem0_retrieve.main(
            {
                "query": "Windmill secret",
                "tenant_id": "org_mil",
                "repo_id": "github:namlogan/MIL",
                "memory_types": ["ci_pattern"],
                "user_id": "repo:github:namlogan/MIL",
                "records": [
                    {
                        "project": "MIL",
                        "task_id": "MEM-001",
                        "memory_type": "ci_pattern",
                        "memory": "Windmill secret caused prior CI failure.",
                        "metadata": {
                            "tenant_id": "org_mil",
                            "repo_id": "github:namlogan/MIL",
                            "user_id": "repo:github:namlogan/MIL",
                            "status": "active",
                            "visibility": "repo",
                        },
                    }
                ],
            }
        )

        self.assertEqual(retrieved["decision"], "MEMORY_CONTEXT_READY")
        self.assertEqual(retrieved["filters"]["AND"][0]["tenant_id"], "org_mil")
        self.assertEqual(retrieved["context_pack"][0]["memory_id"], "local-1")

        with self.assertRaisesRegex(ValueError, "requires approval"):
            mem0_writeback.main(
                {
                    "project": "MIL",
                    "task_id": "MEM-001",
                    "memory_type": "architecture_decision",
                    "text": "Billing must use PaymentGateway only.",
                    "metadata": {
                        "tenant_id": "org_mil",
                        "workspace_id": "engineering",
                        "repo": "MIL",
                        "repo_id": "github:namlogan/MIL",
                        "user_id": "repo:github:namlogan/MIL",
                        "source_uri": "https://github.com/namlogan/MIL/pull/26",
                        "confidence": 0.82,
                        "status": "active",
                        "visibility": "repo",
                        "created_by": "agent",
                    },
                }
            )

        writeback = mem0_writeback.main(
            {
                "project": "MIL",
                "task_id": "MEM-001",
                "memory_type": "failure_pattern",
                "text": "CI token: ghp_123456789012345678901234567890123456 failed.",
                "metadata": {
                    "tenant_id": "org_mil",
                    "workspace_id": "engineering",
                    "repo": "MIL",
                    "repo_id": "github:namlogan/MIL",
                    "user_id": "repo:github:namlogan/MIL",
                    "source_uri": "https://github.com/namlogan/MIL/pull/26",
                    "confidence": 0.82,
                    "status": "active",
                    "visibility": "repo",
                    "created_by": "agent",
                },
            }
        )

        serialized = str(writeback)
        self.assertEqual(writeback["decision"], "MEMORY_WRITE_RECORDED")
        self.assertIn("[REDACTED_GITHUB_TOKEN]", serialized)
        self.assertNotIn("ghp_123456789012345678901234567890123456", serialized)

    def test_windmill_validator_self_test_succeeds(self) -> None:
        validator = load_module(
            "validate_windmill_project",
            "scripts/windmill/validate_windmill_project.py",
        )

        self.assertEqual(validator.validate(REPO_ROOT), [])

    def test_workspace_bootstrap_script_uses_environment_secrets(self) -> None:
        script = (REPO_ROOT / "scripts" / "windmill" / "bootstrap_workspace.sh").read_text(
            encoding="utf-8"
        )

        self.assertIn("WINDMILL_TOKEN is required", script)
        self.assertIn("wmill workspace add", script)
        self.assertIn('WMILL_SYNC_INCLUDE_PATTERN="${WMILL_SYNC_INCLUDE_PATTERN:-f/mil/**}"', script)
        self.assertIn('wmill sync push --dry-run --includes "${WMILL_SYNC_INCLUDE_PATTERN}"', script)
        self.assertNotIn("WINDMILL_TOKEN=", script)

    def test_public_webhook_relay_is_documented_and_scoped(self) -> None:
        relay = REPO_ROOT / "scripts" / "windmill" / "github_webhook_public_relay.py"
        relay_runner = (
            REPO_ROOT
            / "scripts"
            / "windmill"
            / "run_github_webhook_relay_from_windmill_secret.sh"
        )
        env_example = (REPO_ROOT / ".windmill" / "env.example").read_text(
            encoding="utf-8"
        )
        docs = (REPO_ROOT / "docs" / "windmill-setup.md").read_text(
            encoding="utf-8"
        )

        self.assertTrue(relay.exists())
        self.assertIn("MIL_GITHUB_WEBHOOK_SECRET=", env_example)
        self.assertIn("MIL_WEBHOOK_PUBLIC_ROUTE=/mil/github-webhook", env_example)
        self.assertIn("MIL_AUTO_DISPATCH_ENABLED=0", env_example)
        self.assertIn("MIL_AUTO_DISPATCH_REPO=/Users/mac/Documents/MIL", env_example)
        self.assertIn("github_webhook_public_relay.py", docs)
        self.assertIn("auto_dispatcher.py", docs)
        self.assertIn("accepts only `POST /mil/github-webhook`", docs)
        self.assertIn("Do not expose the full Windmill UI/API", docs)
        self.assertTrue(relay_runner.exists())

        runner = relay_runner.read_text(encoding="utf-8")
        self.assertIn("variable get", runner)
        self.assertIn("f/mil/github_webhook_secret", runner)
        self.assertIn('export MIL_GITHUB_WEBHOOK_SECRET="${secret}"', runner)
        self.assertIn("MIL_AUTO_DISPATCH_ENABLED", runner)
        self.assertIn("--auto-dispatch-repo", runner)
        self.assertIn('python3 "${REPO_ROOT}/scripts/windmill/github_webhook_public_relay.py"', runner)
        self.assertIn('exec "${args[@]}"', runner)
        self.assertNotIn("ghp_", runner)
        self.assertNotIn("sk-", runner)

    def test_cloudflare_named_tunnel_setup_is_scoped_to_relay(self) -> None:
        setup = load_module(
            "setup_cloudflare_named_tunnel",
            "scripts/windmill/setup_cloudflare_named_tunnel.py",
        )

        config = setup.build_config(
            tunnel_id="11111111-1111-1111-1111-111111111111",
            credentials_file=REPO_ROOT
            / ".windmill"
            / "runtime"
            / "cloudflared"
            / "mil-github-webhook.json",
            hostname="mil-webhook.example.com",
            relay_url="http://127.0.0.1:18090",
            metrics="127.0.0.1:20241",
        )

        self.assertIn("hostname: mil-webhook.example.com", config)
        self.assertIn("service: http://127.0.0.1:18090", config)
        self.assertIn("service: http_status:404", config)
        self.assertNotIn("localhost:8090", config)
        self.assertNotIn("/api/r/admins", config)
        self.assertEqual(setup.validate_relay_url("http://127.0.0.1:18090"), [])
        self.assertIn(
            "relay URL must not expose the full local Windmill port",
            setup.validate_relay_url("http://127.0.0.1:8090"),
        )

        env_example = (REPO_ROOT / ".windmill" / "env.example").read_text(
            encoding="utf-8"
        )
        docs = (REPO_ROOT / "docs" / "windmill-setup.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("MIL_CLOUDFLARE_TUNNEL_NAME=mil-github-webhook", env_example)
        self.assertIn("setup_cloudflare_named_tunnel.py", docs)

    def test_ngrok_static_endpoint_setup_is_scoped_to_relay(self) -> None:
        setup = load_module(
            "setup_ngrok_static_endpoint",
            "scripts/windmill/setup_ngrok_static_endpoint.py",
        )

        self.assertEqual(
            setup.normalize_domain("https://mil-demo.ngrok-free.app"),
            "mil-demo.ngrok-free.app",
        )
        self.assertEqual(setup.validate_domain("mil-demo.ngrok-free.app"), [])
        self.assertEqual(setup.validate_domain("mil-demo.ngrok-free.dev"), [])
        self.assertIn(
            "expected an ngrok-managed static/dev domain such as <name>.ngrok-free.app or <name>.ngrok-free.dev",
            setup.validate_domain("mil-demo.example.com"),
        )
        self.assertEqual(setup.validate_relay_url("http://127.0.0.1:18090"), [])
        self.assertIn(
            "relay URL must not expose the full local Windmill port",
            setup.validate_relay_url("http://127.0.0.1:8090"),
        )

        env_example = (REPO_ROOT / ".windmill" / "env.example").read_text(
            encoding="utf-8"
        )
        docs = (REPO_ROOT / "docs" / "windmill-setup.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("MIL_NGROK_DOMAIN=", env_example)
        self.assertIn("setup_ngrok_static_endpoint.py", docs)
        self.assertIn("ngrok-free.app", docs)
        self.assertIn("ngrok-free.dev", docs)


if __name__ == "__main__":
    unittest.main()
