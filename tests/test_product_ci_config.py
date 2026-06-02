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


class ProductCIConfigTests(unittest.TestCase):
    def setUp(self) -> None:
        self.product_ci = load_module(
            "run_product_checks",
            "scripts/product-ci/run_product_checks.py",
        )

    def test_product_ci_config_is_enabled_for_flange_app_skeleton(self) -> None:
        config = self.product_ci.load_config(REPO_ROOT / ".ai-factory/product-ci.json")

        self.assertTrue(config["enabled"])
        self.assertEqual(
            [check["name"] for check in config["checks"]],
            [
                "flange-qc-v2-compile",
                "flange-qc-v2-unit",
                "flange-qc-v2-health-smoke",
                "flange-qc-v2-deploy-plan",
            ],
        )
        for check in config["checks"]:
            self.assertTrue(check["required"])
            self.assertTrue(all(part != "pytest" for part in check["command"]))

    def test_product_ci_stack_profiles_are_versioned(self) -> None:
        profiles = self.product_ci.load_profiles(REPO_ROOT / ".ai-factory/product-ci.profiles.json")

        self.assertIn("python-unittest", profiles["profiles"])
        self.assertIn("node-pnpm", profiles["profiles"])
        self.assertTrue(
            self.product_ci.validate_config(
                {
                    "enabled": True,
                    "checks": profiles["profiles"]["python-unittest"]["checks"],
                }
            )["ok"]
        )

    def test_validates_enabled_product_checks(self) -> None:
        config = {
            "enabled": True,
            "checks": [
                {"name": "unit", "command": ["python3", "-m", "unittest"], "required": True}
            ],
        }

        result = self.product_ci.validate_config(config)

        self.assertTrue(result["ok"], result)

    def test_rejects_enabled_product_ci_without_checks(self) -> None:
        result = self.product_ci.validate_config({"enabled": True, "checks": []})

        self.assertFalse(result["ok"])
        self.assertIn("enabled product CI requires at least one check", result["errors"])

    def test_load_config_rejects_shell_string_commands(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "product-ci.json"
            path.write_text(
                json.dumps(
                    {
                        "enabled": True,
                        "checks": [
                            {"name": "unsafe", "command": "pytest && deploy", "required": True}
                        ],
                    }
                ),
                encoding="utf-8",
            )

            config = self.product_ci.load_config(path)
            result = self.product_ci.validate_config(config)

        self.assertFalse(result["ok"])
        self.assertIn("check unsafe command must be a non-empty list", result["errors"])

    def test_applies_named_stack_profile_when_checks_are_not_inline(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            config_path = root / "product-ci.json"
            profiles_path = root / "product-ci.profiles.json"
            config_path.write_text(
                json.dumps({"enabled": True, "profile": "python-unittest", "checks": []}),
                encoding="utf-8",
            )
            profiles_path.write_text(
                json.dumps(
                    {
                        "profiles": {
                            "python-unittest": {
                                "checks": [
                                    {
                                        "name": "unit",
                                        "command": ["python3", "-m", "unittest"],
                                        "required": True,
                                    }
                                ]
                            }
                        }
                    }
                ),
                encoding="utf-8",
            )

            config = self.product_ci.load_effective_config(config_path, profiles_path)

        self.assertTrue(config["enabled"])
        self.assertEqual(config["checks"][0]["name"], "unit")

    def test_self_test_does_not_require_repo_product_ci_to_be_disabled(self) -> None:
        self.assertTrue(self.product_ci.load_config(REPO_ROOT / ".ai-factory/product-ci.json")["enabled"])

        self.product_ci.run_self_test()


if __name__ == "__main__":
    unittest.main()
