import json
import unittest
from pathlib import Path

from apps.flange_qc_v2.domain import ValidationError
from apps.flange_qc_v2.image_quality import evaluate_image_quality


REPO_ROOT = Path(__file__).resolve().parents[2]
QUALITY_SCHEMA = REPO_ROOT / "contracts/flange_qc_v2/image_quality/quality_gate.schema.json"


def quality_payload(**overrides):
    payload = {
        "frame_id": "frame-quality-001",
        "source_uri": "synthetic://flange-qc-v2/phase2/frame-quality-001",
        "captured_at": "2026-06-02T00:00:00Z",
        "brightness_score": 0.72,
        "sharpness_score": 0.81,
        "occlusion_score": 0.08,
        "source_ref": "https://github.com/namlogan/MIL/issues/83",
    }
    payload.update(overrides)
    return payload


class ImageQualitySchemaTests(unittest.TestCase):
    def test_quality_schema_exposes_normalized_scores_and_no_authority(self) -> None:
        schema = json.loads(QUALITY_SCHEMA.read_text(encoding="utf-8"))
        properties = schema["properties"]

        self.assertEqual(schema["title"], "FLANGE QC V2 Image Quality Gate")
        self.assertIn("decision", schema["required"])
        self.assertEqual(set(properties["decision"]["enum"]), {"PASS", "ASSIST", "BLOCKED"})
        for score_name in ("brightness_score", "sharpness_score", "occlusion_score"):
            score = properties["quality_scores"]["properties"][score_name]
            self.assertEqual(score["minimum"], 0)
            self.assertEqual(score["maximum"], 1)
        self.assertEqual(properties["production_authority"]["const"], False)


class ImageQualityGateTests(unittest.TestCase):
    def test_passing_quality_evidence_is_shadow_only(self) -> None:
        result = evaluate_image_quality(quality_payload())

        payload = result.to_payload()

        self.assertEqual(result.decision, "PASS")
        self.assertEqual(result.reason_codes, ())
        self.assertTrue(result.shadow_mode)
        self.assertFalse(result.production_authority)
        self.assertEqual(
            result.authority_blockers,
            ("IMAGE_QUALITY_APPROVAL_REQUIRED", "PRODUCTION_APPROVAL_REQUIRED"),
        )
        self.assertEqual(payload["contract_version"], "image_quality.gate.v1")
        self.assertEqual(payload["evidence"]["frame_id"], "frame-quality-001")
        self.assertEqual(payload["thresholds"]["brightness_min"], 0.35)

    def test_dark_or_blurry_quality_fails_closed(self) -> None:
        result = evaluate_image_quality(
            quality_payload(brightness_score=0.2, sharpness_score=0.25)
        )

        self.assertEqual(result.decision, "BLOCKED")
        self.assertEqual(result.reason_codes, ("IMAGE_TOO_DARK", "IMAGE_TOO_BLURRY"))
        self.assertFalse(result.production_authority)

    def test_moderate_occlusion_requests_assist(self) -> None:
        result = evaluate_image_quality(quality_payload(occlusion_score=0.3))

        self.assertEqual(result.decision, "ASSIST")
        self.assertEqual(result.reason_codes, ("IMAGE_OCCLUSION_REVIEW_REQUIRED",))
        self.assertFalse(result.production_authority)

    def test_severe_occlusion_blocks(self) -> None:
        result = evaluate_image_quality(quality_payload(occlusion_score=0.6))

        self.assertEqual(result.decision, "BLOCKED")
        self.assertEqual(result.reason_codes, ("IMAGE_OCCLUSION_BLOCKED",))
        self.assertFalse(result.production_authority)

    def test_missing_quality_score_is_rejected_explicitly(self) -> None:
        payload = quality_payload()
        del payload["brightness_score"]

        with self.assertRaisesRegex(ValidationError, "brightness_score is required"):
            evaluate_image_quality(payload)

    def test_score_outside_unit_interval_is_rejected_explicitly(self) -> None:
        with self.assertRaisesRegex(ValidationError, "sharpness_score must be between 0 and 1"):
            evaluate_image_quality(quality_payload(sharpness_score=1.2))

    def test_source_uri_cannot_point_to_raw_media_path(self) -> None:
        with self.assertRaisesRegex(ValidationError, "source_uri must use synthetic:// or replay://"):
            evaluate_image_quality(quality_payload(source_uri="file:///factory/raw/frame.jpg"))


if __name__ == "__main__":
    unittest.main()
