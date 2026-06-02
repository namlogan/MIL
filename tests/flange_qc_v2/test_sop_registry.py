import unittest

from apps.flange_qc_v2.domain import ValidationError
from apps.flange_qc_v2.sop_registry import (
    CORE_RULE_IDS,
    REASON_CODES,
    get_reason_code,
    get_rule,
    list_rules,
)


class SopRuleRegistryTests(unittest.TestCase):
    def test_registry_contains_documented_core_rule_ids(self) -> None:
        rule_ids = {rule.rule_id for rule in list_rules()}

        self.assertEqual(rule_ids, set(CORE_RULE_IDS))
        self.assertEqual(get_rule("M1-SOP-6.1-LENGTH-001").phase, "PHASE_1")
        self.assertEqual(get_rule("M1-SOP-6.1-DIAGONAL-002").phase, "PHASE_2")

    def test_model_dependent_rules_expose_safe_fallback_not_production_authority(self) -> None:
        rule = get_rule("M1-SOP-6.4-PUNCH-MARK-001")

        self.assertEqual(rule.authority, "model_vision_dependent_until_approved")
        self.assertEqual(rule.safe_fallback_decision, "ASSIST")
        self.assertFalse(rule.production_enabled)

    def test_post_mvp_rules_are_not_evaluated_by_default(self) -> None:
        rule = get_rule("M1-SOP-7.3-SEAM-CURVATURE-001")

        self.assertEqual(rule.authority, "post_mvp_disabled_until_enabled")
        self.assertEqual(rule.safe_fallback_decision, "NOT_EVALUATED")
        self.assertFalse(rule.production_enabled)

    def test_unknown_rule_id_is_rejected_explicitly(self) -> None:
        with self.assertRaisesRegex(ValidationError, "unknown SOP rule"):
            get_rule("MISSING-RULE")


class ReasonCodeRegistryTests(unittest.TestCase):
    def test_reason_codes_cover_fail_closed_bootstrap_states(self) -> None:
        codes = {reason.code for reason in REASON_CODES}

        self.assertIn("PRODUCT_SPEC_APPROVAL_MISSING", codes)
        self.assertIn("UNKNOWN_PRODUCT", codes)
        self.assertIn("CALIBRATION_MISSING", codes)
        self.assertIn("MEASUREMENTS_INCOMPLETE", codes)
        self.assertIn("LENGTH_OUT_OF_TOLERANCE", codes)
        self.assertIn("WIDTH_OUT_OF_TOLERANCE", codes)
        self.assertIn("DIAGONAL_DEVIATION_EXCEEDS_LIMIT", codes)
        self.assertIn("MODEL_MISSING", codes)
        self.assertEqual(get_reason_code("UNKNOWN_PRODUCT").decision, "BLOCKED")
        self.assertEqual(get_reason_code("LENGTH_OUT_OF_TOLERANCE").decision, "NG")
        self.assertEqual(get_reason_code("WIDTH_OUT_OF_TOLERANCE").decision, "NG")
        self.assertEqual(get_reason_code("DIAGONAL_DEVIATION_EXCEEDS_LIMIT").decision, "NG")

    def test_not_evaluated_reason_codes_never_map_to_pass(self) -> None:
        not_evaluated = [
            reason for reason in REASON_CODES if reason.decision == "NOT_EVALUATED"
        ]

        self.assertTrue(not_evaluated)
        self.assertTrue(all(reason.decision != "PASS" for reason in not_evaluated))

    def test_unknown_reason_code_is_rejected_explicitly(self) -> None:
        with self.assertRaisesRegex(ValidationError, "unknown reason code"):
            get_reason_code("NOT_A_REASON")


if __name__ == "__main__":
    unittest.main()
