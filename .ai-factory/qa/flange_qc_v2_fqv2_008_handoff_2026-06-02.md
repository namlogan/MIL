# FQV2-008 QA Handoff: Shadow Phase Gate And Decision Engine

## Source

- GitHub issue: https://github.com/namlogan/MIL/issues/73
- Branch: `agent/73-shadow-phase-gate-decision-engine`
- Task: FQV2-008

## Files Changed

- `apps/flange_qc_v2/decision_engine.py`
- `apps/flange_qc_v2/sop_registry.py`
- `tests/flange_qc_v2/test_decision_engine.py`
- `tests/flange_qc_v2/test_sop_registry.py`
- `docs/project/flange_qc_v2/DATA_MODEL.md`
- `docs/project/flange_qc_v2/SOP_RULE_REGISTRY.md`
- `.ai-factory/gates/flange_qc_v2_fqv2_008_dor.json`
- `.ai-factory/qa/flange_qc_v2_fqv2_008_handoff_2026-06-02.md`

## Rules Applied

- One task per branch.
- GitHub issue is source of truth for requirement, acceptance criteria, and allowed paths.
- TDD red/green was used before implementation.
- Shadow decision evidence is separated from production authority.
- QC/SOP tolerance approval remains a human gate.

## Implementation Notes

- Added `evaluate_phase_two_geometry` for phase-2 diagonal deviation evidence.
- Draft product specs or synthetic calibration block before shadow PASS/NG.
- Incomplete geometry blocks with `MEASUREMENTS_INCOMPLETE`.
- Diagonal deviation greater than 0.5 inch returns shadow `NG` with `DIAGONAL_DEVIATION_EXCEEDS_LIMIT`.
- Diagonal deviation less than or equal to 0.5 inch returns shadow `PASS` with no PASS reason code.
- `production_authority` remains false for all decision results.

## Tests Run

- `python3 -m unittest tests.flange_qc_v2.test_decision_engine -v`
- `python3 -m unittest tests.flange_qc_v2.test_sop_registry -v`

Additional required checks before PR review:

- `python3 -m unittest discover -s tests/flange_qc_v2 -v`
- `python3 -m compileall -q apps/flange_qc_v2 tests/flange_qc_v2`
- `python3 scripts/product-ci/run_product_checks.py`
- `python3 -m unittest discover -s tests -v`
- `git diff --check`

## Residual Risks

- Shadow PASS/NG is not production authority.
- QC/SOP tolerance approval is still required before production use.
- Product spec approval and calibration approval remain required for production.
- Replay frame source, HMI, and production release gates are not implemented in this task.

## Rollback

Revert the FQV2-008 PR to remove the shadow decision engine, tests, rule metadata
update, and evidence artifacts. This task does not alter production data,
migrations, secrets, or deploy configuration.

## Memory Candidate

- memory_type: implementation_lesson
- content: Flange QC v2 phase-2 diagonal deviation can produce shadow PASS/NG evidence, but production_authority stays false and QC/SOP tolerance approval remains an authority blocker.
- source_ref: https://github.com/namlogan/MIL/issues/73
- why reusable: Future replay, HMI, and release tasks need to preserve the shadow-vs-production boundary.
- scope: project:flange_qc_v2
- suggested status: candidate
