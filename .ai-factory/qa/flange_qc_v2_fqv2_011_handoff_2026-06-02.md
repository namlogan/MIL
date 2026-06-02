# FQV2-011 QA Handoff: Minimum HMI Screen

## Source

- GitHub issue: https://github.com/namlogan/MIL/issues/79
- Branch: `agent/79-minimum-hmi-screen`
- Task: FQV2-011

## Files Changed

- `apps/flange_qc_v2/static/hmi.html`
- `apps/flange_qc_v2/asgi.py`
- `tests/flange_qc_v2/test_hmi_screen.py`
- `docs/project/flange_qc_v2/DATA_MODEL.md`
- `.ai-factory/gates/flange_qc_v2_fqv2_011_dor.json`
- `.ai-factory/qa/flange_qc_v2_fqv2_011_handoff_2026-06-02.md`

## Rules Applied

- One task per branch.
- GitHub issue is source of truth for requirement, acceptance criteria, and allowed paths.
- TDD red/green was used before implementation.
- Frontend is the actual HMI screen, not a landing page.
- QC feedback, live camera, raw media, production deploy, and production authority remain out of scope.

## Implementation Notes

- Added `/hmi` served HTML screen.
- Screen connects to `/ws/inspection` and renders the replay-backed `inspection.snapshot` payload.
- Shows connection state, phase, decision, reason codes, product/spec, measurements, inspection metadata, frame source, unit, and observations state.
- Current bootstrap payload displays `BLOCKED` evidence from missing product spec approval and calibration approval.

## Tests Run

- `python3 -m unittest tests.flange_qc_v2.test_hmi_screen -v`
- `python3 -m unittest tests.flange_qc_v2.test_hmi_stream tests.flange_qc_v2.test_health -v`

Additional required checks before PR review:

- `python3 -m unittest discover -s tests/flange_qc_v2 -v`
- `python3 -m compileall -q apps/flange_qc_v2 tests/flange_qc_v2`
- `python3 scripts/product-ci/run_product_checks.py`
- `python3 -m unittest discover -s tests -v`
- `git diff --check`
- Browser smoke for `/hmi`

## Residual Risks

- QC feedback submission is not implemented in this task.
- The screen uses the current one-payload WebSocket stream; continuous streaming is future work.
- Product spec approval and calibration approval remain required for production.
- Shadow PASS/NG remains non-production authority.

## Rollback

Revert the FQV2-011 PR to remove the HMI screen, ASGI static serving change,
tests, and evidence artifacts. This task does not alter production data,
migrations, secrets, or deploy configuration.

## Memory Candidate

- memory_type: implementation_lesson
- content: Flange QC v2 minimum HMI screen is served at /hmi and renders the replay-backed inspection.snapshot from /ws/inspection as blocked bootstrap evidence.
- source_ref: https://github.com/namlogan/MIL/issues/79
- why reusable: Future feedback, continuous stream, and release tasks need this UI boundary.
- scope: project:flange_qc_v2
- suggested status: candidate
