# FQV2-012 QA Handoff: QC Feedback Shadow Evidence

## Source

- GitHub issue: https://github.com/namlogan/MIL/issues/81
- Branch: `agent/81-qc-feedback-shadow-evidence`
- Task: FQV2-012

## Files Changed

- `apps/flange_qc_v2/feedback.py`
- `apps/flange_qc_v2/audit.py`
- `apps/flange_qc_v2/asgi.py`
- `contracts/flange_qc_v2/feedback/qc_feedback.schema.json`
- `tests/flange_qc_v2/test_feedback.py`
- `docs/project/flange_qc_v2/DATA_MODEL.md`
- `.ai-factory/gates/flange_qc_v2_fqv2_012_dor.json`
- `.ai-factory/qa/flange_qc_v2_fqv2_012_handoff_2026-06-02.md`

## Rules Applied

- One task per branch.
- GitHub issue is source of truth for requirement, acceptance criteria, and allowed paths.
- TDD red/green was used before implementation.
- QC feedback is shadow evidence only and cannot approve production.
- Production release/deploy, secrets, customer data, product spec approval, QC/SOP tolerance approval, and destructive migrations remain human gates.

## Memory Preflight

- Query: Flange QC v2 issue #81 feedback/shadow evidence, prior HMI/audit packages, MIL agent workflow.
- Retrieved decisions: product spec approval and QC/SOP tolerance approval remain human gates; shadow PASS/NG/BLOCKED evidence cannot grant production authority; audit evidence is append-only for bootstrap/replay.
- Retrieved lessons: start each package from a GitHub issue with DoR evidence; use TDD red/green before implementation; keep restricted gates outside routine automation.
- Restricted areas: production release/deploy, secrets, customer data, destructive migrations, QC/SOP tolerance approval, product spec approval authority.
- Conflicts found: none.
- Sources to verify: GitHub issue #81, AGENTS.md, `.ai-factory/RULES.md`, `docs/project/flange_qc_v2/DATA_MODEL.md`.

## Implementation Notes

- Added a QC feedback domain object and JSON payload contract.
- Supported feedback types are `CONFIRM_BLOCKED`, `MARK_FALSE_POSITIVE`, `MARK_FALSE_NEGATIVE`, and `REQUEST_REVIEW`.
- Feedback payloads always set `production_authority` to `false` and include `PRODUCTION_APPROVAL_REQUIRED`.
- Added append-only persistence and fetch helpers for the existing `qc_feedback` audit table.
- Added `POST /feedback` JSON validation that returns shadow evidence or rejects invalid payloads with HTTP 400.

## Tests Run

- `python3 -m unittest tests.flange_qc_v2.test_feedback -v`
- `python3 -m unittest discover -s tests/flange_qc_v2 -v`
- `python3 -m compileall -q apps/flange_qc_v2 tests/flange_qc_v2`
- `python3 scripts/product-ci/run_product_checks.py`
- `python3 -m unittest discover -s tests -v`
- `git diff --check`

## Residual Risks

- Feedback capture UI is not implemented in this task.
- Feedback evidence does not resolve product spec approval or QC/SOP tolerance approval.
- Feedback has no production PASS/NG authority and cannot approve release/deploy.
- Production retention/export/backup policy still requires approval before release.

## Rollback

Revert the FQV2-012 PR to remove the QC feedback contract, endpoint validation,
audit helpers, tests, and evidence artifacts. This task uses the existing
`qc_feedback` table and does not alter production data, secrets, deploy
configuration, or destructive migrations.

## Memory Candidate

- memory_type: implementation_lesson
- content: Flange QC v2 QC feedback is modeled as append-only shadow evidence with explicit production authority blockers.
- source_ref: https://github.com/namlogan/MIL/issues/81
- why reusable: Future feedback UI, QC review, and release readiness tasks need this boundary.
- scope: project:flange_qc_v2
- suggested status: candidate
