# FQV2-031 QA Handoff: HMI Detector Observation Details

## Source

- GitHub issue: https://github.com/namlogan/MIL/issues/119
- Branch: `agent/119-hmi-detector-observation-panel`
- Task: FQV2-031

## Files Changed

- `apps/flange_qc_v2/static/hmi.html`
- `tests/flange_qc_v2/test_hmi_screen.py`
- `docs/project/flange_qc_v2/USER_FLOWS.md`
- `docs/project/flange_qc_v2/DATA_MODEL.md`
- `docs/project/flange_qc_v2/TEST_STRATEGY.md`
- `.ai-factory/gates/flange_qc_v2_fqv2_031_dor.json`
- `.ai-factory/qa/flange_qc_v2_fqv2_031_handoff_2026-06-02.md`
- `.ai-factory/qa/flange_qc_v2_fqv2_031_hmi.png`
- `.ai-factory/qa/flange_qc_v2_fqv2_031_hmi_snapshot.md`

## Rules Applied

- One task per branch.
- GitHub issue is source of truth for requirement, acceptance criteria, and
  allowed paths.
- TDD RED/GREEN checkpoints were used before implementation.
- HMI only renders fields already present in `payload.observations`.
- No backend detector/replay contract changes were introduced.
- No request-supplied arbitrary filesystem path, raw media, raw datasets,
  customer data, notebooks, model weights, model binaries, model deserialization,
  model inference, camera SDK import, live camera capture, GPU use, secrets,
  destructive migration, deployment, product spec approval, QC/SOP tolerance
  approval, model promotion, production PASS/NG authority, or production
  auto-reject behavior is introduced.

## Implementation Notes

- Added a `Detector Observations` panel to `/hmi`.
- Added `renderDetectorObservations()` with a safe empty state.
- Present observations show label, confidence, bbox, `model_ref`, and
  `evidence_ref`.
- Existing `Observation` state continues to show `present` or `none`.
- Added screen test coverage for the panel and renderer bindings.

## Tests Run

- RED: `python3 -m unittest tests.flange_qc_v2.test_hmi_screen -v` failed
  because HMI lacked the detector observations panel and renderer.
- GREEN: `python3 -m unittest tests.flange_qc_v2.test_hmi_screen -v` passed,
  6 tests.
- `python3 -m unittest tests.flange_qc_v2.test_hmi_stream -v` passed, 5 tests.
- Browser evidence on `http://127.0.0.1:8765/hmi` with
  `FLANGE_QC_V2_ARTIFACT_INTAKE_DIR=templates/flange_qc_v2/artifact_intake`
  showed observation state `present`, `punch_mark`, `confidence: 0.87`, bbox,
  manifest `model_ref`, and evaluation `evidence_ref`.
- Browser snapshot artifact:
  `.ai-factory/qa/flange_qc_v2_fqv2_031_hmi_snapshot.md`.
- Browser screenshot artifact:
  `.ai-factory/qa/flange_qc_v2_fqv2_031_hmi.png`.
- `python3 -m json.tool .ai-factory/gates/flange_qc_v2_fqv2_031_dor.json`
  passed.
- `python3 -m unittest discover -s tests/flange_qc_v2 -v` passed, 126 tests.
- `python3 -m compileall -q apps/flange_qc_v2 tests/flange_qc_v2` passed.
- `python3 scripts/product-ci/run_product_checks.py` passed.
- `python3 -m unittest discover -s tests -v` passed, 196 tests.
- `git diff --check` passed.

## Residual Risks

- Browser verification used a temporary stdlib HTTP server because `uvicorn` is
  not installed in the current Python environment. The temp server does not
  implement WebSocket upgrade, so one browser console error was expected for the
  `/ws/inspection` handshake; the real ASGI WebSocket path remains covered by
  `tests/flange_qc_v2/test_hmi_stream.py`.
- Synthetic replay observation metadata is structural evidence only and does not
  prove real dataset quality, model performance, model promotion, or live camera
  behavior.
- Product specs, QC/SOP tolerances, model approval/promotion, live camera
  readiness, and production release remain human-gated.

## Rollback

Revert the FQV2-031 PR to remove the HMI detector observations detail panel.
Existing replay snapshots, artifact intake endpoint, shadow detector status
endpoint, no-camera replay, and detector adapter behavior remain valid. No
migration, model rollback, camera rollback, dataset rollback, or deploy rollback
is required.

## Memory Candidate

- memory_type: implementation_lesson
- content: Flange QC v2 HMI now renders review-only detector observation details
  from `payload.observations`, including label, confidence, bbox, model ref, and
  evidence ref, while preserving safe empty state and shadow-only authority.
- source_ref: https://github.com/namlogan/MIL/issues/119
- why reusable: Future operator-facing model review features should render
  validated observation evidence without changing backend decision authority,
  inference, camera access, or production PASS/NG behavior.
- scope: project:flange_qc_v2
- suggested status: candidate
