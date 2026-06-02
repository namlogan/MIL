# FQV2-003 Handoff Evidence

Date: 2026-06-02

## Task

GitHub issue: <https://github.com/namlogan/MIL/issues/63>

Branch:

```text
agent/63-sop-rule-registry-reason-codes
```

## Summary

Adds bootstrap-safe SOP rule metadata and reason-code vocabulary for Flange QC
v2. The registry provides stable identifiers, phases, categories, authority
labels, safe fallback decisions, and reason codes for later HMI, audit, replay,
and decision-engine work.

This task does not implement product tolerance resolution or production PASS/NG
logic.

## Files Changed

- `apps/flange_qc_v2/sop_registry.py`
- `tests/flange_qc_v2/test_sop_registry.py`
- `docs/project/flange_qc_v2/SOP_RULE_REGISTRY.md`
- `.ai-factory/gates/flange_qc_v2_fqv2_003_dor.json`
- `.ai-factory/qa/flange_qc_v2_fqv2_003_handoff_2026-06-02.md`

## Rules Applied

- GitHub issue is the task source of truth.
- One task branch is used.
- Codex is the implementation worker.
- TDD red/green was used for the new registry behavior.
- No production deploy, secrets, customer data, destructive migrations, live
  camera, model weights, TensorRT engines, product tolerance resolver, or
  production SOP PASS/NG engine were added.

## Tests Run

```text
python3 -m unittest tests.flange_qc_v2.test_sop_registry -v
python3 -m unittest discover -s tests/flange_qc_v2 -v
python3 -m compileall -q apps/flange_qc_v2 tests/flange_qc_v2
python3 scripts/product-ci/run_product_checks.py
python3 -m unittest discover -s tests -v
git diff --check
```

## Residual Risks

- This is metadata only; later product spec validation and decision-engine work
  must continue to fail closed until approval evidence exists.
- Model-dependent rules remain review/assist oriented until model and QC
  approval gates exist.

## Rollback

Revert the FQV2-003 PR to remove the SOP registry/reason-code metadata and
related tests. FQV2-001 and FQV2-002 can remain intact.

## Memory Candidate

- memory_type: implementation_lesson
- content: Flange QC v2 SOP metadata lives in `apps/flange_qc_v2/sop_registry.py`;
  registry lookups reject unknown IDs/codes, and documented but unapproved rules
  expose safe fallback decisions rather than production PASS/NG authority.
- source_ref: GitHub issue #63 and the FQV2-003 PR
- why reusable: Future product spec, decision-engine, HMI, replay, and audit
  tasks should reference these stable rule IDs and reason codes.
- scope: project
- suggested status: candidate

## AIF Gate Result

```text
aif-gate-result:
  decision: APPROVE_MERGE
  reasons:
    - SOP registry is scoped to metadata and reason codes.
    - Unknown rule IDs and reason codes are rejected explicitly.
    - Model-dependent and post-MVP rules remain safely non-production.
  tests:
    - python3 -m unittest tests.flange_qc_v2.test_sop_registry -v
    - python3 -m unittest discover -s tests/flange_qc_v2 -v
  residual_risks:
    - Product tolerance resolver remains future work.
    - Production SOP PASS/NG authority remains blocked pending approval evidence.
```
