# FQV2-047 QA Handoff: Health SOP Decision Engine Readiness

## Scope

- Branch: `agent/151-health-sop-decision-readiness`
- Task: FQV2-047
- Issue: https://github.com/namlogan/MIL/issues/151

## Files Changed

- `apps/flange_qc_v2/domain.py`
- `apps/flange_qc_v2/health.py`
- `tests/flange_qc_v2/test_health.py`
- `tests/flange_qc_v2/test_domain_contracts.py`
- `docs/project/flange_qc_v2/DATA_MODEL.md`
- `docs/project/flange_qc_v2/TEST_STRATEGY.md`
- `.ai-factory/gates/flange_qc_v2_fqv2_047_dor.json`
- `.ai-factory/qa/flange_qc_v2_fqv2_047_handoff_2026-06-03.md`

## Summary

- Changed bootstrap subsystem health from
  `sop_decision_engine=not_implemented` to
  `sop_decision_engine=shadow_implemented_requires_qc_sop_approval`.
- Added `qc_sop_tolerance_approval_missing` to `/health` blockers.
- Kept `/health` in `status=degraded`, `mode=bootstrap`, and
  `decision_authority=none`.
- Preserved product spec, QC/SOP tolerance, model, camera hardware, and
  production release approval gates.
- Updated data model and test strategy docs so readiness evidence matches the
  implemented shadow SOP phase logic without granting production authority.

## TDD Evidence

- RED:
  `python3 -m unittest tests.flange_qc_v2.test_health tests.flange_qc_v2.test_domain_contracts -v`
  failed because health/domain bootstrap still returned `not_implemented`.
- GREEN:
  the same focused suite passed after updating `apps/flange_qc_v2/domain.py`
  and `apps/flange_qc_v2/health.py`.

## Checks

- `python3 -m json.tool .ai-factory/gates/flange_qc_v2_fqv2_047_dor.json >/dev/null`
- `git diff --check`
- `python3 -m unittest tests.flange_qc_v2.test_health tests.flange_qc_v2.test_domain_contracts -v` passed, 9 tests.
- `python3 -m unittest tests.flange_qc_v2.test_decision_engine -v` passed, 11 tests.
- `python3 -m unittest tests.flange_qc_v2.test_hmi_stream -v` passed, 5 tests.
- `python3 -m unittest discover -s tests/flange_qc_v2 -v` passed, 160 tests.
- `python3 scripts/product-ci/run_product_checks.py` passed.

## HTTP Evidence

The local HMI preview was restarted on:

```text
http://127.0.0.1:8766/hmi
```

HTTP smoke for `/health` returned:

```json
{
  "decision_authority": "none",
  "mode": "bootstrap",
  "sop_decision_engine": "shadow_implemented_requires_qc_sop_approval",
  "status": "degraded"
}
```

The same smoke confirmed blockers include:

```json
[
  "qc_product_spec_approval_missing",
  "qc_sop_tolerance_approval_missing",
  "camera_hardware_validation_missing",
  "model_approval_missing",
  "audit_db_not_configured"
]
```

`/hmi` and `/detector/shadow/status` both returned HTTP 200 after the preview
restart.

## Restricted Change Check

No raw media, raw datasets, customer data, model weights, model binaries,
notebooks, model deserialization, inference runtime, camera SDK, live camera
capture, GPU use, secrets, credentials, destructive migrations, production
deploy/release, product spec approval, QC/SOP tolerance approval, model
promotion approval, production PASS/NG authority, production auto-reject
behavior, or Windmill credential/tunnel/runtime change is included.

## Residual Risks

- QC/SOP tolerance approval remains a human gate before production PASS/NG
  authority.
- Product spec approval, model promotion, camera hardware, and production
  release remain blocked until explicit owner/release approval.
- Runtime daily status may still report tmux relay/tunnel and Windmill CLI
  attention; this task intentionally does not touch secret-adjacent runtime
  credentials.

## Rollback

Revert the FQV2-047 PR to restore the previous health subsystem wording.
Existing decision engine, replay, HMI, artifact readiness, detector bridge, and
product CI behavior remain valid.

## Memory Candidate

- memory_type: task_lesson
- content: Health readiness should report implemented shadow SOP logic as
  `shadow_implemented_requires_qc_sop_approval`, while keeping
  `decision_authority=none` and QC/SOP approval blockers until human approval.
- source_ref: https://github.com/namlogan/MIL/issues/151
- why reusable: Future health/readiness endpoints should distinguish app logic
  implemented from production authority granted.
- scope: flange_qc_v2
- suggested status: candidate
