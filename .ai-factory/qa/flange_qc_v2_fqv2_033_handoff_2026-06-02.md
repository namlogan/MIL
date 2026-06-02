# FQV2-033 QA Handoff: QC Device Phase Layout

## Source

- GitHub issue: https://github.com/namlogan/MIL/issues/123
- Branch: `agent/123-qc-device-phase-layout`
- Task: FQV2-033

## Files Changed

- `apps/flange_qc_v2/static/hmi.html`
- `tests/flange_qc_v2/test_hmi_screen.py`
- `docs/project/flange_qc_v2/USER_FLOWS.md`
- `docs/project/flange_qc_v2/DATA_MODEL.md`
- `docs/project/flange_qc_v2/TEST_STRATEGY.md`
- `.ai-factory/gates/flange_qc_v2_fqv2_033_dor.json`
- `.ai-factory/qa/flange_qc_v2_fqv2_033_handoff_2026-06-02.md`
- `.ai-factory/qa/flange_qc_v2_fqv2_033_hmi.png`
- `.ai-factory/qa/flange_qc_v2_fqv2_033_hmi_snapshot.md`

## Rules Applied

- One task per branch.
- GitHub issue is source of truth for requirement, acceptance criteria, and
  allowed paths.
- TDD RED/GREEN checkpoints were used before implementation.
- HMI layout reads existing `phase_results`; it does not change decision engine
  logic, detector authority, production PASS/NG authority, or SOP tolerance
  approval.
- No backend detector/replay contract changes, raw media, raw datasets,
  customer data, notebooks, model weights, model binaries, model deserialization,
  model inference, camera SDK import, live camera capture, GPU use, secrets,
  destructive migration, deployment, product spec approval, QC/SOP tolerance
  approval, model promotion, production PASS/NG authority, or production
  auto-reject behavior is introduced.

## Implementation Notes

- Added a QC-device phase layout near the top of `/hmi`.
- Rendered Phase 1 dimensions and Phase 2 stitch-watch as independent cards.
- Added a Phase 2 suspected-stitch visual zone.
- Mapped `PASS` to green/ok, `NG` to red/error, and all review/blocked/assist
  states to amber/warn for operator scanability.
- Existing SOP phase-results drilldown, artifact intake, detector bridge,
  detector observations, and feedback panels remain available below.

## Tests Run

- RED: `python3 -m unittest tests.flange_qc_v2.test_hmi_screen -v` failed
  because HMI lacked the QC-device phase layout and traffic-state renderer.
- GREEN: `python3 -m unittest tests.flange_qc_v2.test_hmi_screen -v` passed,
  8 tests.
- Browser evidence on `http://127.0.0.1:8765/hmi` with
  `FLANGE_QC_V2_ARTIFACT_INTAKE_DIR=templates/flange_qc_v2/artifact_intake`
  showed `QC device phase layout`, `Phase 1 Dimensions`, `Phase 2 Stitch
  Watch`, `Suspected stitch area`, and amber `REVIEW` state for the blocked
  replay sample.
- Browser snapshot artifact:
  `.ai-factory/qa/flange_qc_v2_fqv2_033_hmi_snapshot.md`.
- Browser screenshot artifact:
  `.ai-factory/qa/flange_qc_v2_fqv2_033_hmi.png`.
- `python3 -m json.tool .ai-factory/gates/flange_qc_v2_fqv2_033_dor.json`:
  passed.
- `python3 -m unittest discover -s tests/flange_qc_v2 -v` passed, 128 tests.
- `python3 -m compileall -q apps/flange_qc_v2 tests/flange_qc_v2` passed.
- `python3 scripts/product-ci/run_product_checks.py` passed.
- `python3 -m unittest discover -s tests -v` passed, 196 tests.
- `git diff --check` passed.

## Residual Risks

- Browser verification used a temporary metadata HTTP server because `uvicorn`
  is not installed in the current Python environment. The temp server does not
  implement WebSocket upgrade, so one browser console error was expected for the
  `/ws/inspection` handshake; the real ASGI WebSocket path remains covered by
  `tests/flange_qc_v2/test_hmi_stream.py`.
- The Phase 2 stitch-watch zone is a QC visual status mapped from current phase
  decision state. It does not add real stitch-defect inference, model promotion,
  live camera behavior, or production rejection authority.
- Product specs, QC/SOP tolerances, model approval/promotion, live camera
  readiness, and production release remain human-gated.

## Rollback

Revert the FQV2-033 PR to remove the QC-device phase layout and Phase 2
suspected-stitch visual zone. Existing SOP drilldown, replay/HMI snapshots,
detector bridge, detector observations, artifact intake, and feedback behavior
remain valid. No migration, model rollback, camera rollback, dataset rollback,
or deploy rollback is required.

## Memory Candidate

- memory_type: implementation_lesson
- content: Flange QC v2 HMI now presents a QC-device phase layout with Phase 1
  and Phase 2 independent cards, plus a Phase 2 suspected-stitch traffic zone
  using green PASS, red NG, and amber review/blocked display states while
  preserving shadow-only authority.
- source_ref: https://github.com/namlogan/MIL/issues/123
- why reusable: Future QC-device UI work should improve operator scanability by
  reading existing evidence, not by changing backend decision authority.
- scope: project:flange_qc_v2
- suggested status: candidate
