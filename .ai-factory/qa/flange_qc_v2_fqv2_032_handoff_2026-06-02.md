# FQV2-032 QA Handoff: HMI Detector Shadow Status

## Source

- GitHub issue: https://github.com/namlogan/MIL/issues/121
- Branch: `agent/121-hmi-detector-shadow-status`
- Task: FQV2-032

## Files Changed

- `apps/flange_qc_v2/static/hmi.html`
- `tests/flange_qc_v2/test_hmi_screen.py`
- `docs/project/flange_qc_v2/USER_FLOWS.md`
- `docs/project/flange_qc_v2/DATA_MODEL.md`
- `docs/project/flange_qc_v2/TEST_STRATEGY.md`
- `.ai-factory/gates/flange_qc_v2_fqv2_032_dor.json`
- `.ai-factory/qa/flange_qc_v2_fqv2_032_handoff_2026-06-02.md`
- `.ai-factory/qa/flange_qc_v2_fqv2_032_hmi.png`
- `.ai-factory/qa/flange_qc_v2_fqv2_032_hmi_snapshot.md`

## Rules Applied

- One task per branch.
- GitHub issue is source of truth for requirement, acceptance criteria, and
  allowed paths.
- TDD RED/GREEN checkpoints were used before implementation.
- HMI only reads the existing `/detector/shadow/status` metadata endpoint.
- No backend detector/replay contract changes were introduced.
- No request-supplied arbitrary filesystem path, raw media, raw datasets,
  customer data, notebooks, model weights, model binaries, model deserialization,
  model inference, camera SDK import, live camera capture, GPU use, secrets,
  destructive migration, deployment, product spec approval, QC/SOP tolerance
  approval, model promotion, production PASS/NG authority, or production
  auto-reject behavior is introduced.

## Implementation Notes

- Added a `Detector Bridge` / `Detector Metadata` HMI panel.
- Added `fetchDetectorShadowStatus()` against `/detector/shadow/status`.
- Added `renderDetectorShadowStatus()` with safe unconfigured/error fallback.
- Ready metadata shows ready state, adapter, model reference, labels, approval
  status, and authority blockers.
- Existing artifact intake, detector observation, replay, and feedback panels
  remain unchanged in authority behavior.

## Tests Run

- RED: `python3 -m unittest tests.flange_qc_v2.test_hmi_screen -v` failed
  because HMI lacked the detector shadow status panel and renderer.
- GREEN: `python3 -m unittest tests.flange_qc_v2.test_hmi_screen -v` passed,
  7 tests.
- Browser evidence on `http://127.0.0.1:8765/hmi` with
  `FLANGE_QC_V2_ARTIFACT_INTAKE_DIR=templates/flange_qc_v2/artifact_intake`
  showed detector bridge status `ready: manifest-detector`, ready `true`,
  model reference `registry://flange-qc-v2/detector/punch-mark/2026-06-02`,
  labels `punch_mark, corner_mark`, approval status `candidate`, and authority
  blockers `MODEL_APPROVAL_REQUIRED, PRODUCTION_APPROVAL_REQUIRED`.
- Browser snapshot artifact:
  `.ai-factory/qa/flange_qc_v2_fqv2_032_hmi_snapshot.md`.
- Browser screenshot artifact:
  `.ai-factory/qa/flange_qc_v2_fqv2_032_hmi.png`.
- `python3 -m json.tool .ai-factory/gates/flange_qc_v2_fqv2_032_dor.json`
  passed.
- `python3 -m unittest tests.flange_qc_v2.test_hmi_stream tests.flange_qc_v2.test_detector_adapter -v`
  passed, 17 tests.
- `python3 -m unittest discover -s tests/flange_qc_v2 -v` passed, 127 tests.
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
- Detector bridge metadata is structural evidence only and does not prove real
  dataset quality, model performance, model promotion, or live camera behavior.
- Product specs, QC/SOP tolerances, model approval/promotion, live camera
  readiness, and production release remain human-gated.

## Rollback

Revert the FQV2-032 PR to remove the HMI detector bridge status panel. Existing
artifact intake, shadow detector status endpoint, detector observation panel,
replay/HMI snapshots, and feedback behavior remain valid. No migration, model
rollback, camera rollback, dataset rollback, or deploy rollback is required.

## Memory Candidate

- memory_type: implementation_lesson
- content: Flange QC v2 HMI now surfaces `/detector/shadow/status` metadata as
  detector bridge readiness, including adapter, model reference, labels,
  approval status, and authority blockers, while preserving shadow-only
  authority.
- source_ref: https://github.com/namlogan/MIL/issues/121
- why reusable: Future operator-facing MLOps readiness features should expose
  metadata status without changing backend decision authority, inference,
  camera access, or production PASS/NG behavior.
- scope: project:flange_qc_v2
- suggested status: candidate
