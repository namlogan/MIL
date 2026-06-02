# FQV2-029 QA Handoff: Shadow Detector Metadata Bridge

## Source

- GitHub issue: https://github.com/namlogan/MIL/issues/115
- Branch: `agent/115-shadow-detector-metadata-bridge`
- Task: FQV2-029

## Files Changed

- `apps/flange_qc_v2/detector.py`
- `apps/flange_qc_v2/asgi.py`
- `tests/flange_qc_v2/test_detector_adapter.py`
- `docs/project/flange_qc_v2/MLOPS_BOUNDARY.md`
- `docs/project/flange_qc_v2/DATA_MODEL.md`
- `docs/project/flange_qc_v2/USER_FLOWS.md`
- `docs/project/flange_qc_v2/TEST_STRATEGY.md`
- `.ai-factory/gates/flange_qc_v2_fqv2_029_dor.json`
- `.ai-factory/qa/flange_qc_v2_fqv2_029_handoff_2026-06-02.md`

## Rules Applied

- One task per branch.
- GitHub issue is source of truth for requirement, acceptance criteria, and
  allowed paths.
- TDD RED/GREEN checkpoints were used before implementation.
- `/detector/shadow/status` reads only `FLANGE_QC_V2_ARTIFACT_INTAKE_DIR`; no
  request-supplied arbitrary filesystem path is accepted.
- The metadata bridge loads only `model_artifact_manifest.json` and only after
  the existing artifact intake validator reports
  `ready.shadow_model_integration_issue=true`.
- No raw media, raw datasets, customer data, notebooks, model weights, model
  binaries, model deserialization, model inference, camera SDK import, live
  camera capture, GPU use, secrets, destructive migration, deployment, product
  spec approval, QC/SOP tolerance approval, model promotion, production PASS/NG
  authority, or production auto-reject behavior is introduced.

## Implementation Notes

- Added `build_shadow_detector_status_from_intake()` for detector-focused
  metadata readiness.
- Added `build_shadow_detector_unconfigured_status()` for safe missing-env
  responses.
- Added `build_manifest_detector_from_intake()` to construct the existing
  review-only `ManifestDetectorAdapter` from validated intake metadata.
- Added `GET /detector/shadow/status` to the ASGI app.
- Ready status reports `manifest-detector`, model reference, artifact version,
  labels, evaluation report reference, approval status, shadow mode, and
  approval blockers.
- Unconfigured or unready status remains non-authoritative and points back to
  artifact intake configuration or repair.

## Tests Run

- RED: `python3 -m unittest tests.flange_qc_v2.test_detector_adapter -v`
  failed because the bridge functions did not exist and
  `/detector/shadow/status` returned 404.
- GREEN: `python3 -m unittest tests.flange_qc_v2.test_detector_adapter -v`
  passed, 12 tests.
- `python3 -m unittest tests.flange_qc_v2.test_artifact_intake -v` passed,
  9 tests.
- `python3 -m unittest tests.flange_qc_v2.test_hmi_screen -v` passed, 5 tests.
- `python3 -m unittest tests.flange_qc_v2.test_hmi_stream -v` passed, 4 tests.
- `python3 -m json.tool .ai-factory/gates/flange_qc_v2_fqv2_029_dor.json`
  passed.
- `git diff --check` passed.
- `python3 -m unittest discover -s tests/flange_qc_v2 -v` passed, 123 tests.
- `python3 -m compileall -q apps/flange_qc_v2 tests/flange_qc_v2` passed.
- `python3 scripts/product-ci/run_product_checks.py` passed.
- `python3 -m unittest discover -s tests -v` passed, 196 tests.

## Residual Risks

- Template artifacts are sanitized metadata only; they do not prove real
  dataset quality, model performance, model promotion, or live camera behavior.
- The bridge does not run inference. A future issue must add review-only
  observation wiring after the real MLOps artifact package is available and
  validated.
- Product specs, QC/SOP tolerances, model approval/promotion, live camera
  readiness, and production release remain human-gated.

## Rollback

Revert the FQV2-029 PR to remove `/detector/shadow/status` and the metadata
bridge. Existing artifact intake endpoint, CLI validator, HMI replay, and
detector adapter behavior remain valid. No migration, model rollback, camera
rollback, dataset rollback, or deploy rollback is required.

## Memory Candidate

- memory_type: implementation_lesson
- content: Flange QC v2 connects validated artifact intake metadata to the
  detector boundary through `/detector/shadow/status`, loading only
  `model_artifact_manifest.json` after intake readiness and keeping detector
  output review-only with no production authority.
- source_ref: https://github.com/namlogan/MIL/issues/115
- why reusable: Future model observation wiring can reuse the env-var-bound
  bridge and `ManifestDetectorAdapter` without introducing request paths, model
  deserialization, inference, camera access, or production PASS/NG authority.
- scope: project:flange_qc_v2
- suggested status: candidate
