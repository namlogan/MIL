# FQV2-020 QA Handoff: HMI Feedback Audit Trail

## Source

- GitHub issue: https://github.com/namlogan/MIL/issues/97
- Branch: `agent/97-hmi-feedback-audit-trail`
- Task: FQV2-020

## Files Changed

- `apps/flange_qc_v2/audit.py`
- `apps/flange_qc_v2/asgi.py`
- `apps/flange_qc_v2/static/hmi.html`
- `tests/flange_qc_v2/test_feedback.py`
- `tests/flange_qc_v2/test_hmi_screen.py`
- `tests/flange_qc_v2/test_hmi_stream.py`
- `docs/project/flange_qc_v2/USER_FLOWS.md`
- `docs/project/flange_qc_v2/DATA_MODEL.md`
- `.ai-factory/gates/flange_qc_v2_fqv2_020_dor.json`
- `.ai-factory/qa/flange_qc_v2_fqv2_020_handoff_2026-06-02.md`

## Rules Applied

- One task per branch.
- GitHub issue is source of truth for requirement, acceptance criteria, and allowed paths.
- TDD RED/GREEN checkpoints were used before implementation.
- Audit persistence is local replay/shadow evidence only.
- No production release/deploy, secrets, customer data, raw media, live camera
  capture, hardware validation, model promotion, destructive migration,
  production DB migration behavior, product spec approval, QC/SOP tolerance
  approval, production PASS/NG authority, or production auto-reject is
  introduced.

## Memory Preflight

- Query: Flange QC v2 HMI feedback durable audit persistence, issue #97, FQV2-019 residual risk, no-camera replay audit store.
- Retrieved decisions: feedback is shadow-only; audit store already supports append-only inspection and qc_feedback records; durable HMI feedback persistence was a recorded FQV2-019 residual risk.
- Retrieved lessons: no-camera work should improve operator usefulness while hardware is unavailable; keep production and hardware gates explicit.
- Restricted areas: production release/deploy, secrets/customer data/raw media, live camera/hardware validation, model promotion, destructive migrations, production DB migration behavior, QC/SOP tolerance approval, product spec approval, production PASS/NG authority.
- Conflicts found: none.
- Sources to verify: issue #97, AGENTS.md, `.ai-factory/RULES.md`, MVP scope, data model, audit store, ASGI app, FQV2-019 handoff.

## Implementation Notes

- Added `AuditStore.ensure_inspection()` so repeated replay refreshes do not
  fail on duplicate inspection IDs.
- Added ASGI audit persistence controlled by `FLANGE_QC_V2_AUDIT_DB_PATH`.
- `GET /inspection/replay` initializes the audit store and records the current
  replay inspection idempotently when the audit path is configured.
- `POST /feedback` validates payloads first, then stores valid feedback in
  `qc_feedback` when the audit path is configured.
- Invalid feedback payloads are rejected before audit feedback writes.
- `/feedback` response includes audit evidence when persistence is active:
  `audit.persisted=true` and `audit.feedback_count`.
- HMI feedback status renders audit persistence status when the response
  includes audit evidence, while preserving no-audit behavior.

## Tests Run

- `python3 -m unittest tests.flange_qc_v2.test_hmi_stream -v`
- `python3 -m unittest tests.flange_qc_v2.test_feedback -v`
- `python3 -m unittest tests.flange_qc_v2.test_hmi_screen -v`
- `python3 -m unittest discover -s tests/flange_qc_v2 -v`
- `python3 -m compileall -q apps/flange_qc_v2 tests/flange_qc_v2`
- `python3 scripts/product-ci/run_product_checks.py`
- `python3 -m unittest discover -s tests -v`
- `git diff --check`

## Browser Evidence

- Local HMI was exercised at `http://127.0.0.1:8765/hmi` using a local no-camera
  server with `FLANGE_QC_V2_AUDIT_DB_PATH` pointing to
  `.ai-factory/tmp/flange_qc_v2/fqv2_020_browser_audit.sqlite`.
- HMI element counts were exactly one each for refresh, feedback form,
  feedback status, reviewer input, feedback type select, note textarea, and
  submit button.
- Replay refresh kept the decision at `BLOCKED` for
  `fqv2-phase2-synthetic-001`.
- Feedback submit returned `CONFIRM_BLOCKED saved for
  fqv2-phase2-synthetic-001 / audit 1`.
- Feedback status state was `ok`.
- `production_authority` rendered as `false`.
- `authority_blockers` rendered as `PRODUCTION_APPROVAL_REQUIRED`.
- Browser console/page errors: none.
- Runtime audit DB check found inspection `fqv2-phase2-synthetic-001`,
  `feedback_count=1`, and `last_feedback_type=CONFIRM_BLOCKED`.

## Residual Risks

- Physical camera is still unavailable and live hardware validation is not run.
- Product specs and QC/SOP tolerances remain unapproved for production-bound
  behavior.
- The audit DB path is local replay/shadow evidence only; production retention,
  export, backup, privacy, and destructive migration rules remain unapproved.
- Production release/deploy remains blocked pending release evidence and human
  approval.

## Rollback

Revert the FQV2-020 PR to remove audit persistence wiring, HMI audit status
display, tests, docs, and gate evidence. This task does not alter production
data, destructive migrations, secrets, deploy configuration, hardware state, raw
media, customer data, product spec approval, QC/SOP tolerance approval, or
production PASS/NG authority.

## Memory Candidate

- memory_type: implementation_lesson
- content: Flange QC v2 no-camera HMI feedback can be persisted as local shadow audit evidence via `FLANGE_QC_V2_AUDIT_DB_PATH` without approving production retention, hardware, SOP, or release gates.
- source_ref: https://github.com/namlogan/MIL/issues/97
- why reusable: Future operator dry-runs can enable local audit persistence while keeping production data and release decisions gated.
- scope: project:flange_qc_v2
- suggested status: candidate
