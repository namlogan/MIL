# FQV2-019 QA Handoff: No-Camera Operator Feedback Loop

## Source

- GitHub issue: https://github.com/namlogan/MIL/issues/95
- Branch: `agent/95-no-camera-operator-loop`
- Task: FQV2-019

## Files Changed

- `apps/flange_qc_v2/asgi.py`
- `apps/flange_qc_v2/static/hmi.html`
- `tests/flange_qc_v2/test_hmi_stream.py`
- `tests/flange_qc_v2/test_hmi_screen.py`
- `tests/flange_qc_v2/test_feedback.py`
- `docs/project/flange_qc_v2/USER_FLOWS.md`
- `docs/project/flange_qc_v2/DATA_MODEL.md`
- `.ai-factory/gates/flange_qc_v2_fqv2_019_dor.json`
- `.ai-factory/qa/flange_qc_v2_fqv2_019_handoff_2026-06-02.md`

## Rules Applied

- One task per branch.
- GitHub issue is source of truth for requirement, acceptance criteria, and allowed paths.
- TDD red/green checkpoints were used before app-code implementation.
- Camera hardware is pending; this task stays in synthetic replay/no-camera mode.
- QC feedback remains shadow evidence only and cannot approve production.
- No deploy, secrets, live camera capture, raw media, customer data, model promotion,
  product spec approval, QC/SOP tolerance approval, or production PASS/NG
  authority is introduced.

## Memory Preflight

- Query: Flange QC v2 no-camera HMI replay feedback loop, issue #95, shadow feedback contract, hardware pending.
- Retrieved decisions: camera hardware is pending; no-camera replay work may continue; feedback is shadow-only; GitHub/docs/tests/PR evidence remain source of truth.
- Retrieved lessons: expose authority blockers clearly; keep operator replay flows useful while hardware is unavailable; use TDD checkpoints.
- Restricted areas: production release/deploy, secrets, customer data, raw media, live camera/hardware validation, Hikrobot SDK/credentials, model/TensorRT promotion, destructive migrations, QC/SOP tolerance approval, product spec approval, production PASS/NG authority.
- Conflicts found: none.
- Sources to verify: issue #95, AGENTS.md, `.ai-factory/RULES.md`, HMI stream contract, feedback contract, user-flow/data-model docs.

## Implementation Notes

- Added `GET /inspection/replay` to return the current replay-backed
  `inspection.snapshot` contract as JSON.
- Added an HMI refresh action that reloads the replay snapshot without camera
  hardware.
- Added an HMI feedback form for reviewer ID, feedback type, and note.
- HMI feedback submits the current inspection ID and shadow decision to
  `/feedback`.
- The feedback status panel displays `production_authority` and
  `authority_blockers`.
- Invalid local submissions and HTTP validation failures render an operator
  visible error state.

## Tests Run

- `python3 -m unittest tests.flange_qc_v2.test_hmi_stream -v`
- `python3 -m unittest tests.flange_qc_v2.test_hmi_screen -v`
- `python3 -m unittest tests.flange_qc_v2.test_feedback -v`
- `python3 -m unittest discover -s tests/flange_qc_v2 -v`
- `python3 -m compileall -q apps/flange_qc_v2 tests/flange_qc_v2`
- `python3 scripts/product-ci/run_product_checks.py`
- `python3 -m unittest discover -s tests -v`
- `git diff --check`

## Browser Evidence

- Local HMI was exercised at `http://127.0.0.1:8766/hmi` using a local no-camera
  test server for the current branch code. The previous `8765` server was a
  static-only process and did not expose the new API route.
- HMI element counts were exactly one each for refresh, feedback form,
  feedback status, reviewer input, feedback type select, note textarea, and
  submit button.
- Replay refresh kept the decision at `BLOCKED` for
  `fqv2-phase2-synthetic-001`.
- Feedback submit returned `CONFIRM_BLOCKED saved for
  fqv2-phase2-synthetic-001`.
- Feedback status state was `ok`.
- `production_authority` rendered as `false`.
- `authority_blockers` rendered as `PRODUCTION_APPROVAL_REQUIRED`.
- Browser console/page errors after favicon fix: none.

## Residual Risks

- Physical camera is still unavailable and live hardware validation is not run.
- Product specs and QC/SOP tolerances remain unapproved for production-bound
  behavior.
- HTTP `/feedback` validates and returns shadow evidence; connecting HMI
  submissions to durable audit persistence remains a later scoped task.
- Production release/deploy remains blocked pending release evidence and human
  approval.

## Rollback

Revert the FQV2-019 PR to remove the replay HTTP endpoint, HMI refresh/feedback
UI, tests, docs, and evidence artifacts. This task does not alter production
data, migrations, secrets, deploy configuration, live camera hardware, raw
media, customer data, product spec approval, QC/SOP tolerance approval, or
production PASS/NG authority.

## Memory Candidate

- memory_type: implementation_lesson
- content: Flange QC v2 can continue product progress without camera hardware by using no-camera replay refresh and shadow-only HMI feedback that exposes production authority blockers.
- source_ref: https://github.com/namlogan/MIL/issues/95
- why reusable: Future no-camera packages should preserve operator value while keeping hardware, spec, QC/SOP, and production release gates blocked.
- scope: project:flange_qc_v2
- suggested status: candidate
