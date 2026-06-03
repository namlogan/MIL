# FQV2-038 QA Handoff: QC Feedback Labeling Review Pack

## Source

- GitHub issue: https://github.com/namlogan/MIL/issues/133
- Branch: `agent/133-labeling-review-pack`
- Task: FQV2-038

## Files Changed

- `apps/flange_qc_v2/feedback.py`
- `scripts/flange_qc_v2/build_labeling_review_pack.py`
- `tests/flange_qc_v2/test_feedback_export.py`
- `docs/project/flange_qc_v2/DATA_MODEL.md`
- `docs/project/flange_qc_v2/DATASET_MLOPS_HANDOFF.md`
- `docs/project/flange_qc_v2/TEST_STRATEGY.md`
- `.ai-factory/gates/flange_qc_v2_fqv2_038_dor.json`
- `.ai-factory/qa/flange_qc_v2_fqv2_038_handoff_2026-06-03.md`

## Rules Applied

- One task per branch.
- GitHub issue is source of truth for requirement, acceptance criteria, and
  allowed paths.
- TDD RED/GREEN checkpoints were used before implementation.
- The pack consumes validated metadata records only.
- The pack emits aggregate counts only and does not include individual feedback
  rows or raw payload dumps.
- No raw media/data, model weights/binaries/inference, live camera, camera SDK,
  secrets, destructive migration, product spec approval, QC/SOP tolerance
  approval, model promotion, production deploy/release, or production PASS/NG
  authority is introduced.

## Implementation Notes

- Added `build_labeling_review_pack()` in `apps/flange_qc_v2/feedback.py`.
- Added `scripts/flange_qc_v2/build_labeling_review_pack.py`.
- Pack contract version is `qc_feedback_labeling_review_pack.v1`.
- Pack includes source record count, product counts, feedback type counts,
  inspection decision counts, shadow decision counts, detector label counts,
  recommended next actions, `production_authority=false`, and authority
  blockers.
- Empty JSONL input produces a valid pack with `collect_more_qc_feedback`.
- Invalid feedback export records fail closed through the existing validator.

## Tests Run

- RED: `python3 -m unittest tests.flange_qc_v2.test_feedback_export -v` failed
  before implementation because `build_labeling_review_pack` did not exist.
- GREEN: `python3 -m unittest tests.flange_qc_v2.test_feedback_export -v`
  passed, 12 tests.
- `python3 -m json.tool .ai-factory/gates/flange_qc_v2_fqv2_038_dor.json >/dev/null`
  passed.
- `git diff --check` passed.
- `python3 -m compileall -q apps/flange_qc_v2 tests/flange_qc_v2 scripts/flange_qc_v2`
  passed.
- `python3 -m unittest tests.flange_qc_v2.test_feedback -v` passed, 10 tests.
- `python3 -m unittest discover -s tests/flange_qc_v2 -v` passed, 141 tests.
- `python3 scripts/product-ci/run_product_checks.py` passed.
- `python3 -m unittest discover -s tests -v` passed, 196 tests.

## Residual Risks

- The pack is an aggregate planning artifact. MLOps/data owners still need to
  approve labeling policy, raw dataset handling, and model training usage.
- This does not approve labels, model promotion, live camera integration,
  product specs, QC/SOP tolerances, production release, or production PASS/NG
  authority.

## Rollback

Revert the FQV2-038 PR to remove the labeling review pack helper, CLI, tests,
docs, and gate evidence. Existing QC feedback export, export validation, audit
DB schema, HMI, replay, detector bridge, artifact intake, and feedback endpoint
behavior remain valid.
