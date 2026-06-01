from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]

PIPELINE_STAGES = [
    "project_intake",
    "memory_preflight",
    "bootstrap_docs",
    "architecture_adr_gate",
    "contract_backlog_gate",
    "repo_ci_bootstrap",
    "agent_delivery_loop",
    "qa_review_merge_gate",
    "release_rollback_gate",
    "operate_learn_memory_maintenance",
]

REQUIRED_PROJECT_DOCS = [
    "docs/project/RISK_REGISTER.md",
    "docs/project/OPEN_QUESTIONS.md",
    "docs/project/SOURCE_OF_TRUTH.md",
    "docs/project/QUALITY_GATE_MATRIX.md",
]

REQUIRED_PROJECT_TEMPLATES = [
    "docs/templates/project/RISK_REGISTER.md",
    "docs/templates/project/OPEN_QUESTIONS.md",
    "docs/templates/project/SOURCE_OF_TRUTH.md",
    "docs/templates/project/QUALITY_GATE_MATRIX.md",
]

REQUIRED_STARTUP_FLOWS = [
    ".windmill/flows/architecture_review.md",
    ".windmill/flows/contract_bootstrap.md",
    ".windmill/flows/task_generation.md",
    ".windmill/flows/repo_bootstrap.md",
    ".windmill/flows/ci_baseline_check.md",
    ".windmill/flows/agent_assignment.md",
    ".windmill/flows/pr_review_gate.md",
    ".windmill/flows/test_gate.md",
    ".windmill/flows/contract_gate.md",
    ".windmill/flows/release_gate.md",
    ".windmill/flows/deployment_gate.md",
    ".windmill/flows/rollback_pack.md",
    ".windmill/flows/postmortem_to_memory.md",
]


class NewProjectStartupPipelineTests(unittest.TestCase):
    def test_startup_runbook_captures_gate_first_pipeline(self) -> None:
        runbook = REPO_ROOT / "docs/runbooks/new_project_startup_pipeline.md"

        self.assertTrue(runbook.is_file(), "missing new project startup runbook")
        text = runbook.read_text(encoding="utf-8")
        for marker in [
            "Project Intake",
            "Memory Preflight",
            "Architecture / ADR Gate",
            "Contract & Backlog Gate",
            "Repo + CI Bootstrap",
            "Agent Delivery Loop",
            "QA / Review / Merge Gate",
            "Release / Rollback Gate",
            "Operate / Learn / Memory Maintenance",
            "Git/docs/tests/issues are source of truth",
            "Memory0 is not source of truth",
            "Do not code before PRD/MVP/Architecture/Test Strategy",
        ]:
            with self.subTest(marker=marker):
                self.assertIn(marker, text)

    def test_runtime_workflow_registers_new_project_pipeline_order(self) -> None:
        workflows = json.loads(
            (REPO_ROOT / ".ai-factory/runtime/workflows.json").read_text(encoding="utf-8")
        )
        startup = workflows["workflows"]["new_project_startup_pipeline"]

        self.assertEqual(startup["stage_order"], PIPELINE_STAGES)
        self.assertEqual(startup["source_of_truth"], "git_docs_tests_issues")
        self.assertEqual(startup["memory_policy"], "approved_memory_context_only")
        self.assertFalse(startup["allow_agent_implementation_before_ready"])

    def test_required_project_docs_and_templates_are_versioned(self) -> None:
        for relative_path in REQUIRED_PROJECT_DOCS + REQUIRED_PROJECT_TEMPLATES:
            with self.subTest(path=relative_path):
                path = REPO_ROOT / relative_path
                self.assertTrue(path.is_file(), f"missing {relative_path}")
                self.assertGreater(path.stat().st_size, 80, f"thin {relative_path}")

    def test_startup_windmill_flow_docs_are_versioned(self) -> None:
        for relative_path in REQUIRED_STARTUP_FLOWS:
            with self.subTest(path=relative_path):
                path = REPO_ROOT / relative_path
                self.assertTrue(path.is_file(), f"missing {relative_path}")
                self.assertGreater(path.stat().st_size, 80, f"thin {relative_path}")

    def test_delivery_validator_enforces_startup_pipeline(self) -> None:
        completed = subprocess.run(
            [sys.executable, "scripts/delivery/validate_delivery_os.py", "--self-test"],
            cwd=REPO_ROOT,
            check=False,
            text=True,
            capture_output=True,
        )

        self.assertEqual(completed.returncode, 0, completed.stderr + completed.stdout)

    def test_agent_instructions_make_pipeline_binding(self) -> None:
        agents = (REPO_ROOT / "AGENTS.md").read_text(encoding="utf-8")
        rules = (REPO_ROOT / ".ai-factory/RULES.md").read_text(encoding="utf-8")

        self.assertIn("New Project Startup Pipeline", agents)
        self.assertIn("No implementation task may start before the startup pipeline gates pass", rules)

    def test_user_binding_startup_protocol_is_explicit(self) -> None:
        agents = (REPO_ROOT / "AGENTS.md").read_text(encoding="utf-8")

        for marker in [
            "User Binding Startup Protocol",
            "Do not let agents code immediately",
            "project_id",
            "PRD.md",
            "python3 scripts/project-intake/validate_project_intake.py",
            "python3 scripts/operator/daily_status.py",
            "GitHub issue -> `agent:plan` -> reviewed plan ->",
            "If a future session tries to skip this sequence",
        ]:
            with self.subTest(marker=marker):
                self.assertIn(marker, agents)


if __name__ == "__main__":
    unittest.main()
