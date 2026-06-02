import json
import tempfile
import unittest
from pathlib import Path

from apps.flange_qc_v2.domain import ValidationError
from apps.flange_qc_v2.model_artifact import ModelArtifactManifest, load_model_artifact_manifest


REPO_ROOT = Path(__file__).resolve().parents[2]
MANIFEST_SCHEMA = REPO_ROOT / "contracts/flange_qc_v2/model/model_artifact_manifest.schema.json"


def valid_manifest_payload(**overrides):
    payload = {
        "contract_version": "model.artifact.v1",
        "model_ref": "registry://flange-qc-v2/detector/punch-mark/2026-06-02",
        "artifact_version": "detector-shadow-2026-06-02",
        "model_family": "detector",
        "task": "flange_qc_v2.detector",
        "labels": ["punch_mark", "corner_mark"],
        "output_schema": "contracts/flange_qc_v2/detector/detector_result.schema.json",
        "eval_report_ref": "docs/project/flange_qc_v2/eval/detector-shadow-2026-06-02.json",
        "artifact_digest": "sha256:" + ("a" * 64),
        "approval_status": "candidate",
        "production_authority": False,
        "shadow_mode": True,
        "source_ref": "https://github.com/namlogan/MIL/issues/99",
    }
    payload.update(overrides)
    return payload


class ModelArtifactManifestSchemaTests(unittest.TestCase):
    def test_schema_documents_shadow_only_manifest_contract(self) -> None:
        schema = json.loads(MANIFEST_SCHEMA.read_text(encoding="utf-8"))

        self.assertEqual(schema["title"], "FLANGE QC V2 Model Artifact Manifest")
        self.assertEqual(schema["properties"]["contract_version"]["const"], "model.artifact.v1")
        self.assertEqual(schema["properties"]["production_authority"]["const"], False)
        self.assertEqual(schema["properties"]["shadow_mode"]["const"], True)
        self.assertIn("source_ref", schema["required"])


class ModelArtifactManifestTests(unittest.TestCase):
    def test_valid_manifest_loads_without_model_deserialization(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            manifest_path = Path(tmpdir) / "detector_manifest.json"
            manifest_path.write_text(json.dumps(valid_manifest_payload()), encoding="utf-8")

            manifest = load_model_artifact_manifest(manifest_path)

        self.assertIsInstance(manifest, ModelArtifactManifest)
        self.assertEqual(manifest.contract_version, "model.artifact.v1")
        self.assertEqual(manifest.model_ref, "registry://flange-qc-v2/detector/punch-mark/2026-06-02")
        self.assertEqual(manifest.labels, ("punch_mark", "corner_mark"))
        self.assertFalse(manifest.production_authority)
        self.assertTrue(manifest.shadow_mode)

    def test_loader_rejects_raw_weight_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            weights_path = Path(tmpdir) / "detector.onnx"
            weights_path.write_bytes(b"raw weights")

            with self.assertRaisesRegex(ValidationError, "manifest path must point to a JSON file"):
                load_model_artifact_manifest(weights_path)

    def test_manifest_rejects_unknown_contract_version(self) -> None:
        with self.assertRaisesRegex(ValidationError, "unknown model artifact contract_version"):
            ModelArtifactManifest.from_payload(valid_manifest_payload(contract_version="model.artifact.v999"))

    def test_manifest_rejects_production_authority(self) -> None:
        with self.assertRaisesRegex(ValidationError, "model artifact cannot approve production authority"):
            ModelArtifactManifest.from_payload(valid_manifest_payload(production_authority=True))

    def test_manifest_rejects_unsafe_relative_paths(self) -> None:
        with self.assertRaisesRegex(ValidationError, "eval_report_ref must be a safe repository-relative path"):
            ModelArtifactManifest.from_payload(valid_manifest_payload(eval_report_ref="../private/eval.json"))

    def test_manifest_rejects_absolute_paths(self) -> None:
        with self.assertRaisesRegex(ValidationError, "output_schema must be a safe repository-relative path"):
            ModelArtifactManifest.from_payload(valid_manifest_payload(output_schema="/tmp/schema.json"))


if __name__ == "__main__":
    unittest.main()
