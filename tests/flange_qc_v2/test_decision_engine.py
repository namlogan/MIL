import unittest
from pathlib import Path

from apps.flange_qc_v2.calibration import CalibrationConfig, load_calibration_config
from apps.flange_qc_v2.decision_engine import (
    evaluate_phase_one_measurements,
    evaluate_phase_three_observations,
    evaluate_phase_two_geometry,
    evaluate_sop_safe_fallbacks,
)
from apps.flange_qc_v2.domain import BoundingBox, DetectorObservation, ValidationError
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


class SopSafeFallbackDecisionEngineTests(unittest.TestCase):
    def test_phase_three_returns_not_evaluated_without_detector_observations(self) -> None:
        result = evaluate_phase_three_observations(observations=[])

        self.assertEqual(result.phase, "PHASE_3")
        self.assertEqual(result.decision, "NOT_EVALUATED")
        self.assertEqual(result.reason_codes, ("MODEL_MISSING",))
        self.assertEqual(result.authority_blockers, ("MODEL_APPROVAL_REQUIRED",))
        self.assertTrue(result.shadow_mode)
        self.assertFalse(result.production_authority)
        self.assertEqual(
            tuple(rule.rule_id for rule in result.rule_results),
            ("M1-SOP-6.4-PUNCH-MARK-001", "M1-SOP-6.2-PUNCH-OFFSET-001"),
        )
        self.assertTrue(all(rule.decision == "NOT_EVALUATED" for rule in result.rule_results))
        self.assertEqual(result.rule_results[0].evidence["observation_count"], 0)

    def test_phase_three_returns_assist_with_detector_observation_evidence(self) -> None:
        observation = DetectorObservation(
            label="punch_mark",
            confidence=0.87,
            bbox=BoundingBox(x=0.42, y=0.25, width=0.12, height=0.08),
            model_ref="registry://flange-qc-v2/detector/punch-mark/2026-06-02",
            evidence_ref="templates/flange_qc_v2/artifact_intake/evaluation_report.json",
        )

        result = evaluate_phase_three_observations(observations=[observation])

        self.assertEqual(result.phase, "PHASE_3")
        self.assertEqual(result.decision, "ASSIST")
        self.assertEqual(result.reason_codes, ("MODEL_REVIEW_REQUIRED",))
        self.assertEqual(result.authority_blockers, ("MODEL_APPROVAL_REQUIRED",))
        self.assertTrue(result.shadow_mode)
        self.assertFalse(result.production_authority)
        self.assertEqual(result.rule_results[0].rule_id, "M1-SOP-6.4-PUNCH-MARK-001")
        self.assertEqual(result.rule_results[0].decision, "ASSIST")
        self.assertEqual(result.rule_results[0].evidence["matched_labels"], ["punch_mark"])
        self.assertEqual(result.rule_results[0].evidence["max_confidence"], 0.87)
        self.assertEqual(result.rule_results[0].evidence["bboxes"], [[0.42, 0.25, 0.12, 0.08]])
        self.assertEqual(
            result.rule_results[0].evidence["model_refs"],
            ["registry://flange-qc-v2/detector/punch-mark/2026-06-02"],
        )
        self.assertEqual(
            result.rule_results[0].evidence["evidence_refs"],
            ["templates/flange_qc_v2/artifact_intake/evaluation_report.json"],
        )
        self.assertNotIn("PASS", {rule.decision for rule in result.rule_results})
        self.assertNotIn("NG", {rule.decision for rule in result.rule_results})

    def test_phase_three_model_dependent_rules_return_assist_without_authority(self) -> None:
        result = evaluate_sop_safe_fallbacks(phase="PHASE_3")

        self.assertEqual(result.phase, "PHASE_3")
        self.assertEqual(result.decision, "ASSIST")
        self.assertEqual(result.reason_codes, ("MODEL_REVIEW_REQUIRED",))
        self.assertEqual(result.authority_blockers, ("MODEL_APPROVAL_REQUIRED",))
        self.assertTrue(result.shadow_mode)
        self.assertFalse(result.production_authority)
        self.assertEqual(
            tuple(rule.rule_id for rule in result.rule_results),
            ("M1-SOP-6.4-PUNCH-MARK-001", "M1-SOP-6.2-PUNCH-OFFSET-001"),
        )
        self.assertTrue(all(rule.decision == "ASSIST" for rule in result.rule_results))
        self.assertEqual(result.rule_results[0].reason_codes, ("MODEL_REVIEW_REQUIRED",))
        self.assertEqual(result.rule_results[0].evidence["fallback_source"], "sop_registry")
        self.assertEqual(result.rule_results[0].evidence["category"], "vision")
        self.assertFalse(result.rule_results[0].evidence["production_enabled"])

    def test_phase_four_rules_keep_assist_and_not_evaluated_safe_states(self) -> None:
        result = evaluate_sop_safe_fallbacks(phase="PHASE_4")

        self.assertEqual(result.phase, "PHASE_4")
        self.assertEqual(result.decision, "ASSIST")
        self.assertEqual(result.reason_codes, ("RULE_POST_MVP_DISABLED", "MODEL_REVIEW_REQUIRED"))
        self.assertEqual(result.authority_blockers, ("MODEL_APPROVAL_REQUIRED",))
        self.assertTrue(result.shadow_mode)
        self.assertFalse(result.production_authority)
        self.assertEqual(len(result.rule_results), 8)
        self.assertIn("ASSIST", {rule.decision for rule in result.rule_results})
        self.assertIn("NOT_EVALUATED", {rule.decision for rule in result.rule_results})
        self.assertNotIn("PASS", {rule.decision for rule in result.rule_results})
        self.assertEqual(
            result.rule_results[0].to_payload()["evidence"]["fallback_source"],
            "sop_registry",
        )

    def test_safe_fallback_rejects_unsupported_phase_explicitly(self) -> None:
        with self.assertRaisesRegex(ValidationError, "supports PHASE_3 or PHASE_4"):
            evaluate_sop_safe_fallbacks(phase="PHASE_1")


if __name__ == "__main__":
    unittest.main()
