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


class DeployProviderTests(unittest.TestCase):
    def setUp(self) -> None:
        self.provider = load_module("deploy_provider", "scripts/release/deploy_provider.py")

    def test_default_deploy_provider_is_manual_and_disabled(self) -> None:
        config = self.provider.load_config(REPO_ROOT / ".ai-factory/deploy-provider.json")
        result = self.provider.validate_config(config)

        self.assertTrue(result["ok"], result)
        self.assertFalse(config["enabled"])
        self.assertEqual(config["provider"], "manual")

    def test_command_provider_requires_command_arrays(self) -> None:
        config = {
            "enabled": True,
            "provider": "command",
            "environments": {
                "staging": {
                    "deploy": "npm run deploy && npm run smoke",
                    "smoke": ["python3", "--version"],
                }
            },
        }

        result = self.provider.validate_config(config)

        self.assertFalse(result["ok"])
        self.assertIn("environment staging deploy must be a command array", result["errors"])

    def test_builds_plan_without_secret_values(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "deploy-provider.json"
            path.write_text(
                json.dumps(
                    {
                        "enabled": True,
                        "provider": "command",
                        "required_secret_names": ["VERCEL_TOKEN"],
                        "environments": {
                            "staging": {
                                "deploy": ["vercel", "deploy", "--prebuilt"],
                                "smoke": ["python3", "scripts/smoke.py"],
                            }
                        },
                    }
                ),
                encoding="utf-8",
            )

            plan = self.provider.build_deploy_plan(
                self.provider.load_config(path),
                environment="staging",
            )

        self.assertTrue(plan["ok"], plan)
        self.assertEqual(plan["provider"], "command")
        self.assertEqual(plan["required_secret_names"], ["VERCEL_TOKEN"])
        self.assertNotIn("actual-token", json.dumps(plan))


if __name__ == "__main__":
    unittest.main()
