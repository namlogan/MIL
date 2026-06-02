# FQV2-009 QA Handoff: Replay Frame Source And No-Camera E2E

## Source

- GitHub issue: https://github.com/namlogan/MIL/issues/75
- Branch: `agent/75-replay-frame-source-no-camera-e2e`
- Task: FQV2-009

## Files Changed

- `apps/flange_qc_v2/replay.py`
- `samples/replay/flange_qc_v2/phase2_synthetic_measurements.json`
- `tests/flange_qc_v2/test_replay.py`
- `docs/project/flange_qc_v2/DATA_MODEL.md`
- `.ai-factory/gates/flange_qc_v2_fqv2_009_dor.json`
- `.ai-factory/qa/flange_qc_v2_fqv2_009_handoff_2026-06-02.md`

## Rules Applied

- One task per branch.
- GitHub issue is source of truth for requirement, acceptance criteria, and allowed paths.
- TDD red/green was used before implementation.
- Replay data is synthetic metadata only.
- No live camera, raw media, model, customer data, or production deploy behavior is introduced.

## Implementation Notes

- Added `load_replay_manifest` for synthetic no-camera replay manifests.
- Added `run_no_camera_replay` to connect product specs, calibration, geometry, and phase-2 decision evidence.
- Current bootstrap config returns `BLOCKED` because product specs and calibration lack production authority.
- Replay frames expose frame ID, synthetic source URI, timestamp, and measurement payload.

## Tests Run

- `python3 -m unittest tests.flange_qc_v2.test_replay -v`

Additional required checks before PR review:

- `python3 -m unittest discover -s tests/flange_qc_v2 -v`
- `python3 -m compileall -q apps/flange_qc_v2 tests/flange_qc_v2`
- `python3 scripts/product-ci/run_product_checks.py`
- `python3 -m unittest discover -s tests -v`
- `git diff --check`

## Residual Risks

- Replay source is synthetic metadata only, not real media playback.
- WebSocket/HMI streaming is not implemented in this task.
- Product spec approval and calibration approval remain required for production.
- Shadow PASS/NG remains non-production authority.

## Rollback

Revert the FQV2-009 PR to remove the replay loader/runner, synthetic manifest,
tests, and evidence artifacts. This task does not alter production data,
migrations, secrets, or deploy configuration.

## Memory Candidate

- memory_type: implementation_lesson
- content: Flange QC v2 no-camera replay should use synthetic metadata-only manifests and fail closed while product specs/calibration are unapproved.
- source_ref: https://github.com/namlogan/MIL/issues/75
- why reusable: Future replay API, WebSocket, HMI, and audit tasks need this no-camera boundary.
- scope: project:flange_qc_v2
- suggested status: candidate
