# FQV2-006 Handoff Evidence

Date: 2026-06-02

## Task

GitHub issue: <https://github.com/namlogan/MIL/issues/69>

Branch:

```text
agent/69-calibration-synthetic-validator
```

## Summary

Adds bootstrap calibration config validation for Flange QC v2. The validator
loads the synthetic calibration fixture, exposes camera and lighting metadata,
and keeps production authority blocked with `CALIBRATION_MISSING`.

This task does not validate live hardware, approve production calibration, or
perform geometry correction.

## Files Changed

- `apps/flange_qc_v2/calibration.py`
- `tests/flange_qc_v2/test_calibration.py`
- `docs/project/flange_qc_v2/DATA_MODEL.md`
- `.ai-factory/gates/flange_qc_v2_fqv2_006_dor.json`
- `.ai-factory/qa/flange_qc_v2_fqv2_006_handoff_2026-06-02.md`

## Rules Applied

- GitHub issue is the task source of truth.
- One task branch is used.
- Codex is the implementation worker.
- TDD red/green was used for calibration behavior.
- No production deploy, secrets, customer data policy, destructive migrations,
  live camera validation, production calibration approval, geometry correction,
  model weights, TensorRT engines, or production SOP PASS/NG logic were added.

## Tests Run

```text
python3 -m unittest tests.flange_qc_v2.test_calibration -v
python3 -m unittest discover -s tests/flange_qc_v2 -v
python3 -m compileall -q apps/flange_qc_v2 tests/flange_qc_v2
python3 scripts/product-ci/run_product_checks.py
python3 -m unittest discover -s tests -v
git diff --check
```

## Residual Risks

- Synthetic calibration is bootstrap/replay diagnostic evidence only.
- Live hardware validation and production calibration approval remain future
  gated work.
- Geometry correction remains future work.

## Rollback

Revert the FQV2-006 PR to remove calibration loader/validator, tests, and
evidence. Existing earlier Flange QC v2 packages can remain intact.

## Memory Candidate

- memory_type: implementation_lesson
- content: Flange QC v2 calibration validation lives in
  `apps/flange_qc_v2/calibration.py`; synthetic fixtures expose camera/lighting
  metadata but return `production_authority=false` and `BLOCKED`.
- source_ref: GitHub issue #69 and the FQV2-006 PR
- why reusable: Future geometry and replay work should call this validator
  instead of treating synthetic calibration as production-ready.
- scope: project
- suggested status: candidate

## AIF Gate Result

```text
aif-gate-result:
  decision: APPROVE_MERGE
  reasons:
    - Calibration scope is synthetic/bootstrap validation only.
    - Invalid camera/lighting config shape is rejected.
    - Production calibration authority remains blocked.
  tests:
    - python3 -m unittest tests.flange_qc_v2.test_calibration -v
    - python3 -m unittest discover -s tests/flange_qc_v2 -v
  residual_risks:
    - Live camera validation remains future work.
    - Production calibration approval remains a future human/domain gate.
```
