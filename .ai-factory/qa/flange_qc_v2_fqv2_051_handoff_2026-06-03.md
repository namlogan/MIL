# FQV2-051 QA Handoff: Phase 3 Shadow Observation Evidence

## Scope

- Branch: `agent/159-phase3-shadow-observation-evidence`
- Task: FQV2-051
- Issue: https://github.com/namlogan/MIL/issues/159

## Files Changed

- `apps/flange_qc_v2/decision_engine.py`
- `apps/flange_qc_v2/replay.py`
- `tests/flange_qc_v2/test_decision_engine.py`
- `tests/flange_qc_v2/test_replay.py`
- `tests/flange_qc_v2/test_hmi_stream.py`
- `docs/project/flange_qc_v2/DATA_MODEL.md`
- `docs/project/flange_qc_v2/TEST_STRATEGY.md`
- `docs/project/flange_qc_v2/USER_FLOWS.md`
- `docs/project/flange_qc_v2/SOP_RULE_REGISTRY.md`
- `.ai-factory/gates/flange_qc_v2_fqv2_051_dor.json`
- `.ai-factory/qa/flange_qc_v2_fqv2_051_handoff_2026-06-03.md`

## Summary

- Added `evaluate_phase_three_observations(...)` for sanitized detector
  observations.
- Phase 3 now returns `NOT_EVALUATED` with `MODEL_MISSING` when no observations
  are available.
- Relevant Phase 3 observations return `ASSIST` with `MODEL_REVIEW_REQUIRED`
  plus matched labels, confidence, bbox, and optional model/evidence refs.
- No-camera replay now routes frame `detector_observations` into Phase 3 SOP
  evidence.
- Phase 3 still cannot emit `PASS` or `NG`, cannot grant production authority,
  and keeps `MODEL_APPROVAL_REQUIRED` as the authority blocker.

## TDD Evidence

- RED:
  `python3 -m unittest tests.flange_qc_v2.test_decision_engine tests.flange_qc_v2.test_replay -v`
  failed because `evaluate_phase_three_observations` did not exist, replay Phase
  3 still used generic fallback evidence, and boundary replay without
  observations returned `ASSIST` instead of `NOT_EVALUATED`.
- GREEN:
  the same focused suite passed after adding the Phase 3 observation evaluator
  and routing replay frame observations through it.

## Checks

- `python3 -m json.tool .ai-factory/gates/flange_qc_v2_fqv2_051_dor.json` passed.
- `git diff --check` passed.
- `python3 -m unittest tests.flange_qc_v2.test_decision_engine tests.flange_qc_v2.test_replay tests.flange_qc_v2.test_hmi_stream -v` passed, 25 tests.
- `python3 -m unittest discover -s tests/flange_qc_v2 -v` passed, 169 tests.
- `python3 scripts/product-ci/run_product_checks.py` passed.

## HTTP And Browser Evidence

The local preview was restarted on:

```text
http://127.0.0.1:8766/hmi
```

with:

```text
FLANGE_QC_V2_ARTIFACT_INTAKE_DIR=templates/flange_qc_v2/artifact_intake
```

HTTP smoke for `/inspection/replay` returned:

```json
{
  "decision": "BLOCKED",
  "inspection_id": "fqv2-phase2-synthetic-001",
  "matched_labels": ["punch_mark"],
  "max_confidence": 0.87,
  "observations_count": 1,
  "phase_production_authority": [false, false, false, false],
  "phase_three_authority_blockers": ["MODEL_APPROVAL_REQUIRED"],
  "phase_three_decision": "ASSIST",
  "phase_three_reason_codes": ["MODEL_REVIEW_REQUIRED"],
  "phase_three_rule": "M1-SOP-6.4-PUNCH-MARK-001",
  "replay_status": 200
}
```

Browser HMI verification at `http://127.0.0.1:8766/hmi` showed:

```json
{
  "decision": "BLOCKED",
  "inspectionId": "fqv2-phase2-synthetic-001",
  "observationState": "present",
  "operatorState": "check",
  "stitchScopeDetail": "punch_mark / 0.87",
  "stitchScopeStatus": "CHECK"
}
```

## Restricted Change Check

No raw media, raw datasets, customer/factory data, notebooks, model weights,
model binaries, model deserialization, inference runtime, camera SDK, live
camera capture, GPU use, secrets, credentials, destructive migrations,
production deploy/release, product spec approval, QC/SOP tolerance approval,
model promotion approval, production PASS/NG authority, production auto-reject
behavior, request-supplied file paths, or Windmill credential/tunnel/runtime
change is included.

## Residual Risks

- Phase 3 observations remain review-only until model approval and production
  release gates pass.
- Product specs and tolerances remain draft until QC/domain owner approval.
- Live camera capture, real calibration, and model inference remain blocked
  until hardware/artifact gates are approved.
- Runtime daily status may still report tmux relay/tunnel or Windmill attention;
  this task intentionally does not touch secret-adjacent runtime credentials.

## Rollback

Revert the FQV2-051 PR to restore Phase 3 to generic safe fallback evidence
only. Existing Phase 1/2 measurement logic, HMI signal layout, replay, detector
bridge, and product CI behavior remain valid.

## Memory Candidate

- memory_type: task_lesson
- content: Phase 3 should consume sanitized detector observations as
  shadow-only SOP evidence: no observations are `NOT_EVALUATED/MODEL_MISSING`,
  relevant observations are `ASSIST/MODEL_REVIEW_REQUIRED`, and production
  authority remains false.
- source_ref: https://github.com/namlogan/MIL/issues/159
- why reusable: Future MLOps/model and live-camera work can feed the same
  observation contract without changing production gate policy.
- scope: flange_qc_v2
- suggested status: candidate
