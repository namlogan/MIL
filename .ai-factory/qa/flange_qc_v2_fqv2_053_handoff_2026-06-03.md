# FQV2-053 QA Handoff: Production-Shaped Inspection Intake

## Scope

- Branch: `agent/163-inspection-intake`
- Task: FQV2-053
- Issue: https://github.com/namlogan/MIL/issues/163

## Files Changed

- `apps/flange_qc_v2/asgi.py`
- `apps/flange_qc_v2/inspection_intake.py`
- `contracts/flange_qc_v2/events/inspection_intake.schema.json`
- `tests/flange_qc_v2/test_inspection_intake.py`
- `docs/project/flange_qc_v2/DATA_MODEL.md`
- `docs/project/flange_qc_v2/USER_FLOWS.md`
- `docs/project/flange_qc_v2/TEST_STRATEGY.md`
- `docs/project/flange_qc_v2/DEPLOYMENT.md`
- `.ai-factory/gates/flange_qc_v2_fqv2_053_dor.json`
- `.ai-factory/qa/flange_qc_v2_fqv2_053_handoff_2026-06-03.md`

## Summary

- Added `POST /inspection/intake` as the runtime handoff point for camera/model
  pipeline metadata once real artifacts arrive.
- Added `inspection.intake.v1` contract for one inspection payload with product
  code, size group, sanitized frame references, exactly one measurement source
  (`measurements` or `boundary`), and optional sanitized detector observations.
- Reused the existing SOP engine for Phase 1, Phase 2, Phase 3, and Phase 4 so
  direct measurements and boundary/corner-derived measurements produce the same
  `inspection.snapshot` payload family as HMI/replay/audit.
- Kept runtime configuration under environment/default repo paths only. Request
  payloads cannot supply product specs, calibration, dataset, model, manifest,
  weights, or artifact intake paths.
- Added idempotent audit persistence when `FLANGE_QC_V2_AUDIT_DB_PATH` is
  configured.
- Documented the intake entity, user flow, test coverage, deployment smoke, and
  observability expectations.

## TDD Evidence

- RED:
  `python3 -m unittest tests.flange_qc_v2.test_inspection_intake -v` failed
  because `/inspection/intake` returned 404 before implementation.
- GREEN:
  the same focused suite passed after adding the intake builder, ASGI route,
  contract, and endpoint tests.
- HARDENING:
  added source-ref and exactly-one-source checks, then reran the focused suite
  successfully.

## Checks

- `python3 -m unittest tests.flange_qc_v2.test_inspection_intake -v` passed, 7 tests.
- `python3 -m unittest tests.flange_qc_v2.test_hmi_stream -v` passed, 7 tests.
- `python3 -m json.tool .ai-factory/gates/flange_qc_v2_fqv2_053_dor.json` passed.
- `python3 -m json.tool contracts/flange_qc_v2/events/inspection_intake.schema.json` passed.
- `python3 -m compileall -q apps/flange_qc_v2 tests/flange_qc_v2` passed.
- `python3 scripts/product-ci/run_product_checks.py` passed.
- `python3 -m unittest discover -s tests/flange_qc_v2 -v` passed, 177 tests.
- `python3 -m unittest discover -s tests -v` passed, 196 tests.
- `git diff --check` passed.

## Restricted Change Check

No live camera SDK loading, live capture, raw media, raw datasets, customer or
factory data, notebooks, model weights, model binaries, model deserialization,
GPU inference runtime, secrets, credentials, destructive migrations, production
deploy/release, product spec approval, QC/SOP tolerance approval, model
promotion approval, production PASS/NG authority, production auto-reject,
Windmill credential/tunnel/runtime change, or Memory0 approved record write is
included.

## Residual Risks

- Product specs and SOP tolerances remain draft until QC/domain owner approval.
- Calibration remains synthetic/example until real camera hardware and
  calibration evidence arrive.
- Model observations remain review-only and cannot approve or reject production
  parts.
- The endpoint accepts sanitized camera/model metadata, not raw images or raw
  model artifacts. Real camera SDK capture and model runtime loading remain
  separate gated tasks.
- Production release/deploy remains blocked until release, rollback, staging,
  monitoring, and human approval gates pass.

## Rollback

Revert the FQV2-053 PR to remove `/inspection/intake`, the intake builder,
contract schema, tests, docs, and gate evidence. No production data, secrets,
camera state, model artifacts, migrations, or release state is changed.

## Memory Candidate

- memory_type: task_lesson
- content: For Flange QC v2, the production-shaped runtime handoff is
  `/inspection/intake` with contract `inspection.intake.v1`. It accepts
  sanitized frame references, exactly one measurement source, and optional
  review-only detector observations, then returns an `inspection.snapshot`
  without production authority.
- source_ref: https://github.com/namlogan/MIL/issues/163
- why reusable: Future camera, calibration, and MLOps integration tasks can
  connect through this endpoint instead of bypassing SOP/audit gates or adding
  request-supplied local paths.
- scope: flange_qc_v2
- suggested status: candidate
