import json
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
WORKSTREAM_MANIFEST = REPO_ROOT / ".ai-factory/workstreams/flange_qc_v2_machine_vision.json"
WORKSTREAM_DOC = REPO_ROOT / "docs/project/flange_qc_v2/WORKSTREAM_STATUS.md"


class FlangeQcV2WorkstreamStatusTests(unittest.TestCase):
    def test_machine_vision_workstream_manifest_freezes_demo_only_lane(self) -> None:
        manifest = json.loads(WORKSTREAM_MANIFEST.read_text(encoding="utf-8"))
        frozen = {entry["workstream_id"]: entry for entry in manifest["frozen_workstreams"]}

        self.assertEqual(manifest["project_id"], "flange_qc_v2")
        self.assertEqual(manifest["active_workstream"]["workstream_id"], "machine_vision")
        self.assertEqual(manifest["active_workstream"]["mode"], "real_runtime_sop")
        self.assertEqual(frozen["flange_qc_v2_demo_only"]["status"], "frozen")
        self.assertIn("demo_only_polish", frozen["flange_qc_v2_demo_only"]["blocked_work"])

    def test_machine_vision_priority_order_keeps_models_after_sop_gates(self) -> None:
        manifest = json.loads(WORKSTREAM_MANIFEST.read_text(encoding="utf-8"))
        ordered_gate_ids = [gate["gate_id"] for gate in manifest["active_workstream"]["priority_order"]]

        self.assertEqual(
            ordered_gate_ids,
            [
                "camera_hardware_readiness",
                "calibration_evidence",
                "runtime_geometry_evidence",
                "product_specs_approval_package",
                "full_sop_rule_gate",
                "advanced_model_defect_work",
            ],
        )
        advanced_model = manifest["active_workstream"]["priority_order"][-1]
        self.assertEqual(advanced_model["status"], "blocked_until_prior_gates_pass")
        self.assertEqual(
            advanced_model["blocked_by"],
            ordered_gate_ids[:-1],
        )
        self.assertFalse(manifest["active_workstream"]["production_authority"])

    def test_workstream_status_doc_names_current_freeze_and_resume_triggers(self) -> None:
        text = WORKSTREAM_DOC.read_text(encoding="utf-8")

        self.assertIn("Demo-only V2 Workstream: Frozen", text)
        self.assertIn("Active Workstream: `machine_vision` Real-Runtime SOP", text)
        self.assertIn("advanced model defect work remains blocked", text)
        self.assertIn("camera hardware/readiness evidence", text)
        self.assertIn("calibration evidence", text)
        self.assertIn("runtime geometry measurement evidence", text)
        self.assertIn("product specs and tolerance approval package", text)
        self.assertIn("full SOP rule gate", text)


if __name__ == "__main__":
    unittest.main()
