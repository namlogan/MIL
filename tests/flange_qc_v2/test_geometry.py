import json
import unittest
from pathlib import Path

from apps.flange_qc_v2.calibration import CalibrationConfig
from apps.flange_qc_v2.decision_engine import evaluate_phase_one_measurements
from apps.flange_qc_v2.domain import ValidationError
from apps.flange_qc_v2.geometry import resolve_geometry_from_boundary, resolve_geometry_measurements
from apps.flange_qc_v2.product_specs import ProductSpecResolution


REPO_ROOT = Path(__file__).resolve().parents[2]
MEASUREMENT_SCHEMA = REPO_ROOT / "contracts/flange_qc_v2/geometry/measurement_set.schema.json"


def calibration_with_scale(inch_per_pixel: float = 0.5) -> CalibrationConfig:
    return CalibrationConfig(
        schema_version=1,
        status="synthetic",
        approved_for_production=False,
        source_ref="test-calibration",
        camera={"mount": "top_down_90_degrees"},
        lighting={"layout": "four_led_bars"},
        geometry={
            "source_units": "pixel",
            "inch_per_pixel": inch_per_pixel,
            "method": "top_down_boundary_corners_shadow_v1",
        },
        production_authority=False,
        decision="BLOCKED",
        reason_codes=["CALIBRATION_MISSING"],
    )


def approved_calibration_with_scale(inch_per_pixel: float = 0.5) -> CalibrationConfig:
    return CalibrationConfig(
        schema_version=1,
        status="approved",
        approved_for_production=True,
        source_ref="test-calibration",
        camera={"mount": "top_down_90_degrees"},
        lighting={"layout": "four_led_bars"},
        geometry={
            "source_units": "pixel",
            "inch_per_pixel": inch_per_pixel,
            "method": "top_down_boundary_corners_shadow_v1",
        },
        production_authority=True,
        decision="NOT_EVALUATED",
        reason_codes=[],
    )


def approved_product_spec() -> ProductSpecResolution:
    return ProductSpecResolution(
        matched=True,
        product_code="611",
        size_group="11",
        approval_status="approved_for_production",
        production_authority=True,
        decision="NOT_EVALUATED",
        reason_codes=[],
        group_id="standard",
        nominal_length_in=75.0,
        nominal_width_in=37.5,
        length_plus_in=0.0,
        length_minus_in=0.75,
        width_plus_in=0.5,
        width_minus_in=0.5,
    )


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

    def test_boundary_corners_derive_measurements_with_calibration_scale(self) -> None:
        result = resolve_geometry_from_boundary(
            {
                "source": "synthetic_boundary_corners",
                "corners": {
                    "top_left": [0, 0],
                    "top_right": [150, 0],
                    "bottom_right": [150, 75],
                    "bottom_left": [0, 75],
                },
            },
            calibration=calibration_with_scale(),
        )

        payload = result.to_payload()

        self.assertEqual(result.decision, "BLOCKED")
        self.assertEqual(result.reason_codes, ("SOP_TOLERANCE_APPROVAL_MISSING",))
        self.assertEqual(payload["measurement_source"], "boundary_corners_calibrated_shadow")
        self.assertEqual(payload["evidence"]["boundary_source"], "synthetic_boundary_corners")
        self.assertEqual(payload["evidence"]["calibration_method"], "top_down_boundary_corners_shadow_v1")
        self.assertEqual(payload["evidence"]["sample_fractions"], [0.0, 0.5, 1.0])
        self.assertFalse(payload["production_authority"])
        self.assertEqual(payload["measurements"]["unit"], "inch")
        self.assertEqual(payload["measurements"]["length_points"], [75.0, 75.0, 75.0])
        self.assertEqual(payload["measurements"]["width_points"], [37.5, 37.5, 37.5])
        self.assertAlmostEqual(payload["measurements"]["diagonals"][0], 83.852549, places=6)
        self.assertAlmostEqual(payload["measurements"]["diagonals"][1], 83.852549, places=6)
        self.assertAlmostEqual(payload["diagonal_deviation"], 0.0)

    def test_boundary_corners_fail_closed_without_calibration_scale(self) -> None:
        with self.assertRaisesRegex(ValidationError, "calibration.geometry.inch_per_pixel is required"):
            resolve_geometry_from_boundary(
                {
                    "corners": {
                        "top_left": [0, 0],
                        "top_right": [150, 0],
                        "bottom_right": [150, 75],
                        "bottom_left": [0, 75],
                    },
                },
                calibration=CalibrationConfig(
                    schema_version=1,
                    status="synthetic",
                    approved_for_production=False,
                    source_ref="test-calibration",
                    camera={"mount": "top_down_90_degrees"},
                    lighting={"layout": "four_led_bars"},
                    production_authority=False,
                    decision="BLOCKED",
                    reason_codes=["CALIBRATION_MISSING"],
                ),
            )

    def test_boundary_measurements_feed_product_tolerance_shadow_decision(self) -> None:
        geometry = resolve_geometry_from_boundary(
            {
                "source": "synthetic_boundary_corners",
                "corners": {
                    "top_left": [0, 0],
                    "top_right": [150, 0],
                    "bottom_right": [150, 75],
                    "bottom_left": [0, 75],
                },
            },
            calibration=calibration_with_scale(),
        )
        result = evaluate_phase_one_measurements(
            product_spec=approved_product_spec(),
            calibration=approved_calibration_with_scale(),
            geometry=geometry,
        )

        self.assertEqual(result.decision, "PASS")
        self.assertEqual(result.authority_blockers, ("SOP_TOLERANCE_APPROVAL_MISSING",))
        self.assertTrue(result.shadow_mode)
        self.assertFalse(result.production_authority)
        self.assertEqual(result.rule_results[0].evidence["points_in"], [75.0, 75.0, 75.0])
        self.assertEqual(result.rule_results[1].evidence["points_in"], [37.5, 37.5, 37.5])


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
