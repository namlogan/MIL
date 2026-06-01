from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


REQUIRED_DOCS = [
    ".ai-factory/DELIVERY_OPERATING_MODEL.md",
    ".ai-factory/DEFINITION_OF_READY.md",
    ".ai-factory/DEFINITION_OF_DONE.md",
    ".ai-factory/QUALITY_GATES.md",
    ".ai-factory/RELEASE_POLICY.md",
    ".ai-factory/ESCALATION_POLICY.md",
    ".ai-factory/SOURCE_OF_TRUTH_MATRIX.md",
]

REQUIRED_CHECKLISTS = [
    ".ai-factory/checklists/project_intake_checklist.md",
    ".ai-factory/checklists/task_ready_checklist.md",
    ".ai-factory/checklists/pr_review_checklist.md",
    ".ai-factory/checklists/release_checklist.md",
    ".ai-factory/checklists/rollback_checklist.md",
    ".ai-factory/checklists/memory_review_checklist.md",
]

REQUIRED_CONTRACTS = [
    "contracts/README.md",
    "contracts/api/openapi.yaml",
    "contracts/events/software_task_event.schema.json",
    "contracts/payloads/task_context_pack.schema.json",
    "contracts/db/migration_contract.md",
    "contracts/memory/memory_event.schema.json",
    "contracts/jobs/gstack_job.schema.json",
]

REQUIRED_WINDMILL_FLOWS = [
    ".windmill/flows/project_intake_gate.md",
    ".windmill/flows/project_bootstrap.md",
    ".windmill/flows/project_readiness_score.md",
    ".windmill/flows/definition_of_ready_check.md",
    ".windmill/flows/quality_gate_router.md",
    ".windmill/flows/contract_test_gate.md",
    ".windmill/flows/security_gate.md",
    ".windmill/flows/release_candidate_pack.md",
    ".windmill/flows/staging_deploy.md",
    ".windmill/flows/shadow_deploy.md",
    ".windmill/flows/production_approval.md",
    ".windmill/flows/rollback_drill.md",
    ".windmill/flows/release_memory_writeback.md",
    ".windmill/flows/sdlc_metrics_report.md",
]

REQUIRED_TEMPLATE_ROOTS = [
    "templates/project_bootstrap/README.md",
    "templates/fastapi_service/README.md",
    "templates/frontend_app/README.md",
    "templates/worker_service/README.md",
    "templates/data_pipeline/README.md",
    "templates/mlops_project/README.md",
    "templates/windmill_flow/README.md",
    "templates/memory_gateway/README.md",
    "templates/gstack_job/README.md",
    "templates/adr/README.md",
    "templates/prd/README.md",
    "templates/runbook/README.md",
    "templates/release_manifest/README.md",
]


