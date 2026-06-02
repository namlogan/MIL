# FQV2-026 QA Handoff: SOP Phase Results in Replay/HMI

## Source

- GitHub issue: https://github.com/namlogan/MIL/issues/109
- Branch: `agent/109-sop-phase-results-hmi-replay`
- Task: FQV2-026

## Files Changed

- `apps/flange_qc_v2/replay.py`
- `apps/flange_qc_v2/hmi_stream.py`
- `apps/flange_qc_v2/domain.py`
- `contracts/flange_qc_v2/websocket/inspection_snapshot.schema.json`
- `tests/flange_qc_v2/test_replay.py`
- `tests/flange_qc_v2/test_hmi_stream.py`
- `tests/flange_qc_v2/test_domain_contracts.py`
- `docs/project/flange_qc_v2/DATA_MODEL.md`
- `docs/project/flange_qc_v2/USER_FLOWS.md`
- `docs/project/flange_qc_v2/TEST_STRATEGY.md`
- `.ai-factory/gates/flange_qc_v2_fqv2_026_dor.json`
- `.ai-factory/qa/flange_qc_v2_fqv2_026_handoff_2026-06-02.md`

## Rules Applied

- One task per branch.
- GitHub issue is source of truth for requirement, acceptance criteria, and
  allowed paths.
- TDD RED/GREEN checkpoints were used before implementation.
- Snapshot integration is no-camera replay only; no model/camera execution or
  production authority is introduced.
- No HMI redesign, live camera, raw media, customer data, model loading,
  dataset ingestion, secrets, destructive migration, deployment, production
  PASS/NG authority, or production auto-reject behavior is introduced.

## Implementation Notes

- `run_no_camera_replay()` now evaluates Phase 1, Phase 2, Phase 3, and Phase 4
  in order.
- `ReplayRunResult.to_payload()` includes ordered `phase_results`.
- Replay top-level `decision` is now a `FINAL` aggregate with fail-closed
  priority: `BLOCKED`, `NG`, `ASSIST`, `NOT_EVALUATED`, then `PASS`.
- `InspectionSnapshot` now serializes and parses `phase_results`.
- HMI HTTP/WebSocket snapshots include the full phase chain while preserving
  top-level `phase`, `decision`, and `reason_codes`.
- WebSocket snapshot schema now requires `phase_results` and documents phase
  result and rule result fields.
- Audit storage keeps the full snapshot payload, including phase results,
  without migration because payload JSON is already persisted as a JSON blob.

## Tests Run

- RED: `python3 -m unittest tests.flange_qc_v2.test_replay -v` failed because
  replay was still `PHASE_2` and lacked `phase_results`.
- RED: `python3 -m unittest tests.flange_qc_v2.test_hmi_stream -v` failed
  because HMI/audit payloads lacked `phase_results`.
- RED: `python3 -m unittest tests.flange_qc_v2.test_domain_contracts -v`
  failed because snapshot/domain schema lacked `phase_results`.
- GREEN: `python3 -m unittest tests.flange_qc_v2.test_replay -v` passed, 3
  tests.
- GREEN: `python3 -m unittest tests.flange_qc_v2.test_hmi_stream -v` passed, 4
  tests.
- GREEN: `python3 -m unittest tests.flange_qc_v2.test_domain_contracts -v`
  passed, 6 tests.
- `python3 -m compileall -q apps/flange_qc_v2 tests/flange_qc_v2` passed.
- `python3 -m json.tool .ai-factory/gates/flange_qc_v2_fqv2_026_dor.json >/dev/null`
  passed.
- `git diff --check` passed.
- `python3 -m unittest discover -s tests/flange_qc_v2 -v` passed, 115 tests.
- `python3 scripts/product-ci/run_product_checks.py` passed.
- `python3 -m unittest discover -s tests -v` passed, 196 tests.

## Residual Risks

- The HMI visual screen still does not render phase-result detail panes; the
  payload now carries the data for a later UI issue.
- Product specs, QC/SOP tolerances, model approval/promotion, live camera
  readiness, and production release remain human-gated.
- Current replay remains synthetic/no-camera and does not prove live factory
  image, camera, or model behavior.

## Rollback

Revert the FQV2-026 PR to remove `phase_results` contract and replay/HMI
wiring. Existing audit records remain valid JSON snapshots; no destructive
migration, model rollback, hardware rollback, or deploy rollback is required.

## Memory Candidate

- memory_type: implementation_lesson
- content: Flange QC v2 no-camera replay and HMI snapshots now carry ordered
  SOP phase_results for Phase 1 through Phase 4 plus a fail-closed FINAL
  aggregate decision.
- source_ref: https://github.com/namlogan/MIL/issues/109
- why reusable: Future HMI UI, audit drill-down, and model integration can read
  full phase evidence from the snapshot payload without enabling production
  authority.
- scope: project:flange_qc_v2
- suggested status: candidate
