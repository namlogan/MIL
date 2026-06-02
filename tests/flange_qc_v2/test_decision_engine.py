import unittest
from pathlib import Path

from apps.flange_qc_v2.calibration import CalibrationConfig, load_calibration_config
from apps.flange_qc_v2.decision_engine import (
    evaluate_phase_one_measurements,
    evaluate_phase_two_geometry,
)
from apps.flange_qc_v2.geometry import resolve_geometry_measurements
from apps.flange_qc_v2.product_specs import ProductSpecResolution, load_product_specs


REPO_ROOT = Path(__file__).resolve().parents[2]
PRODUCT_SPECS = REPO_ROOT / "configs/flange_qc_v2/product_specs.bootstrap.json"
CALIBRATION_FIXTURE = REPO_ROOT / "configs/flange_qc_v2/camera_calibration.synthetic.example.json"


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


def approved_calibration() -> CalibrationConfig:
    return CalibrationConfig(
        schema_version=1,
        status="approved",
        approved_for_production=True,
        source_ref="test-fixture",
        camera={"mount": "top_down_90_degrees"},
        lighting={"layout": "four_led_bars"},
        production_authority=True,
        decision="NOT_EVALUATED",
        reason_codes=[],
    )


class PhaseOneDecisionEngineTests(unittest.TestCase):
    def test_phase_one_blocks_when_product_spec_and_calibration_lack_authority(self) -> None:
        product_spec = load_product_specs(PRODUCT_SPECS).resolve(product_code="611", size_group="11")
        calibration = load_calibration_config(CALIBRATION_FIXTURE)
        geometry = resolve_geometry_measurements(
            {
                "length_points": [74.25, 74.5, 75.0],
                "width_points": [37.0, 37.5, 38.0],
                "diagonals": [83.0, 83.25],
                "unit": "inch",
            }
        )

        result = evaluate_phase_one_measurements(
            product_spec=product_spec,
            calibration=calibration,
            geometry=geometry,
        )

        self.assertEqual(result.phase, "PHASE_1")
        self.assertEqual(result.decision, "BLOCKED")
        self.assertEqual(result.reason_codes, ("PRODUCT_SPEC_APPROVAL_MISSING", "CALIBRATION_MISSING"))
        self.assertFalse(result.shadow_mode)
        self.assertFalse(result.production_authority)

    def test_phase_one_returns_shadow_pass_when_all_points_are_within_tolerance(self) -> None:
        geometry = resolve_geometry_measurements(
            {
                "length_points": [74.25, 74.5, 75.0],
                "width_points": [37.0, 37.5, 38.0],
                "diagonals": [83.0, 83.25],
                "unit": "inch",
            }
        )

        result = evaluate_phase_one_measurements(
            product_spec=approved_product_spec(),
            calibration=approved_calibration(),
            geometry=geometry,
        )

        self.assertEqual(result.decision, "PASS")
        self.assertEqual(result.reason_codes, ())
        self.assertEqual(result.authority_blockers, ("SOP_TOLERANCE_APPROVAL_MISSING",))
        self.assertTrue(result.shadow_mode)
        self.assertFalse(result.production_authority)
        self.assertEqual(
            tuple(rule.rule_id for rule in result.rule_results),
            ("M1-SOP-6.1-LENGTH-001", "M1-SOP-6.1-WIDTH-001"),
        )
        length_evidence = result.rule_results[0].evidence
        self.assertEqual(length_evidence["aggregate_method"], "all_points_must_pass_bootstrap")
        self.assertEqual(length_evidence["points_in"], [74.25, 74.5, 75.0])
        self.assertEqual(length_evidence["nominal_in"], 75.0)
        self.assertEqual(length_evidence["lower_bound_in"], 74.25)
        self.assertEqual(length_evidence["upper_bound_in"], 75.0)
        self.assertEqual(length_evidence["min_in"], 74.25)
        self.assertEqual(length_evidence["max_in"], 75.0)
        self.assertEqual(length_evidence["out_of_tolerance_point_indexes"], [])

    def test_phase_one_returns_shadow_ng_when_any_point_is_out_of_tolerance(self) -> None:
        geometry = resolve_geometry_measurements(
            {
                "length_points": [74.25, 75.1, 74.25],
                "width_points": [36.9, 37.5, 38.0],
                "diagonals": [83.0, 83.25],
                "unit": "inch",
            }
        )

        result = evaluate_phase_one_measurements(
            product_spec=approved_product_spec(),
            calibration=approved_calibration(),
            geometry=geometry,
        )

        self.assertEqual(result.decision, "NG")
        self.assertEqual(result.reason_codes, ("LENGTH_OUT_OF_TOLERANCE", "WIDTH_OUT_OF_TOLERANCE"))
        self.assertEqual(result.authority_blockers, ("SOP_TOLERANCE_APPROVAL_MISSING",))
        self.assertTrue(result.shadow_mode)
        self.assertFalse(result.production_authority)
        self.assertEqual(result.rule_results[0].decision, "NG")
        self.assertEqual(result.rule_results[0].reason_codes, ("LENGTH_OUT_OF_TOLERANCE",))
        self.assertEqual(result.rule_results[0].evidence["average_in"], 74.53333333333333)
        self.assertEqual(result.rule_results[0].evidence["out_of_tolerance_point_indexes"], [1])
        self.assertEqual(result.rule_results[1].decision, "NG")
        self.assertEqual(result.rule_results[1].reason_codes, ("WIDTH_OUT_OF_TOLERANCE",))
        self.assertEqual(result.rule_results[1].evidence["out_of_tolerance_point_indexes"], [0])

    def test_phase_one_blocks_incomplete_measurements_before_shadow_decision(self) -> None:
        geometry = resolve_geometry_measurements(
            {
                "length_points": [74.25, 74.5],
                "width_points": [37.0, 37.5, 38.0],
                "diagonals": [83.0, 83.25],
                "unit": "inch",
            }
        )

        result = evaluate_phase_one_measurements(
            product_spec=approved_product_spec(),
            calibration=approved_calibration(),
            geometry=geometry,
        )

        self.assertEqual(result.decision, "BLOCKED")
        self.assertEqual(result.reason_codes, ("MEASUREMENTS_INCOMPLETE",))
        self.assertFalse(result.shadow_mode)
        self.assertFalse(result.production_authority)


