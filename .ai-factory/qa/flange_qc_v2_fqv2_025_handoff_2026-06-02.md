# FQV2-025 QA Handoff: SOP Safe Fallback Evaluator

## Source

- GitHub issue: https://github.com/namlogan/MIL/issues/107
- Branch: `agent/107-sop-safe-fallback-evaluator`
- Task: FQV2-025

## Files Changed

- `apps/flange_qc_v2/decision_engine.py`
- `tests/flange_qc_v2/test_decision_engine.py`
- `docs/project/flange_qc_v2/SOP_RULE_REGISTRY.md`
- `docs/project/flange_qc_v2/DATA_MODEL.md`
- `docs/project/flange_qc_v2/TEST_STRATEGY.md`
- `.ai-factory/gates/flange_qc_v2_fqv2_025_dor.json`
- `.ai-factory/qa/flange_qc_v2_fqv2_025_handoff_2026-06-02.md`

## Rules Applied

- One task per branch.
- GitHub issue is source of truth for requirement, acceptance criteria, and
  allowed paths.
- TDD RED/GREEN checkpoints were used before implementation.
- Phase 3/4 fallback evidence is registry-driven and cannot grant production
  authority.
- No model loading, model inference, training, dataset ingestion, live camera,
  raw media, customer data, secrets, deployment, destructive migration,
  production PASS/NG authority, or production auto-reject behavior is
  introduced.

## Implementation Notes

- Added `evaluate_sop_safe_fallbacks(phase=...)` for `PHASE_3` and `PHASE_4`.
- The evaluator filters `list_rules()` from `sop_registry.py`, so fallback rule
  results follow registry metadata instead of a hardcoded phase rule list.
- Phase 3 model/vision rules return `ASSIST` with `MODEL_REVIEW_REQUIRED` and
  `MODEL_APPROVAL_REQUIRED` as an authority blocker.
- Phase 4 post-MVP rules return `NOT_EVALUATED` with `RULE_POST_MVP_DISABLED`.
- Phase 4 review-dependent rules return `ASSIST` with `MODEL_REVIEW_REQUIRED`.
- Aggregate fallback decision returns `ASSIST` when any rule needs review and
  otherwise `NOT_EVALUATED`; it never maps fallback states to `PASS`.
- Rule evidence includes `fallback_source`, registry `category`, registry
  `authority`, and `production_enabled`.

## Tests Run

- RED: `python3 -m unittest tests.flange_qc_v2.test_decision_engine -v`
  failed because `evaluate_sop_safe_fallbacks` did not exist.
- GREEN: `python3 -m unittest tests.flange_qc_v2.test_decision_engine -v`
  passed, 11 tests.
- `python3 -m compileall -q apps/flange_qc_v2 tests/flange_qc_v2` passed.
- `python3 -m json.tool .ai-factory/gates/flange_qc_v2_fqv2_025_dor.json >/dev/null`
  passed.
- `git diff --check` passed.
- `python3 -m unittest discover -s tests/flange_qc_v2 -v` passed, 115 tests.
- `python3 scripts/product-ci/run_product_checks.py` passed.
- `python3 -m unittest discover -s tests -v` passed, 196 tests.

## Residual Risks

- Fallback evaluator is not yet wired into replay/HMI/audit output; it prepares
  the rule evidence path for a later integration issue.
- Model-dependent rules still need real model artifacts, evaluation evidence,
  and supervised QC approval before any production use.
- Product specs, QC/SOP tolerances, live camera/hardware readiness, model
  promotion, and production release remain blocked human gates.

## Rollback

Revert the FQV2-025 PR to remove Phase 3/4 fallback evaluator changes, tests,
docs, and gate evidence. No production data migration, model rollback, hardware
rollback, or deploy rollback is required.

## Memory Candidate

- memory_type: implementation_lesson
- content: Flange QC v2 Phase 3/4 SOP fallback logic is registry-driven:
  model/review-dependent rules emit ASSIST, post-MVP rules emit NOT_EVALUATED,
  and fallback states never map to PASS or production authority.
- source_ref: https://github.com/namlogan/MIL/issues/107
- why reusable: Future replay/HMI/audit integration can surface full SOP chain
  evidence without enabling model, camera, or production PASS/NG authority.
- scope: project:flange_qc_v2
- suggested status: candidate
