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
            "issue_to_plan",
            "plan_to_pr",
            "pr_quality_gate",
            "fix_ci_or_review",
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
            "issue_to_plan",
            "plan_to_pr",
            "pr_quality_gate",
            "fix_ci_or_review",
            "auggie_supervised_advisory",
            "github_webhook_router",
        ]:
            with self.subTest(name=name):
                script = (REPO_ROOT / "f" / "mil" / f"{name}.py").read_text(
                    encoding="utf-8"
                )

                self.assertIn("from f.mil.flow_contract import", script)
                self.assertNotIn("from flow_contract import", script)

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
        self.assertEqual(result["agent_calls"][0]["agent"], "windmill")
        self.assertEqual(result["agent_calls"][0]["action"], "dispatch_coding_agent")

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
        self.assertIn("github_webhook_public_relay.py", docs)
        self.assertIn("accepts only `POST /mil/github-webhook`", docs)
        self.assertIn("Do not expose the full Windmill UI/API", docs)
        self.assertTrue(relay_runner.exists())

        runner = relay_runner.read_text(encoding="utf-8")
        self.assertIn("variable get", runner)
        self.assertIn("f/mil/github_webhook_secret", runner)
        self.assertIn('export MIL_GITHUB_WEBHOOK_SECRET="${secret}"', runner)
        self.assertIn("exec python3", runner)
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
        self.assertIn(
            "expected an ngrok-managed static/dev domain such as <name>.ngrok-free.app",
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


if __name__ == "__main__":
    unittest.main()
