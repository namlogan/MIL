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

    def test_default_product_ci_config_is_versioned_and_disabled_until_app_exists(self) -> None:
        config = self.product_ci.load_config(REPO_ROOT / ".ai-factory/product-ci.json")

        self.assertFalse(config["enabled"])
        self.assertEqual(config["checks"], [])

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


if __name__ == "__main__":
    unittest.main()
