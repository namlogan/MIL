# FQV2-010 QA Handoff: WebSocket HMI Payload Stream

## Source

- GitHub issue: https://github.com/namlogan/MIL/issues/77
- Branch: `agent/77-websocket-hmi-payload-stream`
- Task: FQV2-010

## Files Changed

- `apps/flange_qc_v2/hmi_stream.py`
- `apps/flange_qc_v2/asgi.py`
- `tests/flange_qc_v2/test_hmi_stream.py`
- `docs/project/flange_qc_v2/DATA_MODEL.md`
- `.ai-factory/gates/flange_qc_v2_fqv2_010_dor.json`
- `.ai-factory/qa/flange_qc_v2_fqv2_010_handoff_2026-06-02.md`

## Rules Applied

- One task per branch.
- GitHub issue is source of truth for requirement, acceptance criteria, and allowed paths.
- TDD red/green was used before implementation.
- Existing WebSocket inspection snapshot contract remains the payload source of truth.
- No HMI UI, live camera, raw media, production deploy, or production authority is introduced.

## Implementation Notes

- Added `build_replay_inspection_snapshot` to convert the no-camera replay result into `InspectionSnapshot`.
- Extended ASGI app to support `/ws/inspection`.
- The WebSocket endpoint accepts, sends one `inspection.snapshot` JSON payload, and closes with code 1000.
- Current bootstrap data still sends `BLOCKED` because product spec and calibration authority are missing.

## Tests Run

- `python3 -m unittest tests.flange_qc_v2.test_hmi_stream -v`
- `python3 -m unittest tests.flange_qc_v2.test_health -v`

Additional required checks before PR review:

- `python3 -m unittest discover -s tests/flange_qc_v2 -v`
- `python3 -m compileall -q apps/flange_qc_v2 tests/flange_qc_v2`
- `python3 scripts/product-ci/run_product_checks.py`
- `python3 -m unittest discover -s tests -v`
- `git diff --check`

## Residual Risks

- HMI screen/UI is not implemented in this task.
- Endpoint sends one replay-backed payload per connection; continuous streaming is future work.
- Product spec approval and calibration approval remain required for production.
- Shadow PASS/NG remains non-production authority.

## Rollback

Revert the FQV2-010 PR to remove the HMI stream builder, WebSocket endpoint
change, tests, and evidence artifacts. This task does not alter production data,
migrations, secrets, or deploy configuration.

## Memory Candidate

- memory_type: implementation_lesson
- content: Flange QC v2 bootstrap WebSocket stream sends one replay-backed inspection.snapshot payload from synthetic no-camera replay and closes cleanly.
- source_ref: https://github.com/namlogan/MIL/issues/77
- why reusable: Future HMI screen and continuous stream tasks need this contract boundary.
- scope: project:flange_qc_v2
- suggested status: candidate
