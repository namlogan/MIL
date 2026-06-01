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


class Mem0LibraryPreflightTests(unittest.TestCase):
    def setUp(self) -> None:
        self.preflight = load_module(
            "check_mem0_library",
            "scripts/agent-memory/check_mem0_library.py",
        )

    def test_python_library_mode_requires_package_and_llm_config(self) -> None:
        result = self.preflight.check_library(
            runtime="python",
            env={},
            python_module_available=lambda module: module == "mem0",
        )

        self.assertTrue(result["ok"], result)
        self.assertEqual(result["runtime"], "python")
        self.assertEqual(result["store"]["history"], "~/.mem0/history.db")
        self.assertEqual(result["store"]["vector"], "/tmp/qdrant")
        self.assertIn("No external LLM provider is configured", result["warnings"][0])

    def test_library_mode_requires_llm_only_when_explicitly_requested(self) -> None:
        result = self.preflight.check_library(
            runtime="python",
            env={},
            python_module_available=lambda module: module == "mem0",
            require_llm=True,
        )

        self.assertFalse(result["ok"])
        self.assertIn(
            "OPENAI_API_KEY, OLLAMA_HOST, or another explicit Mem0 LLM provider is required.",
            result["errors"],
        )

    def test_python_library_mode_can_use_ollama_instead_of_openai(self) -> None:
        result = self.preflight.check_library(
            runtime="python",
            env={"OLLAMA_HOST": "http://127.0.0.1:11434"},
            python_module_available=lambda module: module == "mem0",
        )

        self.assertTrue(result["ok"], result)
        self.assertEqual(result["llm_provider"], "ollama")

    def test_node_library_mode_detects_mem0ai_dependency(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "package.json").write_text(
                json.dumps({"dependencies": {"mem0ai": "^3.0.0"}}),
                encoding="utf-8",
            )

            result = self.preflight.check_library(
                runtime="node",
                repo_root=root,
                env={"OPENAI_API_KEY": "secret-openai-key"},
            )

        self.assertTrue(result["ok"], result)
        self.assertEqual(result["runtime"], "node")
        self.assertEqual(result["package"], "mem0ai")

    def test_missing_library_reports_actionable_install_command(self) -> None:
        result = self.preflight.check_library(
            runtime="python",
            env={"OPENAI_API_KEY": "secret-openai-key"},
            python_module_available=lambda module: False,
        )

        self.assertFalse(result["ok"])
        self.assertIn("pip install mem0ai", result["install_command"])


if __name__ == "__main__":
    unittest.main()
