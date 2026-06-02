# FQV2-028 QA Handoff: Artifact Intake Readiness in ASGI/HMI

## Source

- GitHub issue: https://github.com/namlogan/MIL/issues/113
- Branch: `agent/113-artifact-intake-readiness-hmi`
- Task: FQV2-028

## Files Changed

- `apps/flange_qc_v2/asgi.py`
- `apps/flange_qc_v2/static/hmi.html`
- `tests/flange_qc_v2/test_artifact_intake.py`
- `tests/flange_qc_v2/test_hmi_screen.py`
- `docs/project/flange_qc_v2/ARTIFACT_INTAKE.md`
- `docs/project/flange_qc_v2/DATA_MODEL.md`
- `docs/project/flange_qc_v2/USER_FLOWS.md`
- `docs/project/flange_qc_v2/TEST_STRATEGY.md`
- `.ai-factory/gates/flange_qc_v2_fqv2_028_dor.json`
- `.ai-factory/qa/flange_qc_v2_fqv2_028_handoff_2026-06-02.md`
- `.ai-factory/qa/flange_qc_v2_fqv2_028_hmi.png`
- `.ai-factory/qa/flange_qc_v2_fqv2_028_hmi_snapshot.md`

## Rules Applied

- One task per branch.
- GitHub issue is source of truth for requirement, acceptance criteria, and
  allowed paths.
- TDD RED/GREEN checkpoints were used before implementation.
- Endpoint reads only `FLANGE_QC_V2_ARTIFACT_INTAKE_DIR`; no request-supplied
  arbitrary filesystem path is accepted.
- No raw media, raw datasets, customer data, notebooks, model weights, model
  binaries, model deserialization, model inference, camera SDK import, live
  camera capture, GPU use, secrets, destructive migration, deployment, product
  spec approval, QC/SOP tolerance approval, model promotion, production PASS/NG
  authority, or production auto-reject behavior is introduced.

## Implementation Notes

- Added `GET /artifact-intake/status` to the ASGI app.
- Missing `FLANGE_QC_V2_ARTIFACT_INTAKE_DIR` returns a safe unconfigured state.
- Configured env var delegates to the existing `validate_artifact_intake()`
  contract and adds `configured=true`, `production_authority=false`, and
  approval blockers.
- HMI now renders an artifact readiness panel with configured state, shadow model
  readiness, live camera readiness, next task, warnings/errors, and artifact
  names/summaries.
- HMI artifact summaries show metadata contract/status only and do not display
  raw artifact files, model weights, or camera credentials.

## Tests Run

- RED: `python3 -m unittest tests.flange_qc_v2.test_artifact_intake -v` failed
  because `/artifact-intake/status` returned 404.
- RED: `python3 -m unittest tests.flange_qc_v2.test_hmi_screen -v` failed
  because the HMI did not render or bind the artifact readiness panel.
- GREEN: `python3 -m unittest tests.flange_qc_v2.test_artifact_intake -v`
  passed, 9 tests.
- GREEN: `python3 -m unittest tests.flange_qc_v2.test_hmi_screen -v` passed,
  5 tests.
- `python3 -m unittest tests.flange_qc_v2.test_hmi_stream -v` passed, 4 tests.
- Browser evidence: `http://127.0.0.1:8765/hmi` rendered artifact intake status
  as configured, shadow model ready, live camera not ready, next task
  `shadow_model_integration`, and four valid metadata artifacts from the
  template intake bundle.
- Browser snapshot artifact:
  `.ai-factory/qa/flange_qc_v2_fqv2_028_hmi_snapshot.md`.
- Browser screenshot artifact:
  `.ai-factory/qa/flange_qc_v2_fqv2_028_hmi.png`.
- `python3 -m json.tool .ai-factory/gates/flange_qc_v2_fqv2_028_dor.json`
  passed.
- `git diff --check` passed.
- `python3 -m unittest discover -s tests/flange_qc_v2 -v` passed, 119 tests.
- `python3 -m compileall -q apps/flange_qc_v2 tests/flange_qc_v2` passed.
- `python3 scripts/product-ci/run_product_checks.py` passed.
- `python3 -m unittest discover -s tests -v` passed, 196 tests.

## Residual Risks

- Browser verification used a local stdlib test server because `uvicorn` is not
  installed in the current Python environment and the Browser plugin had no
  available `iab` backend. Playwright fallback verified the rendered local HMI.
- Template artifacts are sanitized metadata only; they do not prove real
  dataset quality, model performance, model promotion, or live camera behavior.
- Product specs, QC/SOP tolerances, model approval/promotion, live camera
  readiness, and production release remain human-gated.

## Rollback

Revert the FQV2-028 PR to remove `/artifact-intake/status` and the HMI readiness
panel. Existing CLI artifact validator, docs, templates, and HMI replay/feedback
behavior remain valid. No migration, model rollback, camera rollback, dataset
rollback, or deploy rollback is required.

## Memory Candidate

- memory_type: implementation_lesson
- content: Flange QC v2 exposes artifact intake readiness through a safe env-var
  bound endpoint and HMI panel, using existing metadata validators without
  request-supplied paths or production authority.
- source_ref: https://github.com/namlogan/MIL/issues/113
- why reusable: Future shadow model integration can use
  `/artifact-intake/status` to confirm metadata readiness before connecting a
  model reference to detector boundaries.
- scope: project:flange_qc_v2
- suggested status: candidate
