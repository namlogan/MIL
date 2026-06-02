# FQV2-002 Handoff Evidence

Date: 2026-06-02

## Task

GitHub issue: <https://github.com/namlogan/MIL/issues/61>

Branch:

```text
agent/61-domain-models-websocket-contracts
```

## Summary

Adds Flange QC v2 domain payload models and a WebSocket/HMI inspection snapshot
contract. The work keeps the app in bootstrap-safe mode: unknown products and
missing production capabilities remain represented as `BLOCKED`, degraded, or
not implemented states.

## Files Changed

- `apps/flange_qc_v2/domain.py`
- `apps/flange_qc_v2/health.py`
- `contracts/flange_qc_v2/websocket/inspection_snapshot.schema.json`
- `tests/flange_qc_v2/test_domain_contracts.py`
- `.ai-factory/gates/flange_qc_v2_fqv2_002_dor.json`
- `.ai-factory/qa/flange_qc_v2_fqv2_002_handoff_2026-06-02.md`

## Rules Applied

- GitHub issue is the task source of truth.
- One task branch is used.
- Codex is the implementation worker.
- TDD red/green was used for the new domain behavior.
- No production deploy, secrets, customer data, destructive migrations, live
  camera, model weights, TensorRT engines, or production SOP PASS/NG approval
  logic were added.

## Tests Run

```text
python3 -m unittest tests.flange_qc_v2.test_domain_contracts -v
python3 -m unittest tests.flange_qc_v2.test_health -v
python3 -m unittest discover -s tests/flange_qc_v2 -v
python3 -m compileall -q apps/flange_qc_v2 tests/flange_qc_v2
python3 scripts/product-ci/run_product_checks.py
python3 -m unittest discover -s tests -v
git diff --check
```

## Residual Risks

- JSON schema is contract-first evidence; runtime schema validation is not wired
  to an external validator in this task.
- Product tolerance and SOP PASS/NG behavior remain blocked until a separate
  product spec and QC/SOP approval gate.
- WebSocket transport is not implemented in this task; only the payload contract
  and domain model exist.

## Rollback

Revert the FQV2-002 PR to remove the domain model module, WebSocket schema
contract, and related tests. FQV2-001 health/app skeleton can remain intact.

## Memory Candidate

- memory_type: implementation_lesson
- content: Flange QC v2 domain payload validation is stdlib dataclass based; bbox
  and confidence values are constrained to [0, 1], and bootstrap snapshots use
  `BLOCKED` instead of production PASS/NG decisions.
- source_ref: GitHub issue #61 and the FQV2-002 PR
- why reusable: Future HMI, replay, detector, and SOP-rule work should reuse this
  payload vocabulary instead of adding parallel shapes.
- scope: project
- suggested status: candidate

## AIF Gate Result

```text
aif-gate-result:
  decision: APPROVE_MERGE
  reasons:
    - Domain payload validation is scoped to FQV2-002.
    - Bootstrap safety boundaries remain explicit.
    - New tests cover bbox range, unknown decisions, measurement cardinality,
      subsystem health, and schema constraints.
  tests:
    - python3 -m unittest tests.flange_qc_v2.test_domain_contracts -v
    - python3 -m unittest tests.flange_qc_v2.test_health -v
  residual_risks:
    - Runtime WebSocket transport remains future work.
    - Product tolerance approval remains a future human/domain gate.
```
