from __future__ import annotations

import importlib.util
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


class ProjectIntakeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.intake = load_module(
            "validate_project_intake",
            "scripts/project-intake/validate_project_intake.py",
        )

    def test_required_project_templates_are_versioned(self) -> None:
        for relative_path in self.intake.REQUIRED_TEMPLATE_PATHS:
            with self.subTest(path=relative_path):
                self.assertTrue((REPO_ROOT / relative_path).exists())

    def test_validator_accepts_complete_project_intake(self) -> None:
        result = self.intake.validate_project_intake(REPO_ROOT)

        self.assertTrue(result["ok"], result)
        self.assertIn("docs/templates/project/PRD.md", result["checked_templates"])
        self.assertIn(".ai-factory/DESCRIPTION.md", result["checked_active_docs"])

    def test_validator_rejects_missing_active_project_docs(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / ".ai-factory").mkdir()
            (root / "docs/project").mkdir(parents=True)
            (root / ".ai-factory/DESCRIPTION.md").write_text("# Description\n", encoding="utf-8")

            result = self.intake.validate_project_intake(root)

        self.assertFalse(result["ok"])
        self.assertIn(".ai-factory/ARCHITECTURE.md", result["missing_active_docs"])
        self.assertIn("docs/project/PRD.md", result["missing_active_docs"])


if __name__ == "__main__":
    unittest.main()
