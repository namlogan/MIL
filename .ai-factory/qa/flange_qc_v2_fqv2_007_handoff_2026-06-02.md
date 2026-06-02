# FQV2-007 QA Handoff: Geometry Measurement Contract

## Source

- GitHub issue: https://github.com/namlogan/MIL/issues/71
- Branch: `agent/71-geometry-measurement-contract`
- Task: FQV2-007

## Files Changed

- `apps/flange_qc_v2/geometry.py`
- `contracts/flange_qc_v2/geometry/measurement_set.schema.json`
- `tests/flange_qc_v2/test_geometry.py`
- `docs/project/flange_qc_v2/DATA_MODEL.md`
- `.ai-factory/gates/flange_qc_v2_fqv2_007_dor.json`
- `.ai-factory/qa/flange_qc_v2_fqv2_007_handoff_2026-06-02.md`

## Rules Applied

- One task per branch.
- GitHub issue is source of truth for requirement, acceptance criteria, and allowed paths.
- TDD red/green was used before implementation.
- Geometry contract work is scoped to evidence only.
- No production PASS/NG decision authority is introduced.
- QC/SOP tolerance approval remains a human gate.

## Implementation Notes

- Added `resolve_geometry_measurements` for bootstrap geometry evidence.
- Complete payloads require exactly 3 length points, 3 width points, and 2 diagonals.
- Complete payloads compute `diagonal_deviation` but still return `BLOCKED` with `SOP_TOLERANCE_APPROVAL_MISSING`.
- Incomplete payloads return `BLOCKED` with `MEASUREMENTS_INCOMPLETE` and count evidence.
- `production_authority` is always false and cannot be enabled by this contract.

## Tests Run

- `python3 -m unittest tests.flange_qc_v2.test_geometry -v`

Additional required checks before PR review:

- `python3 -m unittest discover -s tests/flange_qc_v2 -v`
- `python3 -m compileall -q apps/flange_qc_v2 tests/flange_qc_v2`
- `python3 scripts/product-ci/run_product_checks.py`
- `python3 -m unittest discover -s tests -v`
- `git diff --check`

## Residual Risks

- Measurement extraction from camera/replay frames is not implemented.
- Geometry correction/calibration transform is not implemented.
- Production PASS/NG decision engine remains gated.
- QC/SOP tolerance approval is still required before production authority.

## Rollback

Revert the FQV2-007 PR to remove the geometry contract, tests, schema, and
evidence artifacts. This task does not alter production data or migrations.

## Memory Candidate

- memory_type: implementation_lesson
- content: Flange QC v2 geometry evidence requires 3 length points, 3 width points, and 2 diagonals; diagonal deviation is evidence only and remains blocked without QC/SOP tolerance approval.
- source_ref: https://github.com/namlogan/MIL/issues/71
- why reusable: Future decision-engine and HMI tasks need this boundary to avoid premature production PASS/NG authority.
- scope: project:flange_qc_v2
- suggested status: candidate
