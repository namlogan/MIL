# FQV2-043 QA Handoff: Shadow Observation Request Contract

## Source

- GitHub issue: https://github.com/namlogan/MIL/issues/143
- Branch: `agent/143-shadow-observation-request-contract`
- Task: FQV2-043

## Files Changed

- `apps/flange_qc_v2/detector.py`
- `contracts/flange_qc_v2/detector/shadow_observation_request.schema.json`
- `scripts/flange_qc_v2/validate_shadow_detector_observations.py`
- `samples/replay/flange_qc_v2/shadow_detector_observation_request.json`
- `tests/flange_qc_v2/test_detector_adapter.py`
- `docs/project/flange_qc_v2/USER_FLOWS.md`
- `docs/project/flange_qc_v2/DATA_MODEL.md`
- `docs/project/flange_qc_v2/MLOPS_BOUNDARY.md`
- `docs/project/flange_qc_v2/TEST_STRATEGY.md`
- `.ai-factory/gates/flange_qc_v2_fqv2_043_dor.json`
- `.ai-factory/qa/flange_qc_v2_fqv2_043_handoff_2026-06-03.md`

## Rules Applied

- One task per branch.
- GitHub issue is source of truth for requirement, acceptance criteria, and
  allowed paths.
- TDD RED/GREEN checkpoints were used before implementation.
- The validator accepts only metadata payloads for the existing
  `/detector/shadow/observations` endpoint.
- Request payloads cannot provide artifact directories, manifest paths, model
  paths, dataset paths, observation `model_ref`, or observation `evidence_ref`.
- The sample payload is sanitized metadata only and contains no raw media,
  model binaries, credentials, or production authority.
- No raw media/data, feedback rows, model weights/binaries/inference, live
  camera, camera SDK, secrets, destructive migration, product spec approval,
  QC/SOP tolerance approval, model promotion, production deploy/release, or
  production PASS/NG authority is introduced.

## Implementation Notes

- Added `shadow_detector_observation_request.v1` schema.
- Added `validate_shadow_detector_observation_request()` in `detector.py`.
- Added `scripts/flange_qc_v2/validate_shadow_detector_observations.py`.
- Added safe sample payload at
  `samples/replay/flange_qc_v2/shadow_detector_observation_request.json`.
- Kept endpoint backward-compatible: CLI/schema require `contract_version`, but
  the endpoint can still validate payloads that omit it from prior FQV2-042
  callers. If a contract version is supplied, it must match.
- Validator reports field-level errors for confidence and bbox to help MLOps fix
  payloads quickly.

## Tests Run

- RED: `python3 -m unittest tests.flange_qc_v2.test_detector_adapter -v`
  failed before implementation because the schema and validator CLI were
  missing.
- GREEN: `python3 -m unittest tests.flange_qc_v2.test_detector_adapter -v`
  passed, 21 tests.
- `python3 -m unittest tests.flange_qc_v2.test_hmi_stream -v` passed, 5 tests.
- `python3 scripts/flange_qc_v2/validate_shadow_detector_observations.py --input samples/replay/flange_qc_v2/shadow_detector_observation_request.json`
  passed with `ok=true` and `observation_count=1`.
- `python3 -m json.tool contracts/flange_qc_v2/detector/shadow_observation_request.schema.json >/dev/null`
  passed.
- `python3 -m json.tool .ai-factory/gates/flange_qc_v2_fqv2_043_dor.json >/dev/null`
  passed.
- `git diff --check` passed.
- `python3 -m compileall -q apps/flange_qc_v2 tests/flange_qc_v2 scripts/flange_qc_v2`
  passed.
- `python3 -m unittest discover -s tests/flange_qc_v2 -v` passed, 160 tests.
- `python3 scripts/product-ci/run_product_checks.py` passed.
- `python3 -m unittest discover -s tests -v` passed, 196 tests.

## Runtime Note

Daily operator status before dispatch still reported runtime support attention:
tmux relay/tunnel sessions are absent and the local Windmill CLI credential is
Unauthorized. This task does not require Windmill secret access and does not
modify `.windmill/runtime/**`.

## Residual Risks

- This contract validates app-side metadata for future MLOps output; it is not a
  model runtime, inference endpoint, model promotion gate, or release approval.
- Live camera use still requires hardware readiness and credential/runtime setup
  outside this task.
- This does not approve labels, model promotion, live camera integration,
  product specs, QC/SOP tolerances, production release, or production PASS/NG
  authority.

## Rollback

Revert the FQV2-043 PR to remove the shadow detector observation request schema,
validator CLI, sample payload, tests, docs, and gate evidence. Existing detector
dry-run endpoint, detector status endpoint, replay/HMI observation flow,
artifact readiness, feedback, and product CI behavior remain valid.
