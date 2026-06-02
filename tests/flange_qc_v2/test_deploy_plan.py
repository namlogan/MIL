from __future__ import annotations

import copy
import importlib.util
import json
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


def load_module(name: str, relative_path: str):
    module_path = REPO_ROOT / relative_path
    spec = importlib.util.spec_from_file_location(name, module_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class FlangeQCDeployPlanTests(unittest.TestCase):
    def setUp(self) -> None:
        self.validator = load_module(
            "validate_flange_qc_v2_deploy_plan",
            "scripts/deploy/validate_flange_qc_v2_deploy_plan.py",
        )
        self.plan = self.validator.load_plan(REPO_ROOT / "deploy/flange_qc_v2/deploy_plan.json")

    def test_checked_in_plan_is_disabled_shadow_scaffold(self) -> None:
        result = self.validator.validate_plan(self.plan)

        self.assertTrue(result["ok"], result)
        self.assertEqual(result["status"], "scaffold_only")
        self.assertEqual(result["deployment_authority"], "none")
        self.assertFalse(result["production_deploy_enabled"])
        self.assertEqual(result["required_secret_names"], [])
        self.assertEqual(
            {environment["name"] for environment in self.plan["environments"]},
            {"local_replay", "jetson_shadow", "rtx_shadow"},
        )

    def test_rejects_production_deploy_enabled(self) -> None:
        plan = copy.deepcopy(self.plan)
        plan["production_deploy_enabled"] = True

        result = self.validator.validate_plan(plan)

        self.assertFalse(result["ok"])
        self.assertIn("production_deploy_enabled must remain false", result["errors"])

    def test_rejects_live_camera_or_raw_media_enabled(self) -> None:
        for field in ["live_camera_enabled", "raw_media_enabled"]:
            with self.subTest(field=field):
                plan = copy.deepcopy(self.plan)
                plan[field] = True

                result = self.validator.validate_plan(plan)

                self.assertFalse(result["ok"])
                self.assertIn(f"{field} must remain false", result["errors"])

    def test_rejects_secret_like_values(self) -> None:
        plan = copy.deepcopy(self.plan)
        plan["notes"] = "token: ghp_123456789012345678901234567890123456"

        result = self.validator.validate_plan(plan)

        self.assertFalse(result["ok"])
        self.assertIn("secret-like value found at notes", result["errors"])

    def test_rejects_executable_deploy_commands(self) -> None:
        plan = copy.deepcopy(self.plan)
        plan["environments"][1]["commands"]["deploy"] = ["bash", "deploy.sh"]

        result = self.validator.validate_plan(plan)

        self.assertFalse(result["ok"])
        self.assertIn(
            "environment jetson_shadow command deploy is not allowed in scaffold",
            result["errors"],
        )

    def test_cli_emits_json_validation_result(self) -> None:
        result = self.validator.main(
            ["--plan", str(REPO_ROOT / "deploy/flange_qc_v2/deploy_plan.json")]
        )

        self.assertEqual(result, 0)


if __name__ == "__main__":
    unittest.main()
