from __future__ import annotations

import importlib.util
import json
import tarfile
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


class AgentFactoryBackupTests(unittest.TestCase):
    def setUp(self) -> None:
        self.backup = load_module(
            "create_agent_factory_backup",
            "scripts/portable/create_agent_factory_backup.py",
        )

    def test_selects_tracked_framework_files_without_runtime_artifacts(self) -> None:
        files = self.backup.select_backup_files(REPO_ROOT)

        self.assertIn("AGENTS.md", files)
        self.assertIn(".ai-factory/config.yaml", files)
        self.assertIn("f/mil/github_webhook_router.py", files)
        self.assertIn("docs/agent-factory-workflow-and-starter.md", files)
        self.assertNotIn(".windmill/runtime/local/.env", files)
        self.assertFalse(any("__pycache__" in path for path in files))
        self.assertFalse(any(path.startswith(".ai-factory/queue/") for path in files))

    def test_creates_archive_bundle_and_manifest_without_secret_values(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            result = self.backup.create_backup(
                repo_root=REPO_ROOT,
                output_dir=Path(tmpdir),
                project_id="MIL",
                archive_prefix="test-agent-factory",
            )

            archive_path = Path(result["archive_path"])
            bundle_path = Path(result["bundle_path"])
            manifest_path = Path(result["manifest_path"])

            self.assertTrue(archive_path.exists())
            self.assertTrue(bundle_path.exists())
            self.assertTrue(manifest_path.exists())

            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            self.assertEqual(manifest["project_id"], "MIL")
            self.assertIn("docs/agent-factory-workflow-and-starter.md", manifest["files"])
            self.assertIn("f/mil/github_webhook_router.py", manifest["files"])
            self.assertNotIn(".windmill/runtime/local/.env", manifest["files"])
            serialized = json.dumps(manifest)
            self.assertIn("Windmill f/mil/github_status_token", serialized)
            self.assertIn("Local JSONL runtime memory is excluded", serialized)
            self.assertIn("different tenant_id, repo_id, project_id", serialized)
            for secret_shape in ("ghp_", "github_pat_", "sk-", "accessToken"):
                self.assertNotIn(secret_shape, serialized)

            with tarfile.open(archive_path, "r:gz") as archive:
                names = archive.getnames()

            archive_root = manifest["archive_root"]
            self.assertIn(f"{archive_root}/AGENTS.md", names)
            self.assertIn(
                f"{archive_root}/docs/agent-factory-workflow-and-starter.md",
                names,
            )
            self.assertNotIn(f"{archive_root}/.windmill/runtime/local/.env", names)


if __name__ == "__main__":
    unittest.main()
