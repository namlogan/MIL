# FQV2-030 QA Handoff: Review-Only Shadow Detector Observations in Replay

## Source

- GitHub issue: https://github.com/namlogan/MIL/issues/117
- Branch: `agent/117-shadow-detector-observations-replay`
- Task: FQV2-030

## Files Changed

- `apps/flange_qc_v2/replay.py`
- `apps/flange_qc_v2/hmi_stream.py`
- `tests/flange_qc_v2/test_replay.py`
- `tests/flange_qc_v2/test_hmi_stream.py`
- `samples/replay/flange_qc_v2/phase2_synthetic_measurements.json`
- `docs/project/flange_qc_v2/MLOPS_BOUNDARY.md`
- `docs/project/flange_qc_v2/DATA_MODEL.md`
- `docs/project/flange_qc_v2/USER_FLOWS.md`
- `docs/project/flange_qc_v2/TEST_STRATEGY.md`
- `.ai-factory/gates/flange_qc_v2_fqv2_030_dor.json`
- `.ai-factory/qa/flange_qc_v2_fqv2_030_handoff_2026-06-02.md`

## Rules Applied

- One task per branch.
- GitHub issue is source of truth for requirement, acceptance criteria, and
  allowed paths.
- TDD RED/GREEN checkpoints were used before implementation.
- Replay observations are synthetic metadata only: label, confidence, and
  normalized bbox.
- HMI snapshot generation reads only `FLANGE_QC_V2_ARTIFACT_INTAKE_DIR` for
  manifest detector integration; no request-supplied arbitrary filesystem path
  is accepted.
- No raw media, raw datasets, customer data, notebooks, model weights, model
  binaries, model deserialization, model inference, camera SDK import, live
  camera capture, GPU use, secrets, destructive migration, deployment, product
  spec approval, QC/SOP tolerance approval, model promotion, production PASS/NG
  authority, or production auto-reject behavior is introduced.

## Implementation Notes

- Extended `ReplayFrame` with optional `detector_observations`.
- Parser validates observation shape through `DetectorObservation` and strips
  fixture-supplied model/evidence references.
- Added synthetic observation metadata to the existing no-camera replay sample.
- HMI snapshot generation attaches observations only when artifact intake is
  ready; otherwise the existing safe empty observation state remains.
- `ManifestDetectorAdapter` fills model reference and evidence reference from
  validated manifest metadata.
- Final replay decision aggregation remains unchanged and non-authoritative.

## Tests Run

- RED: `python3 -m unittest tests.flange_qc_v2.test_replay -v` failed because
  replay frames did not expose `detector_observations` and invalid observation
  bbox was not rejected.
- RED: `python3 -m unittest tests.flange_qc_v2.test_hmi_stream -v` failed
  because HMI snapshots stayed empty even when artifact intake was ready.
- GREEN: `python3 -m unittest tests.flange_qc_v2.test_replay -v` passed,
  4 tests.
- GREEN: `python3 -m unittest tests.flange_qc_v2.test_hmi_stream -v` passed,
  5 tests.
- `python3 -m unittest tests.flange_qc_v2.test_detector_adapter -v` passed,
  12 tests.
- `python3 -m json.tool .ai-factory/gates/flange_qc_v2_fqv2_030_dor.json`
  passed.
- `git diff --check` passed.
- `python3 -m unittest discover -s tests/flange_qc_v2 -v` passed, 125 tests.
- `python3 -m compileall -q apps/flange_qc_v2 tests/flange_qc_v2` passed.
- `python3 scripts/product-ci/run_product_checks.py` passed.
- `python3 -m unittest discover -s tests -v` passed, 196 tests.

## Residual Risks

- Synthetic replay observation metadata is only structural evidence; it does not
  prove real dataset quality, model performance, model promotion, or live camera
  behavior.
- The app still does not run inference. A future issue may connect real
  review-only model output only after MLOps artifacts are validated.
- Product specs, QC/SOP tolerances, model approval/promotion, live camera
  readiness, and production release remain human-gated.

## Rollback

Revert the FQV2-030 PR to remove optional replay detector observations and HMI
snapshot wiring. Existing artifact intake endpoint, shadow detector status
endpoint, no-camera replay, HMI, and detector adapter behavior remain valid. No
migration, model rollback, camera rollback, dataset rollback, or deploy rollback
is required.

## Memory Candidate

- memory_type: implementation_lesson
- content: Flange QC v2 can carry review-only synthetic detector observations in
  replay snapshots by validating label/confidence/bbox metadata, stripping
  fixture provenance, and using the manifest detector adapter to attach model
  and evaluation refs only when artifact intake is ready.
- source_ref: https://github.com/namlogan/MIL/issues/117
- why reusable: Future MLOps review-output wiring can preserve the same
  fail-safe empty state and manifest provenance rules while avoiding inference,
  camera access, request paths, and production PASS/NG authority.
- scope: project:flange_qc_v2
- suggested status: candidate
