#!/usr/bin/env python3
"""Validate the MIL Delivery Operating System framework artifacts."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


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

REQUIRED_TEMPLATES = [
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

REQUIRED_CONFIG_MARKERS = [
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
]

SECRET_PATTERN = re.compile(r"(gho_|ghp_|github_pat_|accessToken|sk-[A-Za-z0-9]{8,})")


def _missing_or_thin(root: Path, paths: list[str], errors: list[str]) -> None:
    for relative_path in paths:
        path = root / relative_path
        if not path.is_file():
            errors.append(f"missing required artifact: {relative_path}")
            continue
        text = path.read_text(encoding="utf-8")
        if len(text.strip()) < 80:
            errors.append(f"thin required artifact: {relative_path}")


def _validate_config(root: Path, errors: list[str]) -> None:
    config_path = root / ".ai-factory/config.yaml"
    if not config_path.is_file():
        errors.append("missing .ai-factory/config.yaml")
        return
    config = config_path.read_text(encoding="utf-8")
    for marker in REQUIRED_CONFIG_MARKERS:
        if marker not in config:
            errors.append(f"config.yaml missing {marker}")


def _validate_runtime_workflows(root: Path, errors: list[str]) -> None:
    path = root / ".ai-factory/runtime/workflows.json"
    if not path.is_file():
        errors.append("missing .ai-factory/runtime/workflows.json")
        return
    data = json.loads(path.read_text(encoding="utf-8"))
    workflows = data.get("workflows", {}) if isinstance(data, dict) else {}
    delivery = workflows.get("delivery_operating_system")
    if not isinstance(delivery, dict):
        errors.append("workflows.json missing delivery_operating_system")
        return
    for stage in [
        "project_intake_gate",
        "definition_of_ready_check",
        "quality_gate_router",
        "contract_test_gate",
        "release_candidate_pack",
        "rollback_drill",
        "sdlc_metrics_report",
    ]:
        if stage not in delivery:
            errors.append(f"delivery_operating_system missing {stage}")


def _validate_no_secrets(root: Path, paths: list[str], errors: list[str]) -> None:
    for relative_path in paths:
        path = root / relative_path
        if path.is_file() and SECRET_PATTERN.search(path.read_text(encoding="utf-8")):
            errors.append(f"possible secret marker in {relative_path}")


def validate_delivery_os(repo_root: str | Path) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    errors: list[str] = []
    required = (
        REQUIRED_DOCS
        + REQUIRED_CHECKLISTS
        + REQUIRED_CONTRACTS
        + REQUIRED_WINDMILL_FLOWS
        + REQUIRED_TEMPLATES
    )

    _missing_or_thin(root, required, errors)
    _validate_config(root, errors)
    _validate_runtime_workflows(root, errors)
    _validate_no_secrets(root, required, errors)

    return {
        "ok": not errors,
        "checked_artifacts": required,
        "errors": errors,
    }


def run_self_test() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    result = validate_delivery_os(repo_root)
    assert result["ok"], result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", default=str(Path(__file__).resolve().parents[2]))
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args(argv)

    if args.self_test:
        run_self_test()
        print("validate_delivery_os self-test passed")
        return 0

    result = validate_delivery_os(args.repo)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