def load_module(name: str, relative_path: str):
    module_path = REPO_ROOT / relative_path
    spec = importlib.util.spec_from_file_location(name, module_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class DeliveryOperatingSystemTests(unittest.TestCase):
    def test_delivery_os_required_artifacts_are_versioned(self) -> None:
        for relative_path in (
            REQUIRED_DOCS
            + REQUIRED_CHECKLISTS
            + REQUIRED_CONTRACTS
            + REQUIRED_WINDMILL_FLOWS
            + REQUIRED_TEMPLATE_ROOTS
        ):
            with self.subTest(path=relative_path):
                path = REPO_ROOT / relative_path
                self.assertTrue(path.is_file(), f"missing {relative_path}")
                self.assertGreater(path.stat().st_size, 80, f"thin artifact {relative_path}")

    def test_delivery_os_policy_docs_define_sdlc_gates(self) -> None:
        delivery_model = (REPO_ROOT / ".ai-factory/DELIVERY_OPERATING_MODEL.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("Project Intake Gate", delivery_model)
        self.assertIn("Definition of Ready", delivery_model)
        self.assertIn("Definition of Done", delivery_model)
        self.assertIn("Release Gate", delivery_model)
        self.assertIn("Memory Hygiene", delivery_model)

        quality_gates = (REPO_ROOT / ".ai-factory/QUALITY_GATES.md").read_text(encoding="utf-8")
        for marker in [
            "Product",
            "API contract",
            "Database migration",
            "Security",
            "Memory event",
            "Release",
        ]:
            with self.subTest(marker=marker):
                self.assertIn(marker, quality_gates)

        source_of_truth = (REPO_ROOT / ".ai-factory/SOURCE_OF_TRUTH_MATRIX.md").read_text(
            encoding="utf-8"
        )
        for marker in [
            "Requirements",
            "Architecture decision",
            "Code",
            "Task state",
            "Test result",
            "Release state",
            "Memory",
        ]:
            with self.subTest(marker=marker):
                self.assertIn(marker, source_of_truth)

    def test_contract_validator_accepts_contract_first_skeletons(self) -> None:
        completed = subprocess.run(
            [sys.executable, "scripts/contracts/validate_contracts.py", "--self-test"],
            cwd=REPO_ROOT,
            check=False,
            text=True,
            capture_output=True,
        )

        self.assertEqual(completed.returncode, 0, completed.stderr + completed.stdout)
        self.assertIn("validate_contracts self-test passed", completed.stdout)

    def test_delivery_os_validator_accepts_current_install(self) -> None:
        completed = subprocess.run(
            [sys.executable, "scripts/delivery/validate_delivery_os.py", "--self-test"],
            cwd=REPO_ROOT,
            check=False,
            text=True,
            capture_output=True,
        )

        self.assertEqual(completed.returncode, 0, completed.stderr + completed.stdout)
        self.assertIn("validate_delivery_os self-test passed", completed.stdout)

    def test_sdlc_metrics_report_defines_operator_dashboard(self) -> None:
        metrics = load_module(
            "sdlc_metrics_report",
            "scripts/operator/sdlc_metrics_report.py",
        )
        report = metrics.build_sdlc_metrics_report(REPO_ROOT, runner=metrics.fake_runner)

        self.assertTrue(report["ok"], report)
        for metric in [
            "lead_time_issue_to_merge",
            "cycle_time_by_task_type",
            "pr_review_latency",
            "build_failure_rate",
            "rework_rate",
            "escaped_defect_count",
            "rollback_count",
            "memory_conflict_count",
            "agent_handoff_quality",
            "test_flakiness",
            "release_frequency",
        ]:
            with self.subTest(metric=metric):
                self.assertIn(metric, report["metrics"])

        for section in [
            "current_wip",
            "blocked_tasks",
            "aging_prs",
            "failed_gates",
            "upcoming_releases",
            "memory_candidates_waiting_review",
            "stale_open_questions",
            "postmortem_actions",
        ]:
            with self.subTest(section=section):
                self.assertIn(section, report["dashboard"])

    def test_config_registers_delivery_os_controls(self) -> None:
        config = (REPO_ROOT / ".ai-factory/config.yaml").read_text(encoding="utf-8")
        for marker in [
            "delivery_operating_model: .ai-factory/DELIVERY_OPERATING_MODEL.md",
            "definition_of_ready: .ai-factory/DEFINITION_OF_READY.md",
            "definition_of_done: .ai-factory/DEFINITION_OF_DONE.md",
            "delivery_quality_gates: .ai-factory/QUALITY_GATES.md",
            "release_policy: .ai-factory/RELEASE_POLICY.md",
            "escalation_policy: .ai-factory/ESCALATION_POLICY.md",
            "source_of_truth_matrix: .ai-factory/SOURCE_OF_TRUTH_MATRIX.md",
            "contracts: contracts",
            "templates: templates",
            "delivery_os_validator: scripts/delivery/validate_delivery_os.py",
            "contract_validator: scripts/contracts/validate_contracts.py",
            "sdlc_metrics_report: scripts/operator/sdlc_metrics_report.py",
            "require_definition_of_ready: true",
            "require_definition_of_done: true",
            "require_contract_tests_for_contract_changes: true",
            "max_preferred_pr_loc: 300",
            "max_unapproved_pr_loc: 800",
            "require_rollback_drill_for_production: true",
        ]:
            with self.subTest(marker=marker):
                self.assertIn(marker, config)

    def test_memory_contract_schema_is_single_source_compatible(self) -> None:
        canonical = json.loads(
            (REPO_ROOT / "memory/schemas/memory_event.schema.json").read_text(encoding="utf-8")
        )
        contract = json.loads(
            (REPO_ROOT / "contracts/memory/memory_event.schema.json").read_text(encoding="utf-8")
        )

        self.assertEqual(contract, canonical)


if __name__ == "__main__":
    unittest.main()
