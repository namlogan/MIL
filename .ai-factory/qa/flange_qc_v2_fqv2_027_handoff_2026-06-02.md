# FQV2-027 QA Handoff: HMI SOP Phase Results Drilldown

## Source

- GitHub issue: https://github.com/namlogan/MIL/issues/111
- Branch: `agent/111-hmi-phase-results-drilldown`
- Task: FQV2-027

## Files Changed

- `apps/flange_qc_v2/static/hmi.html`
- `tests/flange_qc_v2/test_hmi_screen.py`
- `docs/project/flange_qc_v2/DATA_MODEL.md`
- `docs/project/flange_qc_v2/USER_FLOWS.md`
- `docs/project/flange_qc_v2/TEST_STRATEGY.md`
- `.ai-factory/gates/flange_qc_v2_fqv2_027_dor.json`
- `.ai-factory/qa/flange_qc_v2_fqv2_027_handoff_2026-06-02.md`
- `.ai-factory/qa/flange_qc_v2_fqv2_027_hmi.png`
- `.ai-factory/qa/flange_qc_v2_fqv2_027_hmi_snapshot.md`

## Rules Applied

- One task per branch.
- GitHub issue is source of truth for requirement, acceptance criteria, and
  allowed paths.
- TDD RED/GREEN checkpoints were used before implementation.
- HMI drilldown consumes existing replay/HMI `phase_results` payload data.
- No model/camera execution, raw media, customer data, dataset ingestion,
  secrets, destructive migration, deployment, product spec approval, QC/SOP
  tolerance approval, production PASS/NG authority, or production auto-reject
  behavior is introduced.

## Implementation Notes

- The HMI now renders an operator-facing SOP phase-results section below the
  top-level reason/measurement panels.
- Each phase card shows phase, decision, phase reason codes, authority blockers,
  and production-authority state.
- Rule results render rule id, rule decision, rule reason codes, and a compact
  evidence summary.
- Empty or missing `phase_results` renders `No phase results`.
- Existing top-level status, reason list, measurements, replay refresh,
  WebSocket snapshot render, and feedback form bindings remain in place.

## Tests Run

- RED: `python3 -m unittest tests.flange_qc_v2.test_hmi_screen -v` failed
  because the prior HMI did not expose `id="phase-results"` or bind
  `payload.phase_results`.
- GREEN: `python3 -m unittest tests.flange_qc_v2.test_hmi_screen -v` passed, 4
  tests.
- Browser evidence: `http://127.0.0.1:8765/hmi` rendered 4 phase cards from the
  replay snapshot, including `PHASE_1`, `PHASE_2`, `PHASE_3`, `PHASE_4`,
  `M1-SOP-6.4-PUNCH-MARK-001`, `PRODUCTION_APPROVAL_REQUIRED`, and
  `production_authority=false`.
- Browser snapshot artifact:
  `.ai-factory/qa/flange_qc_v2_fqv2_027_hmi_snapshot.md`.
- Browser screenshot artifact:
  `.ai-factory/qa/flange_qc_v2_fqv2_027_hmi.png`.
- `python3 -m unittest tests.flange_qc_v2.test_hmi_stream -v` passed, 4
  tests.
- `python3 -m json.tool .ai-factory/gates/flange_qc_v2_fqv2_027_dor.json`
  passed.
- `git diff --check` passed.
- `python3 -m unittest discover -s tests/flange_qc_v2 -v` passed, 116 tests.
- `python3 -m compileall -q apps/flange_qc_v2 tests/flange_qc_v2` passed.
- `python3 scripts/product-ci/run_product_checks.py` passed.
- `python3 -m unittest discover -s tests -v` passed, 196 tests.

## Residual Risks

- Browser verification used a local stdlib test server because `uvicorn` is not
  installed in the current Python environment and the Browser plugin had no
  available `iab` backend. Playwright fallback verified the rendered local HMI.
- Product specs, QC/SOP tolerances, model approval/promotion, live camera
  readiness, and production release remain human-gated.
- Current replay remains synthetic/no-camera and does not prove live factory
  image, camera, or model behavior.

## Rollback

Revert the FQV2-027 PR to remove the HMI phase-results drilldown and restore the
prior static HMI screen. No migration, model rollback, camera rollback, dataset
rollback, or deploy rollback is required.

## Memory Candidate

- memory_type: implementation_lesson
- content: Flange QC v2 HMI now renders ordered SOP phase_results as operator
  drilldown cards with rule evidence, blockers, and production-authority state.
- source_ref: https://github.com/namlogan/MIL/issues/111
- why reusable: Future HMI, QA, and model handoff work can use the same snapshot
  phase-results contract for operator-facing rule evidence without enabling
  production authority.
- scope: project:flange_qc_v2
- suggested status: candidate
