import json
import tempfile
import unittest
from pathlib import Path

from apps.flange_qc_v2.domain import ValidationError
from apps.flange_qc_v2.product_specs import load_product_specs


REPO_ROOT = Path(__file__).resolve().parents[2]
PRODUCT_SPECS = REPO_ROOT / "configs/flange_qc_v2/product_specs.bootstrap.json"


class ProductSpecResolverTests(unittest.TestCase):
    def test_resolves_known_draft_product_size_without_production_authority(self) -> None:
        catalog = load_product_specs(PRODUCT_SPECS)

        result = catalog.resolve(product_code="611", size_group="11")

        self.assertTrue(result.matched)
        self.assertEqual(result.group_id, "standard")
        self.assertEqual(result.nominal_length_in, 75.0)
        self.assertEqual(result.nominal_width_in, 37.5)
        self.assertEqual(result.length_plus_in, 0.0)
        self.assertEqual(result.length_minus_in, 0.75)
        self.assertEqual(result.width_plus_in, 0.5)
        self.assertEqual(result.width_minus_in, 0.5)
        self.assertEqual(result.approval_status, "draft_requires_qc_owner_approval")
        self.assertFalse(result.production_authority)
        self.assertEqual(result.decision, "BLOCKED")
        self.assertIn("PRODUCT_SPEC_APPROVAL_MISSING", result.reason_codes)

    def test_unknown_product_fails_closed(self) -> None:
        catalog = load_product_specs(PRODUCT_SPECS)

        result = catalog.resolve(product_code="NOPE", size_group="11")

        self.assertFalse(result.matched)
        self.assertEqual(result.decision, "BLOCKED")
        self.assertEqual(result.reason_codes, ["UNKNOWN_PRODUCT"])
        self.assertIsNone(result.nominal_length_in)

    def test_unknown_size_fails_closed(self) -> None:
        catalog = load_product_specs(PRODUCT_SPECS)

        result = catalog.resolve(product_code="611", size_group="99")

        self.assertFalse(result.matched)
        self.assertEqual(result.decision, "BLOCKED")
        self.assertEqual(result.reason_codes, ["UNKNOWN_SIZE"])

    def test_invalid_config_shape_is_rejected_explicitly(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "product_specs.json"
            path.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "status": "draft_requires_qc_owner_approval",
                        "source_ref": "fixture",
                        "approval_required": True,
                    }
                ),
                encoding="utf-8",
            )

            with self.assertRaisesRegex(ValidationError, "product_groups is required"):
                load_product_specs(path)


if __name__ == "__main__":
    unittest.main()
