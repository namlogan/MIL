# FLANGE QC V2 Kickoff ZIP Review

Date: 2026-06-02

## Source Reviewed

```text
/Users/mac/Desktop/flange_project_kickoff_docs.zip
```

Extracted review location:

```text
/tmp/flange_project_kickoff_docs
```

## Contents

The ZIP includes 13 files:

- `AGENTS.md`
- `.ai-factory/DESCRIPTION.md`
- `.ai-factory/ARCHITECTURE.md`
- `.ai-factory/RULES.md`
- `.ai-factory/rules/product.md`
- `.ai-factory/rules/security.md`
- `.ai-factory/rules/implementation.md`
- `docs/project/PRD.md`
- `docs/project/MVP_SCOPE.md`
- `docs/project/USER_FLOWS.md`
- `docs/project/DATA_MODEL.md`
- `docs/project/TEST_STRATEGY.md`
- `docs/project/DEPLOYMENT.md`

## Framework Fit

The ZIP is compatible with the current MIL workflow for bootstrap use:

- It preserves SOP-first behavior and fail-closed inspection decisions.
- It keeps Windmill outside runtime PASS/NG decisions.
- It keeps Memory0 outside source-of-truth authority.
- It keeps product specs in config instead of hardcoded service logic.
- It treats model-dependent rules as `ASSIST`, `NOT_EVALUATED`, or blocked
  until validation and owner approval.

## Gaps Against Current MIL Startup Rules

The ZIP alone is not enough for app-code implementation because it does not
provide all current MIL startup artifacts:

- `docs/project/RISK_REGISTER.md`
- `docs/project/OPEN_QUESTIONS.md`
- `docs/project/SOURCE_OF_TRUTH.md`
- `docs/project/QUALITY_GATE_MATRIX.md`
- approved ADRs
- contract schemas and job manifests
- release/rollback evidence
- target repo and `repo_id`
- a DoR-ready GitHub issue with allowed files, required checks, rollback, and
  memory preflight

It also leaves implementation-affecting questions open:

- canonical package root: `src/flange_qc/**` or `apps/flange_qc_v2/**`
- branch naming convention when ZIP guidance conflicts with MIL AGENTS.md
- blocking CI checks for the first app skeleton
- QC/domain owner authority for product specs
- replay fixture and hardware validation source

## Bootstrap Action Taken

The ZIP product/tolerance table has been promoted into draft bootstrap config:

```text
configs/flange_qc_v2/product_specs.bootstrap.json
```

The SOP rule registry, open questions, and readiness evidence were updated to
reference the ZIP explicitly.

## Decision

The ZIP is enough to continue project bootstrap and planning. It is not enough to
start app-code implementation under the current MIL rules.

```aif-gate-result
{
  "schema_version": "2.0",
  "gate": "kickoff_zip_review",
  "status": "warn",
  "blocking": true,
  "decision": "BLOCKED_NEEDS_HUMAN",
  "reasons": [
    "zip_is_bootstrap_compatible",
    "current_mil_required_artifacts_are_not_all_present_in_zip",
    "target_repo_id_missing",
    "canonical_app_layout_unconfirmed",
    "definition_of_ready_issue_missing",
    "qc_product_spec_approval_missing"
  ],
  "tests": [
    "manual_document_review"
  ],
  "residual_risks": [
    "draft_product_specs_may_not_match_official_sop_revision",
    "first_implementation_scope_could_touch_wrong_repo_or_package_root_without_owner_confirmation",
    "replay_and_hardware_validation_sources_are_not_ready"
  ],
  "suggested_next": "create_or_approve_first_definition_of_ready_issue"
}
```
