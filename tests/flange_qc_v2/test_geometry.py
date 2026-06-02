import json
import unittest
from pathlib import Path

from apps.flange_qc_v2.domain import ValidationError
from apps.flange_qc_v2.geometry import resolve_geometry_measurements


REPO_ROOT = Path(__file__).resolve().parents[2]
MEASUREMENT_SCHEMA = REPO_ROOT / "contracts/flange_qc_v2/geometry/measurement_set.schema.json"


class GeometryMeasurementContractTests(unittest.TestCase):
    def test_complete_geometry_payload_exposes_deviation_without_production_authority(self) -> None:
        result = resolve_geometry_measurements(
            {
                "length_points": [10.99, 11.0, 11.01],
                "width_points": [20.0, 20.02, 19.98],
                "diagonals": [22.50, 22.75],
                "unit": "inch",
            }
        )

        payload = result.to_payload()

        self.assertEqual(result.decision, "BLOCKED")
        self.assertEqual(result.reason_codes, ("SOP_TOLERANCE_APPROVAL_MISSING",))
        self.assertFalse(result.production_authority)
        self.assertAlmostEqual(result.diagonal_deviation, 0.25)
        self.assertEqual(payload["contract_version"], "geometry.measurement_set.v1")
        self.assertEqual(payload["measurements"]["length_points"], [10.99, 11.0, 11.01])
        self.assertNotIn(payload["decision"], ("PASS", "NG"))

    def test_incomplete_geometry_payload_fails_closed_with_counts_evidence(self) -> None:
        result = resolve_geometry_measurements(
            {
                "length_points": [10.99, 11.0],
                "width_points": [20.0, 20.02, 19.98],
                "diagonals": [22.50, 22.75],
                "unit": "inch",
            }
        )

        self.assertEqual(result.decision, "BLOCKED")
        self.assertEqual(result.reason_codes, ("MEASUREMENTS_INCOMPLETE",))
        self.assertFalse(result.production_authority)
        self.assertIsNone(result.diagonal_deviation)
        self.assertEqual(result.received_counts["length_points"], 2)
        self.assertEqual(result.expected_counts["length_points"], 3)

    def test_unknown_measurement_unit_is_rejected_explicitly(self) -> None:
        with self.assertRaisesRegex(ValidationError, "unknown measurement unit"):
            resolve_geometry_measurements(
                {
                    "length_points": [10.99, 11.0, 11.01],
                    "width_points": [20.0, 20.02, 19.98],
                    "diagonals": [22.50, 22.75],
                    "unit": "cm",
                }
            )


class GeometryMeasurementSchemaTests(unittest.TestCase):
    def test_measurement_set_schema_requires_exact_geometry_point_counts(self) -> None:
        schema = json.loads(MEASUREMENT_SCHEMA.read_text(encoding="utf-8"))
        measurements = schema["properties"]["measurements"]["properties"]

        self.assertEqual(schema["title"], "FLANGE QC V2 Geometry Measurement Set")
        self.assertEqual(measurements["length_points"]["minItems"], 3)
        self.assertEqual(measurements["length_points"]["maxItems"], 3)
        self.assertEqual(measurements["width_points"]["minItems"], 3)
        self.assertEqual(measurements["width_points"]["maxItems"], 3)
        self.assertEqual(measurements["diagonals"]["minItems"], 2)
        self.assertEqual(measurements["diagonals"]["maxItems"], 2)
        self.assertEqual(schema["properties"]["production_authority"]["const"], False)


if __name__ == "__main__":
    unittest.main()
