# FQV2-037 QA Handoff: QC Feedback Export Validation

## Source

- GitHub issue: https://github.com/namlogan/MIL/issues/131
- Branch: `agent/131-feedback-export-validation`
- Task: FQV2-037

## Files Changed

- `apps/flange_qc_v2/feedback.py`
- `apps/flange_qc_v2/audit.py`
- `contracts/flange_qc_v2/feedback/qc_feedback_export.schema.json`
- `scripts/flange_qc_v2/validate_qc_feedback_export.py`
- `tests/flange_qc_v2/test_feedback_export.py`
- `docs/project/flange_qc_v2/DATA_MODEL.md`
- `docs/project/flange_qc_v2/DATASET_MLOPS_HANDOFF.md`
- `docs/project/flange_qc_v2/TEST_STRATEGY.md`
- `.ai-factory/gates/flange_qc_v2_fqv2_037_dor.json`
- `.ai-factory/qa/flange_qc_v2_fqv2_037_handoff_2026-06-03.md`

## Rules Applied

- One task per branch.
- GitHub issue is source of truth for requirement, acceptance criteria, and
  allowed paths.
- TDD RED/GREEN checkpoints were used before implementation.
- Validator reads metadata JSONL only.
- No raw media/data, model weights/binaries/inference, live camera, camera SDK,
  secrets, destructive migration, product spec approval, QC/SOP tolerance
  approval, model promotion, production deploy/release, or production PASS/NG
  authority is introduced.

## Implementation Notes

- Added `contracts/flange_qc_v2/feedback/qc_feedback_export.schema.json`.
- Added `validate_feedback_export_record()` and
  `validate_feedback_export_records()` in `apps/flange_qc_v2/feedback.py`.
- Added `scripts/flange_qc_v2/validate_qc_feedback_export.py`.
- The validator accepts empty JSONL files as zero valid records.
- The validator rejects extra payload dump fields, `production_authority=true`,
  raw-media-like references, malformed bbox values, missing fields, invalid
  feedback types, and invalid decision states.

## Tests Run

- RED: `python3 -m unittest tests.flange_qc_v2.test_feedback_export -v` failed
  before implementation because `scripts.flange_qc_v2.validate_qc_feedback_export`
  did not exist.
- GREEN: `python3 -m unittest tests.flange_qc_v2.test_feedback_export -v`
  passed, 8 tests.
- `python3 -m json.tool .ai-factory/gates/flange_qc_v2_fqv2_037_dor.json >/dev/null`
  passed.
- `python3 -m json.tool contracts/flange_qc_v2/feedback/qc_feedback_export.schema.json >/dev/null`
  passed.
- `git diff --check` passed.
- `python3 -m compileall -q apps/flange_qc_v2 tests/flange_qc_v2 scripts/flange_qc_v2`
  passed.
- `python3 -m unittest tests.flange_qc_v2.test_feedback -v` passed, 10
  tests.
- `python3 -m unittest discover -s tests/flange_qc_v2 -v` passed, 137 tests.
- `python3 scripts/product-ci/run_product_checks.py` passed.
- `python3 -m unittest discover -s tests -v` passed, 196 tests.

## Residual Risks

- Validation proves schema and safety shape only. MLOps/data owners still need to
  approve labeling policy, raw dataset handling, and model training usage.
- Operator note text remains human-authored metadata and may need downstream
  review before labeling.
- This does not approve model promotion, live camera integration, product specs,
  QC/SOP tolerances, production release, or production PASS/NG authority.

## Rollback

Revert the FQV2-037 PR to remove the feedback export schema, validator helper,
CLI, tests, docs, and gate evidence. Existing QC feedback export, audit DB
schema, HMI, replay, detector bridge, artifact intake, and feedback endpoint
behavior remain valid.
