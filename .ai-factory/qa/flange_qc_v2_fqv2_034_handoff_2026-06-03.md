# FQV2-034 QA Handoff: Signal-First QC Tablet Viewport

## Source

- GitHub issue: https://github.com/namlogan/MIL/issues/125
- Branch: `agent/125-qc-tablet-viewport`
- Task: FQV2-034

## Files Changed

- `apps/flange_qc_v2/static/hmi.html`
- `tests/flange_qc_v2/test_hmi_screen.py`
- `docs/project/flange_qc_v2/USER_FLOWS.md`
- `docs/project/flange_qc_v2/DATA_MODEL.md`
- `docs/project/flange_qc_v2/TEST_STRATEGY.md`
- `docs/superpowers/specs/2026-06-03-qc-tablet-viewport-design.md`
- `docs/superpowers/plans/2026-06-03-qc-tablet-viewport.md`
- `.ai-factory/gates/flange_qc_v2_fqv2_034_dor.json`
- `.ai-factory/qa/flange_qc_v2_fqv2_034_handoff_2026-06-03.md`
- `.ai-factory/qa/flange_qc_v2_fqv2_034_hmi_snapshot.md`
- `.ai-factory/qa/flange_qc_v2_fqv2_034_hmi_tablet.png`

## Rules Applied

- One task per branch.
- GitHub issue is source of truth for requirement, acceptance criteria, and
  allowed paths.
- TDD RED/GREEN checkpoints were used before implementation.
- HMI reads existing replay snapshot, `phase_results`, feedback contract, and
  review-only detector observations; it does not change backend inspection
  authority.
- No live camera enablement, camera SDK loading, raw media ingestion, raw
  factory/customer data, model weights, model binaries, model deserialization,
  training code, runtime inference, MLOps promotion, production deploy, release
  approval, product spec approval, QC/SOP tolerance approval, destructive
  migration, production PASS/NG authority, or production auto-reject behavior is
  introduced.

## Implementation Notes

- Replaced the dense first HMI viewport with a signal-first QC tablet viewport.
- Added top measurement chips for product, length, width, and diagonal/stitch
  state.
- Added green `PASS`, red `CHECK`, and amber `REVIEW` operator banner mapping.
- Added an image well that draws normalized bbox overlays from review-only
  detector observations.
- Added red-alert feedback buttons: `Alert correct` writes `CONFIRM_BLOCKED`,
  and `False alarm` writes `MARK_FALSE_POSITIVE` through the existing
  `/feedback` endpoint.
- Existing SOP drilldown, detector bridge, detector observations, artifact
  intake, and feedback form remain below the first viewport.

## Tests Run

- RED: `python3 -m unittest tests.flange_qc_v2.test_hmi_screen -v` failed
  before implementation because HMI lacked `qc-tablet-viewport` and
  `renderQcTabletViewport`.
- GREEN: `python3 -m unittest tests.flange_qc_v2.test_hmi_screen -v` passed,
  9 tests.
- Browser evidence on `http://127.0.0.1:8765/hmi` at `1024x768` with
  `FLANGE_QC_V2_ARTIFACT_INTAKE_DIR=templates/flange_qc_v2/artifact_intake`
  showed red `CHECK`, `Inspect suspected area`, visible suspected-region bbox
  overlay, `punch_mark / 0.87`, and alarm buttons mapped to
  `CONFIRM_BLOCKED` / `MARK_FALSE_POSITIVE`.
- Browser snapshot artifact:
  `.ai-factory/qa/flange_qc_v2_fqv2_034_hmi_snapshot.md`.
- Browser screenshot artifact:
  `.ai-factory/qa/flange_qc_v2_fqv2_034_hmi_tablet.png`.
- `python3 -m json.tool .ai-factory/gates/flange_qc_v2_fqv2_034_dor.json`:
  passed.
- `python3 -m compileall -q apps/flange_qc_v2 tests/flange_qc_v2` passed.
- `git diff --check` passed.
- `python3 -m unittest discover -s tests/flange_qc_v2 -v` passed, 129 tests.
- `python3 scripts/product-ci/run_product_checks.py` passed.
- `python3 -m unittest discover -s tests -v` passed, 196 tests.

## Residual Risks

- Browser verification used a temporary metadata HTTP server and no live camera.
  This is intentional for FQV2-034; live capture remains blocked until hardware
  readiness and owner approval.
- The image well currently uses synthetic/replay visual evidence and normalized
  bbox metadata only. Real captured product images require a future camera/model
  contract issue.
- Detector observations remain review-only and cannot decide final production
  PASS/NG.
- Product specs, QC/SOP tolerances, model approval/promotion, live camera
  readiness, production deployment, and release remain human-gated.

## Rollback

Revert the FQV2-034 PR to restore the previous HMI first viewport. Existing
backend replay, decision engine, detector bridge, artifact intake, SOP
drilldown, and feedback contracts remain valid. No migration, camera, model,
dataset, or deploy rollback is required.

## Memory Candidate

- memory_type: implementation_lesson
- content: Flange QC v2 HMI now uses a signal-first QC tablet viewport with top
  measurement chips, green PASS, red CHECK, amber REVIEW, suspected-region bbox
  overlay, and alarm-correct/false-alarm feedback while preserving shadow-only
  authority.
- source_ref: https://github.com/namlogan/MIL/issues/125
- why reusable: Future QC tablet work should keep operator action visible first
  and route model-training feedback through existing shadow evidence contracts.
- scope: project:flange_qc_v2
- suggested status: candidate