class PhaseTwoDecisionEngineTests(unittest.TestCase):
    def test_phase_two_blocks_when_product_spec_and_calibration_lack_authority(self) -> None:
        product_spec = load_product_specs(PRODUCT_SPECS).resolve(product_code="611", size_group="11")
        calibration = load_calibration_config(CALIBRATION_FIXTURE)
        geometry = resolve_geometry_measurements(
            {
                "length_points": [74.9, 75.0, 75.1],
                "width_points": [37.4, 37.5, 37.6],
                "diagonals": [83.0, 83.25],
                "unit": "inch",
            }
        )

        result = evaluate_phase_two_geometry(
            product_spec=product_spec,
            calibration=calibration,
            geometry=geometry,
        )

        self.assertEqual(result.phase, "PHASE_2")
        self.assertEqual(result.decision, "BLOCKED")
        self.assertEqual(result.reason_codes, ("PRODUCT_SPEC_APPROVAL_MISSING", "CALIBRATION_MISSING"))
        self.assertFalse(result.shadow_mode)
        self.assertFalse(result.production_authority)

    def test_phase_two_returns_shadow_ng_when_diagonal_deviation_exceeds_limit(self) -> None:
        geometry = resolve_geometry_measurements(
            {
                "length_points": [74.9, 75.0, 75.1],
                "width_points": [37.4, 37.5, 37.6],
                "diagonals": [83.0, 83.75],
                "unit": "inch",
            }
        )

        result = evaluate_phase_two_geometry(
            product_spec=approved_product_spec(),
            calibration=approved_calibration(),
            geometry=geometry,
        )

        self.assertEqual(result.decision, "NG")
        self.assertEqual(result.reason_codes, ("DIAGONAL_DEVIATION_EXCEEDS_LIMIT",))
        self.assertEqual(result.authority_blockers, ("SOP_TOLERANCE_APPROVAL_MISSING",))
        self.assertTrue(result.shadow_mode)
        self.assertFalse(result.production_authority)
        self.assertEqual(result.rule_results[0].rule_id, "M1-SOP-6.1-DIAGONAL-002")
        self.assertEqual(result.rule_results[0].evidence["threshold_in"], 0.5)

    def test_phase_two_returns_shadow_pass_when_diagonal_deviation_is_within_limit(self) -> None:
        geometry = resolve_geometry_measurements(
            {
                "length_points": [74.9, 75.0, 75.1],
                "width_points": [37.4, 37.5, 37.6],
                "diagonals": [83.0, 83.5],
                "unit": "inch",
            }
        )

        result = evaluate_phase_two_geometry(
            product_spec=approved_product_spec(),
            calibration=approved_calibration(),
            geometry=geometry,
        )

        self.assertEqual(result.decision, "PASS")
        self.assertEqual(result.reason_codes, ())
        self.assertEqual(result.authority_blockers, ("SOP_TOLERANCE_APPROVAL_MISSING",))
        self.assertTrue(result.shadow_mode)
        self.assertFalse(result.production_authority)

    def test_phase_two_blocks_incomplete_measurements_before_shadow_decision(self) -> None:
        geometry = resolve_geometry_measurements(
            {
                "length_points": [74.9, 75.0],
                "width_points": [37.4, 37.5, 37.6],
                "diagonals": [83.0, 83.5],
                "unit": "inch",
            }
        )

        result = evaluate_phase_two_geometry(
            product_spec=approved_product_spec(),
            calibration=approved_calibration(),
            geometry=geometry,
        )

        self.assertEqual(result.decision, "BLOCKED")
        self.assertEqual(result.reason_codes, ("MEASUREMENTS_INCOMPLETE",))
        self.assertFalse(result.shadow_mode)
        self.assertFalse(result.production_authority)


if __name__ == "__main__":
    unittest.main()
