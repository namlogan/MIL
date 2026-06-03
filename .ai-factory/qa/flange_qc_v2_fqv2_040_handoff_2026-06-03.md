# FQV2-040 QA Handoff: Artifact Readiness Status Endpoint

## Source

- GitHub issue: https://github.com/namlogan/MIL/issues/137
- Branch: `agent/137-artifact-readiness-endpoint`
- Task: FQV2-040

## Files Changed

- `apps/flange_qc_v2/asgi.py`
- `apps/flange_qc_v2/artifact_readiness.py`
- `tests/flange_qc_v2/test_artifact_readiness.py`
- `docs/project/flange_qc_v2/USER_FLOWS.md`
- `docs/project/flange_qc_v2/DATA_MODEL.md`
- `docs/project/flange_qc_v2/TEST_STRATEGY.md`
- `.ai-factory/gates/flange_qc_v2_fqv2_040_dor.json`
- `.ai-factory/qa/flange_qc_v2_fqv2_040_handoff_2026-06-03.md`

## Rules Applied

- One task per branch.
- GitHub issue is source of truth for requirement, acceptance criteria, and
  allowed paths.
- TDD RED/GREEN checkpoints were used before implementation.
- The endpoint reads only configured env paths and accepts no request-supplied
  filesystem paths.
- The endpoint emits readiness metadata only and never grants production
  authority.
- No raw media/data, model weights/binaries/inference, live camera, camera SDK,
  secrets, destructive migration, product spec approval, QC/SOP tolerance
  approval, HMI redesign, model promotion, production deploy/release, or
  production PASS/NG authority is introduced.

## Implementation Notes

- Added `GET /artifact-readiness/status`.
- Endpoint uses `FLANGE_QC_V2_ARTIFACT_INTAKE_DIR` for artifact intake.
- Endpoint optionally reads `FLANGE_QC_V2_LABELING_REVIEW_PACK_PATH`.
- Missing artifact intake returns safe `configured=false` readiness lanes.
- Missing/malformed optional labeling pack is reported as a warning and keeps
  QC feedback readiness blocked.
- Existing artifact intake status, detector status, HMI, feedback export, and
  readiness CLI behavior remain in place.

## Tests Run

- RED: `python3 -m unittest tests.flange_qc_v2.test_artifact_readiness -v`
  failed before implementation because `/artifact-readiness/status` returned
  HTTP 404.
- GREEN: `python3 -m unittest tests.flange_qc_v2.test_artifact_readiness -v`
  passed, 9 tests.
- `python3 -m json.tool .ai-factory/gates/flange_qc_v2_fqv2_040_dor.json >/dev/null`
  passed.
- `git diff --check` passed.
- `python3 -m compileall -q apps/flange_qc_v2 tests/flange_qc_v2 scripts/flange_qc_v2`
  passed.
- `python3 -m unittest tests.flange_qc_v2.test_artifact_intake -v` passed,
  9 tests.
- `python3 -m unittest tests.flange_qc_v2.test_detector_adapter -v` passed,
  12 tests.
- `python3 -m unittest discover -s tests/flange_qc_v2 -v` passed, 150 tests.
- `python3 scripts/product-ci/run_product_checks.py` passed.
- `python3 -m unittest discover -s tests -v` passed, 196 tests.

## Residual Risks

- The endpoint is an internal readiness/status surface, not a production release
  or model promotion gate.
- Live camera use still requires hardware readiness and credential/runtime setup
  outside this task.
- This does not approve labels, model promotion, live camera integration,
  product specs, QC/SOP tolerances, production release, or production PASS/NG
  authority.

## Rollback

Revert the FQV2-040 PR to remove the artifact readiness HTTP endpoint, endpoint
tests, docs, and gate evidence. Existing artifact intake endpoint, detector
bridge, HMI, readiness CLI, feedback export, and product CI behavior remain
valid.
