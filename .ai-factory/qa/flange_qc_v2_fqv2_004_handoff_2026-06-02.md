# FQV2-004 Handoff Evidence

Date: 2026-06-02

## Task

GitHub issue: <https://github.com/namlogan/MIL/issues/65>

Branch:

```text
agent/65-product-specs-validator
```

## Summary

Adds draft product-spec config validation and lookup for Flange QC v2. Known
product/size pairs resolve to nominal dimensions and plus/minus tolerances from
the versioned JSON config, while carrying draft approval status and keeping
`production_authority` false.

Unknown products and unknown sizes fail closed with stable reason codes.

## Files Changed

- `apps/flange_qc_v2/product_specs.py`
- `apps/flange_qc_v2/sop_registry.py`
- `tests/flange_qc_v2/test_product_specs.py`
- `docs/project/flange_qc_v2/APPROVAL_REQUEST_PRODUCT_SPECS.md`
- `.ai-factory/gates/flange_qc_v2_fqv2_004_dor.json`
- `.ai-factory/qa/flange_qc_v2_fqv2_004_handoff_2026-06-02.md`

## Rules Applied

- GitHub issue is the task source of truth.
- One task branch is used.
- Codex is the implementation worker.
- TDD red/green was used for the resolver behavior.
- No production deploy, secrets, customer data, destructive migrations, live
  camera, model weights, TensorRT engines, production SOP PASS/NG engine, or
  production tolerance approval were added.

## Tests Run

```text
python3 -m unittest tests.flange_qc_v2.test_product_specs -v
python3 -m unittest discover -s tests/flange_qc_v2 -v
python3 -m compileall -q apps/flange_qc_v2 tests/flange_qc_v2
python3 scripts/product-ci/run_product_checks.py
python3 -m unittest discover -s tests -v
git diff --check
```

## Residual Risks

- Product specs remain draft and not production-approved.
- The resolver exposes tolerance data for bootstrap/replay tests only; final
  production PASS/NG decision logic remains future work.
- Additional schema file validation can be added later if needed, but current
  loader validation rejects missing core shape.

## Rollback

Revert the FQV2-004 PR to remove the product spec loader/resolver and related
tests/evidence. Earlier bootstrap/domain/SOP registry work can remain intact.

## Memory Candidate

- memory_type: implementation_lesson
- content: Flange QC v2 product spec lookup lives in
  `apps/flange_qc_v2/product_specs.py`; it resolves known draft config values
  but returns `production_authority=false` and `BLOCKED` until approval evidence
  exists.
- source_ref: GitHub issue #65 and the FQV2-004 PR
- why reusable: Future decision-engine, replay, and HMI work should use this
  resolver instead of reading config ad hoc or hardcoding dimensions.
- scope: project
- suggested status: candidate

## AIF Gate Result

```text
aif-gate-result:
  decision: APPROVE_MERGE
  reasons:
    - Product spec validation and lookup are scoped to draft bootstrap config.
    - Unknown product and unknown size fail closed.
    - Production authority remains false for current draft config.
  tests:
    - python3 -m unittest tests.flange_qc_v2.test_product_specs -v
    - python3 -m unittest discover -s tests/flange_qc_v2 -v
  residual_risks:
    - Product specs still require QC/domain approval before production use.
    - Final SOP PASS/NG logic remains future work.
```
