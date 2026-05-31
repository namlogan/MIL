from __future__ import annotations

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


check_augment_config = load_module(
    "check_augment_config",
    "scripts/agent-flow/check_augment_config.py",
)


class AugmentConfigTests(unittest.TestCase):
    def test_valid_env_file_passes_without_exposing_secret(self) -> None:
        session = {
            "accessToken": "secret-token",
            "tenantURL": "https://e6.api.augmentcode.com/",
            "scopes": ["read", "write"],
        }
        with tempfile.TemporaryDirectory() as tmpdir:
            env_path = Path(tmpdir) / ".env.local"
            env_path.write_text(
                "\n".join(
                    [
                        "AUGMENT_MCP_TOKEN=secret-token",
                        "AUGMENT_API_TOKEN=secret-token",
                        "AUGMENT_API_URL=https://e6.api.augmentcode.com/",
                        "AUGMENT_SESSION_AUTH=" + json.dumps(session, separators=(",", ":")),
                    ]
                ),
                encoding="utf-8",
            )

            result = check_augment_config.check_config(env_file=env_path)

        self.assertTrue(result["ok"])
        serialized = json.dumps(result)
        self.assertNotIn("secret-token", serialized)
        self.assertEqual(
            result["checks"]["augment_session_auth"]["tenant_url"],
            "https://e6.api.augmentcode.com/",
        )

    def test_missing_required_values_fails(self) -> None:
        result = check_augment_config.check_config(env={}, env_file=None)

        self.assertFalse(result["ok"])
        self.assertFalse(result["checks"]["augment_mcp_token"]["present"])
        self.assertFalse(result["checks"]["augment_session_auth"]["present"])

    def test_mil_mcp_runtime_checker_is_documented(self) -> None:
        checker = REPO_ROOT / "scripts" / "agent-flow" / "check_mil_mcp_runtime.py"
        docs = (REPO_ROOT / "docs" / "augment-setup.md").read_text(encoding="utf-8")

        self.assertTrue(checker.exists())
        self.assertIn("check_mil_mcp_runtime.py --mcp-smoke", docs)
        self.assertIn("mil_workspace_indexed=true", docs)
        self.assertIn("not another repo", docs)


if __name__ == "__main__":
    unittest.main()
