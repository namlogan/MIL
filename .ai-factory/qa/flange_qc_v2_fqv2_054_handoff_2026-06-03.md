# FQV2-054 QA Handoff: Machine Vision Workstream Switch

## Scope

- Branch: `agent/165-machine-vision-workstream`
- Task: FQV2-054
- Issue: https://github.com/namlogan/MIL/issues/165

## Files Changed

- `.ai-factory/workstreams/flange_qc_v2_machine_vision.json`
- `.ai-factory/gates/flange_qc_v2_fqv2_054_dor.json`
- `.ai-factory/qa/flange_qc_v2_fqv2_054_handoff_2026-06-03.md`
- `docs/project/flange_qc_v2/WORKSTREAM_STATUS.md`
- `docs/project/flange_qc_v2/WORK_PACKAGES.md`
- `docs/project/flange_qc_v2/MVP_SCOPE.md`
- `docs/project/flange_qc_v2/HARDWARE_CAMERA_READINESS.md`
- `docs/project/flange_qc_v2/MLOPS_BOUNDARY.md`
- `tests/flange_qc_v2/test_workstream_status.py`

## Summary

- Froze the Flange QC v2 demo-only/replay/HMI workstream as a regression
  baseline and rollback path.
- Opened `machine_vision` real-runtime SOP as the active workstream.
- Added a machine-readable workstream manifest for agent/orchestrator routing.
- Documented the new priority order: camera hardware/readiness evidence,
  calibration evidence, runtime geometry measurement evidence, product specs and
  tolerance approval package, full SOP rule gate, then advanced model defect
  work.
- Made advanced model defect work explicitly blocked until prior
  `machine_vision` gates pass.
- Added tests that fail if the manifest loses the freeze, active workstream,
  priority order, or advanced-model deferral.

## TDD Evidence

- RED:
  `python3 -m unittest tests.flange_qc_v2.test_workstream_status -v` failed
  because the workstream manifest and status doc did not exist.
- GREEN:
  the same focused suite passed after adding the manifest, status doc, and
  workstream documentation updates.

## Checks

- `python3 -m unittest tests.flange_qc_v2.test_workstream_status -v` passed, 3 tests.
- `python3 -m json.tool .ai-factory/workstreams/flange_qc_v2_machine_vision.json` passed.
- `python3 -m json.tool .ai-factory/gates/flange_qc_v2_fqv2_054_dor.json` passed.
- `python3 -m unittest discover -s tests/flange_qc_v2 -v` passed, 180 tests.
- `python3 -m compileall -q apps/flange_qc_v2 tests/flange_qc_v2` passed.
- `python3 scripts/product-ci/run_product_checks.py` passed.
- `python3 -m unittest discover -s tests -v` passed, 196 tests.
- `git diff --check` passed.

## Restricted Change Check

No app runtime code, live camera SDK import, live capture, raw media,
customer/factory data, camera credentials, secrets, calibration approval,
product spec approval, QC/SOP tolerance approval, model promotion, production
PASS/NG authority, production auto-reject, production release/deploy,
destructive migrations, Memory0 approved writes, advanced defect model
implementation, model deserialization, inference runtime loading, GPU inference,
dataset notebooks, or raw dataset management is included.

## Residual Risks

- `machine_vision` is active but waiting on external camera/site evidence.
- Product spec and QC/SOP tolerance approvals remain human gates.
- Advanced model defect work remains blocked until the runtime SOP gates are
  recorded.
- No physical `machine_vision` branch is created by this task; the workstream
  identity is source-of-truth metadata under `.ai-factory/workstreams/`.

## Rollback

Revert the FQV2-054 PR to remove the workstream manifest, status doc, tests, and
documentation updates. No runtime app behavior, data, secrets, hardware state,
model artifacts, migrations, or release state is changed.

## Memory Candidate

- memory_type: project_decision
- content: Flange QC v2 demo-only/replay/HMI workstream is frozen; the active
  workstream is `machine_vision` real-runtime SOP. Future work must prioritize
  camera hardware/readiness, calibration, runtime geometry, product specs
  package, and full SOP rule gate before advanced model defect work.
- source_ref: https://github.com/namlogan/MIL/issues/165
- why reusable: Prevents agents from continuing demo-only polish or model-first
  work before runtime SOP evidence exists.
- scope: flange_qc_v2
- suggested status: candidate
