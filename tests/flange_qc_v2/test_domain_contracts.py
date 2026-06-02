import json
import unittest
from pathlib import Path

from apps.flange_qc_v2.domain import (
    BoundingBox,
    DetectorObservation,
    InspectionMeasurements,
    InspectionSnapshot,
    SubsystemHealth,
    ValidationError,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
SNAPSHOT_SCHEMA = REPO_ROOT / "contracts/flange_qc_v2/websocket/inspection_snapshot.schema.json"


class DomainPayloadTests(unittest.TestCase):
    def test_bootstrap_snapshot_serializes_blocked_payload_for_unknown_product(self) -> None:
        snapshot = InspectionSnapshot.bootstrap_blocked(
            inspection_id="insp-001",
            product_code="UNKNOWN",
            reason_codes=["product_specs_unapproved"],
        )

        payload = snapshot.to_payload()

        self.assertEqual(payload["event_type"], "inspection.snapshot")
        self.assertEqual(payload["decision"], "BLOCKED")
        self.assertEqual(payload["phase"], "BOOTSTRAP")
        self.assertEqual(payload["product"]["code"], "UNKNOWN")
        self.assertEqual(payload["measurements"]["length_points"], [])
        self.assertEqual(payload["phase_results"], [])
        self.assertIn("product_specs_unapproved", payload["reason_codes"])

    def test_detector_observation_rejects_bbox_values_outside_unit_interval(self) -> None:
        with self.assertRaisesRegex(ValidationError, "bbox values must be between 0 and 1"):
            DetectorObservation(
                label="flange",
                confidence=0.91,
                bbox=BoundingBox(x=-0.1, y=0.1, width=0.2, height=0.3),
            )

    def test_snapshot_parser_rejects_unknown_decision_state(self) -> None:
        payload = InspectionSnapshot.bootstrap_blocked(
            inspection_id="insp-002",
            product_code="UNKNOWN",
            reason_codes=["product_specs_unapproved"],
        ).to_payload()
        payload["decision"] = "MAYBE"

        with self.assertRaisesRegex(ValidationError, "unknown decision"):
            InspectionSnapshot.from_payload(payload)

    def test_measurements_require_expected_phase_two_point_counts(self) -> None:
        with self.assertRaisesRegex(ValidationError, "length_points requires 3 values"):
            InspectionMeasurements(
                length_points=[1.0, 1.1],
                width_points=[2.0, 2.1, 2.2],
                diagonals=[3.0, 3.1],
                unit="inch",
            )

    def test_subsystem_health_domain_model_keeps_bootstrap_states_explicit(self) -> None:
        payload = SubsystemHealth.bootstrap().to_payload()

        self.assertEqual(payload["camera"], "unavailable")
        self.assertEqual(payload["model"], "unavailable")
        self.assertEqual(payload["product_specs"], "draft_requires_qc_owner_approval")
        self.assertEqual(payload["sop_decision_engine"], "not_implemented")


class WebSocketContractSchemaTests(unittest.TestCase):
    def test_inspection_snapshot_schema_defines_hmi_payload_contract(self) -> None:
        schema = json.loads(SNAPSHOT_SCHEMA.read_text(encoding="utf-8"))
        properties = schema["properties"]
        observation = properties["observations"]["items"]["properties"]

        self.assertEqual(schema["title"], "FLANGE QC V2 WebSocket Inspection Snapshot")
        self.assertIn("event_type", schema["required"])
        self.assertIn("decision", schema["required"])
        self.assertIn("phase_results", schema["required"])
        self.assertEqual(properties["decision"]["enum"], ["PASS", "NG", "BLOCKED", "NOT_EVALUATED", "ASSIST"])
        phase_result = properties["phase_results"]["items"]
        self.assertIn("phase", phase_result["required"])
        self.assertIn("rule_results", phase_result["required"])
        self.assertIn("authority_blockers", phase_result["required"])
        self.assertEqual(observation["bbox"]["items"]["minimum"], 0)
        self.assertEqual(observation["bbox"]["items"]["maximum"], 1)


if __name__ == "__main__":
    unittest.main()
