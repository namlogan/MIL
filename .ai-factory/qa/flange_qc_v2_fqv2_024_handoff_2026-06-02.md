# FQV2-024 QA Handoff: Phase 1 SOP Shadow Evaluation

## Source

- GitHub issue: https://github.com/namlogan/MIL/issues/105
- Branch: `agent/105-phase-one-sop-shadow-eval`
- Task: FQV2-024

## Files Changed

- `apps/flange_qc_v2/decision_engine.py`
- `apps/flange_qc_v2/sop_registry.py`
- `tests/flange_qc_v2/test_decision_engine.py`
- `tests/flange_qc_v2/test_sop_registry.py`
- `docs/project/flange_qc_v2/SOP_RULE_REGISTRY.md`
- `docs/project/flange_qc_v2/DATA_MODEL.md`
- `docs/project/flange_qc_v2/TEST_STRATEGY.md`
- `.ai-factory/gates/flange_qc_v2_fqv2_024_dor.json`
- `.ai-factory/qa/flange_qc_v2_fqv2_024_handoff_2026-06-02.md`

## Rules Applied

- One task per branch.
- GitHub issue is source of truth for requirement, acceptance criteria, and
  allowed paths.
- TDD RED/GREEN checkpoints were used before implementation.
- Phase 1 evidence is shadow-only and cannot grant production authority.
- Product specs, QC/SOP tolerances, camera hardware, model promotion, and
  production release remain human-gated.
- No raw media, customer data, model weights, secrets, live capture, deployment,
  destructive migrations, production PASS/NG authority, or production
  auto-reject behavior is introduced.

## Implementation Notes

- Added `evaluate_phase_one_measurements()` to evaluate length and width from
  existing product spec, calibration, and geometry resolutions.
- Product spec, calibration, and geometry blockers return `BLOCKED` before any
  shadow PASS/NG evidence.
- Added rule-level `RuleResult` evidence for:
  - `M1-SOP-6.1-LENGTH-001`
  - `M1-SOP-6.1-WIDTH-001`
- Evidence includes source unit, inch-normalized points, nominal value,
  tolerance plus/minus, lower/upper bounds, min/max/average, and
  out-of-tolerance point indexes.
- Added `LENGTH_OUT_OF_TOLERANCE` and `WIDTH_OUT_OF_TOLERANCE` reason codes.
- Used `all_points_must_pass_bootstrap` as a conservative shadow-only aggregate
  assumption while the final SOP aggregate method remains open.

## Tests Run

- RED: `python3 -m unittest tests.flange_qc_v2.test_decision_engine -v`
  failed because `evaluate_phase_one_measurements` did not exist.
- RED: `python3 -m unittest tests.flange_qc_v2.test_sop_registry -v`
  failed because `LENGTH_OUT_OF_TOLERANCE` and `WIDTH_OUT_OF_TOLERANCE` did not
  exist.
- GREEN: `python3 -m unittest tests.flange_qc_v2.test_decision_engine -v`
  passed, 8 tests.
- GREEN: `python3 -m unittest tests.flange_qc_v2.test_sop_registry -v` passed,
  7 tests.
- `python3 -m compileall -q apps/flange_qc_v2 tests/flange_qc_v2` passed.
- `python3 -m json.tool .ai-factory/gates/flange_qc_v2_fqv2_024_dor.json >/dev/null`
  passed.
- `python3 -m unittest discover -s tests/flange_qc_v2 -v` passed, 112 tests.
- `python3 scripts/product-ci/run_product_checks.py` passed.
- `git diff --check` passed.
- `python3 -m unittest discover -s tests -v` passed, 196 tests.

## Residual Risks

- Length/width aggregate method still needs QC/domain owner approval; current
  all-points behavior is bootstrap shadow evidence only.
- Product specs are still draft and require product spec approval before
  production authority.
- QC/SOP tolerance approval, model approval, live camera/hardware readiness, and
  production release approval remain blocked human gates.
- HMI/replay currently do not surface Phase 1 result yet; this PR adds the
  deterministic evaluator needed for a later integration issue.

## Rollback

Revert the FQV2-024 PR to remove Phase 1 evaluator changes, reason codes, tests,
docs, and gate evidence. No production data migration, model rollback, hardware
rollback, or deploy rollback is required.

## Memory Candidate

- memory_type: implementation_lesson
- content: Flange QC v2 Phase 1 length/width SOP logic now has a shadow-only
  evaluator using conservative all-points-must-pass bootstrap evidence, but the
  aggregate method and tolerances still require QC/domain owner approval before
  production authority.
- source_ref: https://github.com/namlogan/MIL/issues/105
- why reusable: Future HMI/replay/model integration issues can call the Phase 1
  evaluator while preserving fail-closed production gates.
- scope: project:flange_qc_v2
- suggested status: candidate
