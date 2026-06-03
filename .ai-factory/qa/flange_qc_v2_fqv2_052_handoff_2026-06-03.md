# FQV2-052 QA Handoff: Parallel QC Terminology Alignment

## Scope

- Branch: `agent/161-parallel-qc-terminology`
- Task: FQV2-052
- Issue: https://github.com/namlogan/MIL/issues/161

## Files Changed

- `apps/flange_qc_v2/static/hmi.html`
- `apps/flange_qc_v2/health.py`
- `apps/flange_qc_v2/domain.py`
- `tests/flange_qc_v2/test_hmi_screen.py`
- `tests/flange_qc_v2/test_health.py`
- `tests/flange_qc_v2/test_domain_contracts.py`
- `docs/project/flange_qc_v2/DATA_MODEL.md`
- `docs/project/flange_qc_v2/USER_FLOWS.md`
- `docs/project/flange_qc_v2/TEST_STRATEGY.md`
- `.ai-factory/gates/flange_qc_v2_fqv2_052_dor.json`
- `.ai-factory/qa/flange_qc_v2_fqv2_052_handoff_2026-06-03.md`

## Summary

- Defined `shadow` in docs as an internal compatibility term for the
  parallel-QC operating lane that runs beside real human QC.
- Updated HMI operator-facing readiness labels from `Shadow Model` and detector
  shadow wording to `Model Assist`, `Parallel QC`, and `Review-only`.
- Added HMI mapping for internal readiness tasks/actions so operators see
  `parallel QC observation review`, `submit observation evidence`, and
  `collect more QC feedback` instead of raw internal task IDs.
- Updated health/domain bootstrap states to
  `parallel_qc_implemented_requires_qc_sop_approval` and
  `manifest_ready_parallel_qc_only`.
- Preserved existing internal IDs, schema fields, audit fields, endpoint paths,
  and contract names such as `/detector/shadow/status`, `shadow_mode`, and
  `shadow_decision`.

## TDD Evidence

- RED 1:
  `python3 -m unittest tests.flange_qc_v2.test_hmi_screen tests.flange_qc_v2.test_health tests.flange_qc_v2.test_domain_contracts -v`
  failed because HMI visible text still used `Shadow Model` /
  `Detector shadow status`, and health/domain still reported shadow-only state
  names.
- GREEN 1:
  the same focused suite passed after updating HMI labels, health/domain state
  strings, and docs.
- RED 2:
  `python3 -m unittest tests.flange_qc_v2.test_hmi_screen -v`
  failed because the HMI had no task/action label mapper for internal
  `shadow_observation_review` and `submit_shadow_observation_payload`.
- GREEN 2:
  the same HMI suite passed after adding `formatTaskLabel`,
  `formatActionLabel`, and `formatReadinessState`.

## Checks

- `python3 -m unittest tests.flange_qc_v2.test_hmi_screen tests.flange_qc_v2.test_health tests.flange_qc_v2.test_domain_contracts -v` passed, 21 tests.
- `python3 -m unittest discover -s tests/flange_qc_v2 -v` passed, 170 tests.
- `python3 -m compileall -q apps/flange_qc_v2 tests/flange_qc_v2` passed.
- `python3 scripts/product-ci/run_product_checks.py` passed.
- `python3 -m unittest discover -s tests -v` passed, 196 tests.
- `git diff --check` passed.

## Browser Evidence

The local preview was already available at:

```text
http://127.0.0.1:8766/hmi
```

Browser smoke after reload returned:

```json
{
  "textIncludes": {
    "parallelQc": true,
    "modelAssist": true,
    "reviewOnly": true,
    "shadowModel": false,
    "rawShadowObservationReview": false,
    "rawSubmitShadowPayload": false,
    "detectorShadowStatusAria": false,
    "detectorParallelAria": true
  },
  "nextTask": "parallel QC observation review",
  "readinessLabel": "Model Assist\nready for parallel QC observation review",
  "readinessActions": [
    "submit observation evidence",
    "schedule camera hardware readiness",
    "collect more QC feedback",
    "keep production release blocked"
  ],
  "detectorStatus": "Review-only ready: manifest-detector",
  "operatorState": "check",
  "decision": "BLOCKED",
  "stitchScopeStatus": "CHECK"
}
```

## Restricted Change Check

No raw media, raw datasets, customer/factory data, notebooks, model weights,
model binaries, model deserialization, inference runtime, camera SDK, live
camera capture, GPU use, secrets, credentials, destructive migrations,
production deploy/release, product spec approval, QC/SOP tolerance approval,
model promotion approval, production PASS/NG authority, production auto-reject
behavior, request-supplied file paths, endpoint/schema/audit-field rename, or
Windmill credential/tunnel/runtime change is included.

## Residual Risks

- Internal compatibility names containing `shadow` remain in contracts, schema
  fields, tests, task IDs, and endpoint paths by design.
- Product specs and tolerances remain draft until QC/domain owner approval.
- Live camera capture, real calibration, and model inference remain blocked
  until hardware/artifact gates are approved.
- Runtime daily status may still report tmux relay/tunnel or Windmill attention;
  this task intentionally does not touch secret-adjacent runtime credentials.

## Rollback

Revert the FQV2-052 PR to restore prior HMI labels, health state strings, tests,
and docs. No data, secrets, deployment, hardware, model, migration, or release
state is changed.

## Memory Candidate

- memory_type: task_lesson
- content: For Flange QC v2, `shadow` is an internal compatibility term for the
  parallel-QC operating lane beside human QC. Operator-facing HMI text should
  say `Parallel QC`, `Model Assist`, and `Review-only`, while existing contract
  fields and `/detector/shadow/*` endpoint paths remain stable.
- source_ref: https://github.com/namlogan/MIL/issues/161
- why reusable: Future app, docs, and MLOps work can avoid leaking internal
  shadow task IDs into the QC tablet while preserving existing contracts.
- scope: flange_qc_v2
- suggested status: candidate
