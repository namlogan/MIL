# FQV2-036 QA Handoff: QC Feedback Metadata Export

## Source

- GitHub issue: https://github.com/namlogan/MIL/issues/129
- Branch: `agent/129-feedback-export-mlops`
- Task: FQV2-036

## Files Changed

- `apps/flange_qc_v2/audit.py`
- `scripts/flange_qc_v2/export_qc_feedback.py`
- `tests/flange_qc_v2/test_feedback_export.py`
- `docs/project/flange_qc_v2/DATA_MODEL.md`
- `docs/project/flange_qc_v2/DATASET_MLOPS_HANDOFF.md`
- `docs/project/flange_qc_v2/MLOPS_BOUNDARY.md`
- `docs/project/flange_qc_v2/TEST_STRATEGY.md`
- `.ai-factory/gates/flange_qc_v2_fqv2_036_dor.json`
- `.ai-factory/qa/flange_qc_v2_fqv2_036_handoff_2026-06-03.md`

## Rules Applied

- One task per branch.
- GitHub issue is source of truth for requirement, acceptance criteria, and
  allowed paths.
- TDD RED/GREEN checkpoints were used before implementation.
- Export reads existing SQLite audit evidence only.
- Export emits JSONL sanitized metadata only and does not write to the audit DB.
- No raw media/data, model weights/binaries/inference, live camera, camera SDK,
  secrets, destructive migration, product spec approval, QC/SOP tolerance
  approval, model promotion, production deploy/release, or production PASS/NG
  authority is introduced.

## Implementation Notes

- Added `AuditStore.export_feedback_metadata_records()`.
- Added `scripts/flange_qc_v2/export_qc_feedback.py`.
- Records use `contract_version=qc_feedback_export.v1`.
- Records include feedback id, inspection id, product metadata, inspection
  decision, feedback metadata, authority blockers, and compact detector
  observation label/confidence/bbox metadata when present.
- The CLI writes JSONL to stdout or an output file.
- Missing audit DB paths fail closed with a non-secret error.
- Empty initialized audit stores export an empty JSONL file without error.

## Tests Run

- RED: `python3 -m unittest tests.flange_qc_v2.test_feedback_export -v` failed
  before implementation because `scripts.flange_qc_v2.export_qc_feedback` did
  not exist.
- GREEN: `python3 -m unittest tests.flange_qc_v2.test_feedback_export -v`
  passed, 3 tests.
- `python3 -m json.tool .ai-factory/gates/flange_qc_v2_fqv2_036_dor.json >/dev/null`
  passed.
- `git diff --check` passed.
- `python3 -m compileall -q apps/flange_qc_v2 tests/flange_qc_v2 scripts/flange_qc_v2`
  passed.
- `python3 -m unittest tests.flange_qc_v2.test_feedback -v` passed, 10
  tests.
- `python3 -m unittest tests.flange_qc_v2.test_audit_store -v` passed, 5
  tests.
- `python3 -m unittest discover -s tests/flange_qc_v2 -v` passed, 132 tests.
- `python3 scripts/product-ci/run_product_checks.py` passed.
- `python3 -m unittest discover -s tests -v` passed, 196 tests.

## Residual Risks

- Export depends on existing audit DB contents. It does not create inspections or
  feedback rows.
- Exported feedback note text is operator-entered metadata. It must still be
  reviewed by MLOps/data owners before use in real labeling workflows.
- This does not approve raw dataset storage, model training, model promotion,
  live camera integration, or production PASS/NG authority.

## Rollback

Revert the FQV2-036 PR to remove the feedback export helper, CLI, tests, docs,
and gate evidence. Existing audit DB schema, HMI, replay, detector bridge,
artifact intake, and feedback endpoint behavior remain valid.
