import json
import unittest
from pathlib import Path

from apps.flange_qc_v2.detector import DetectorRequest, DetectorResult, StubDetectorAdapter
from apps.flange_qc_v2.domain import ValidationError


REPO_ROOT = Path(__file__).resolve().parents[2]
DETECTOR_SCHEMA = REPO_ROOT / "contracts/flange_qc_v2/detector/detector_result.schema.json"


def detector_request_payload(**overrides):
    payload = {
        "frame_id": "frame-detector-001",
        "source_uri": "synthetic://flange-qc-v2/phase3/frame-detector-001",
        "captured_at": "2026-06-02T00:00:00Z",
        "source_ref": "https://github.com/namlogan/MIL/issues/85",
    }
    payload.update(overrides)
    return payload


class DetectorAdapterSchemaTests(unittest.TestCase):
    def test_detector_result_schema_keeps_observations_non_authoritative(self) -> None:
        schema = json.loads(DETECTOR_SCHEMA.read_text(encoding="utf-8"))
        properties = schema["properties"]
        observation = properties["observations"]["items"]["properties"]

        self.assertEqual(schema["title"], "FLANGE QC V2 Detector Result")
        self.assertEqual(set(properties["decision"]["enum"]), {"NOT_EVALUATED", "ASSIST", "BLOCKED"})
        self.assertNotIn("PASS", properties["decision"]["enum"])
        self.assertNotIn("NG", properties["decision"]["enum"])
        self.assertEqual(observation["bbox"]["items"]["minimum"], 0)
        self.assertEqual(observation["bbox"]["items"]["maximum"], 1)
        self.assertEqual(properties["production_authority"]["const"], False)


class StubDetectorAdapterTests(unittest.TestCase):
    def test_stub_detector_returns_not_evaluated_when_model_is_missing(self) -> None:
        request = DetectorRequest.from_payload(detector_request_payload())
        result = StubDetectorAdapter().detect(request)

        payload = result.to_payload()

        self.assertEqual(result.decision, "NOT_EVALUATED")
        self.assertEqual(result.reason_codes, ("MODEL_MISSING",))
        self.assertEqual(result.observations, ())
        self.assertFalse(result.production_authority)
        self.assertEqual(result.authority_blockers, ("MODEL_APPROVAL_REQUIRED", "PRODUCTION_APPROVAL_REQUIRED"))
        self.assertEqual(payload["contract_version"], "detector.result.v1")
        self.assertEqual(payload["request"]["frame_id"], "frame-detector-001")

    def test_stub_detector_returns_validated_observations_for_review_only(self) -> None:
        request = DetectorRequest.from_payload(detector_request_payload())
        adapter = StubDetectorAdapter(
            adapter_id="stub-review",
            model_ref="stub://detector/no-model",
            observations=[
                {
                    "label": "punch_mark",
                    "confidence": 0.42,
                    "bbox": [0.1, 0.2, 0.3, 0.4],
                    "model_ref": "stub://detector/no-model",
                    "evidence_ref": "synthetic://flange-qc-v2/evidence/punch-mark",
                }
            ],
        )

        result = adapter.detect(request)

        self.assertEqual(result.decision, "ASSIST")
        self.assertEqual(result.reason_codes, ("MODEL_REVIEW_REQUIRED",))
        self.assertEqual(len(result.observations), 1)
        self.assertEqual(result.observations[0].label, "punch_mark")
        self.assertFalse(result.production_authority)

    def test_stub_detector_rejects_invalid_observation_bbox(self) -> None:
        request = DetectorRequest.from_payload(detector_request_payload())
        adapter = StubDetectorAdapter(
            observations=[
                {
                    "label": "bad_bbox",
                    "confidence": 0.5,
                    "bbox": [0.1, 0.2, 1.5, 0.4],
                }
            ],
        )

        with self.assertRaisesRegex(ValidationError, "bbox values must be between 0 and 1"):
            adapter.detect(request)

    def test_detector_request_rejects_raw_media_source_uri(self) -> None:
        with self.assertRaisesRegex(ValidationError, "source_uri must use synthetic:// or replay://"):
            DetectorRequest.from_payload(
                detector_request_payload(source_uri="file:///factory/raw/frame.jpg")
            )

    def test_detector_result_cannot_emit_pass_or_ng(self) -> None:
        request = DetectorRequest.from_payload(detector_request_payload())

        with self.assertRaisesRegex(ValidationError, "detector result cannot emit decision"):
            DetectorResult(
                adapter_id="stub",
                request=request,
                decision="PASS",
                reason_codes=(),
                observations=(),
            )


if __name__ == "__main__":
    unittest.main()
