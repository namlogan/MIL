# FQV2-042 QA Handoff: Shadow Detector Observation Dry Run

## Source

- GitHub issue: https://github.com/namlogan/MIL/issues/141
- Branch: `agent/141-shadow-detector-observations`
- Task: FQV2-042

## Files Changed

- `apps/flange_qc_v2/asgi.py`
- `apps/flange_qc_v2/detector.py`
- `tests/flange_qc_v2/test_detector_adapter.py`
- `docs/project/flange_qc_v2/USER_FLOWS.md`
- `docs/project/flange_qc_v2/DATA_MODEL.md`
- `docs/project/flange_qc_v2/MLOPS_BOUNDARY.md`
- `docs/project/flange_qc_v2/TEST_STRATEGY.md`
- `.ai-factory/gates/flange_qc_v2_fqv2_042_dor.json`
- `.ai-factory/qa/flange_qc_v2_fqv2_042_handoff_2026-06-03.md`

## Rules Applied

- One task per branch.
- GitHub issue is source of truth for requirement, acceptance criteria, and
  allowed paths.
- TDD RED/GREEN checkpoints were used before implementation.
- The endpoint reads manifest metadata only from
  `FLANGE_QC_V2_ARTIFACT_INTAKE_DIR`.
- Request payloads cannot provide artifact directories, manifest paths, model
  paths, dataset paths, observation `model_ref`, or observation `evidence_ref`.
- The endpoint emits existing `detector.result.v1` review-only evidence and
  cannot grant production authority.
- No raw media/data, feedback rows, model weights/binaries/inference, live
  camera, camera SDK, secrets, destructive migration, product spec approval,
  QC/SOP tolerance approval, model promotion, production deploy/release, or
  production PASS/NG authority is introduced.

## Implementation Notes

- Added `build_shadow_detector_result_from_payload()` in `detector.py`.
- Added `POST /detector/shadow/observations` in `asgi.py`.
- Valid sanitized observations return `ASSIST` with
  `MODEL_REVIEW_REQUIRED`; manifest `model_ref` and `evidence_ref` are filled
  by `ManifestDetectorAdapter`.
- Empty observations return `NOT_EVALUATED` with `MODEL_MISSING`.
- Missing intake env, invalid intake, invalid labels, invalid bbox/confidence,
  raw-media source URIs, request-supplied paths, and request-supplied
  model/evidence refs fail closed with HTTP 400.

## Tests Run

- RED: `python3 -m unittest tests.flange_qc_v2.test_detector_adapter -v`
  failed before implementation because `/detector/shadow/observations` returned
  HTTP 404 for the new cases.
- GREEN: `python3 -m unittest tests.flange_qc_v2.test_detector_adapter -v`
  passed, 17 tests.
- `python3 -m unittest tests.flange_qc_v2.test_hmi_stream -v` passed, 5 tests.
- `python3 -m unittest tests.flange_qc_v2.test_artifact_readiness -v` passed,
  9 tests.
- `python3 -m json.tool .ai-factory/gates/flange_qc_v2_fqv2_042_dor.json >/dev/null`
  passed.
- `git diff --check` passed.
- `python3 -m compileall -q apps/flange_qc_v2 tests/flange_qc_v2 scripts/flange_qc_v2`
  passed.
- `python3 -m unittest discover -s tests/flange_qc_v2 -v` passed, 156 tests.
- `python3 scripts/product-ci/run_product_checks.py` passed.
- `python3 -m unittest discover -s tests -v` passed, 196 tests.

## Runtime Note

Daily operator status was inspected before dispatch. The remaining attention is
runtime support only: tmux relay/tunnel sessions are absent and the local
Windmill CLI credential is Unauthorized, so the relay cannot read the Windmill
webhook secret. This task does not require Windmill secret access and does not
modify `.windmill/runtime/**`.

## Residual Risks

- This endpoint is an app-side contract dry run for future MLOps output, not a
  model runtime, inference endpoint, model promotion gate, or release approval.
- Live camera use still requires hardware readiness and credential/runtime setup
  outside this task.
- This does not approve labels, model promotion, live camera integration,
  product specs, QC/SOP tolerances, production release, or production PASS/NG
  authority.

## Rollback

Revert the FQV2-042 PR to remove the shadow detector observation dry-run path,
tests, docs, and gate evidence. Existing detector status endpoint, replay/HMI
observation flow, artifact readiness, feedback, and product CI behavior remain
valid.
