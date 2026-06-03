# FQV2-041 QA Handoff: HMI Artifact Readiness Panel

## Source

- GitHub issue: https://github.com/namlogan/MIL/issues/139
- Branch: `agent/139-hmi-artifact-readiness-panel`
- Task: FQV2-041

## Files Changed

- `apps/flange_qc_v2/static/hmi.html`
- `tests/flange_qc_v2/test_hmi_screen.py`
- `docs/project/flange_qc_v2/USER_FLOWS.md`
- `docs/project/flange_qc_v2/DATA_MODEL.md`
- `docs/project/flange_qc_v2/TEST_STRATEGY.md`
- `.ai-factory/gates/flange_qc_v2_fqv2_041_dor.json`
- `.ai-factory/qa/flange_qc_v2_fqv2_041_handoff_2026-06-03.md`

## Rules Applied

- One task per branch.
- GitHub issue is source of truth for requirement, acceptance criteria, and
  allowed paths.
- TDD RED/GREEN checkpoints were used before implementation.
- HMI fetches the existing `/artifact-readiness/status` endpoint only; no
  backend route behavior was changed.
- The artifact readiness panel is outside the primary QC tablet viewport and
  does not change green/red/amber QC decision semantics.
- The panel renders metadata-only readiness lanes and never grants production
  authority.
- No raw media/data, feedback rows, model weights/binaries/inference, live
  camera, camera SDK, secrets, destructive migration, product spec approval,
  QC/SOP tolerance approval, model promotion, production deploy/release, or
  production PASS/NG authority is introduced.

## Implementation Notes

- Added a compact HMI artifact readiness support panel.
- Added HMI bindings for:
  - artifact readiness status
  - shadow model readiness
  - live camera readiness
  - QC feedback labeling readiness
  - production release blocker
  - recommended next actions
- Missing or fetch-failed readiness data renders a blocked/attention state.
- Existing QC tablet viewport, artifact intake panel, detector bridge panel,
  detector observations panel, and feedback controls remain in place.

## Tests Run

- RED: `python3 -m unittest tests.flange_qc_v2.test_hmi_screen -v` failed
  before implementation because the HMI did not contain
  `artifact-readiness-status`.
- GREEN: `python3 -m unittest tests.flange_qc_v2.test_hmi_screen -v` passed,
  10 tests.
- `python3 -m unittest tests.flange_qc_v2.test_artifact_readiness -v` passed,
  9 tests.
- `python3 -m json.tool .ai-factory/gates/flange_qc_v2_fqv2_041_dor.json >/dev/null`
  passed.
- `git diff --check` passed.
- `python3 -m compileall -q apps/flange_qc_v2 tests/flange_qc_v2 scripts/flange_qc_v2`
  passed.
- `python3 -m unittest discover -s tests/flange_qc_v2 -v` passed, 151 tests.
- `python3 scripts/product-ci/run_product_checks.py` passed.
- `python3 -m unittest discover -s tests -v` passed, 196 tests.

## Browser Smoke

- Previewed the current branch at `http://127.0.0.1:8766/hmi` because port
  `8765` was already occupied by a previous temporary preview process.
- Verified the first viewport keeps the signal-first QC layout:
  - operator banner: `CHECK`
  - measurement scope: `OK`
  - stitch scope: `CHECK`
  - suspected-region overlay visible
- Verified artifact readiness support panel:
  - status: `artifact readiness metadata loaded`
  - state: `ok`
  - shadow model lane: `ready_for_shadow_integration`
  - live camera lane: blocked
  - QC feedback lane: blocked
  - production release lane: blocked
  - recommended actions: `open_shadow_model_integration_issue`,
    `schedule_camera_hardware_readiness`, `collect_more_qc_feedback`,
    `keep_production_release_blocked`
- Verified the readiness panel is below the primary QC tablet viewport and does
  not become the main QC pass/fail focus.

## Residual Risks

- The panel is a support surface for engineering/operator readiness, not a
  production release, model promotion, or QC approval gate.
- Live camera use still requires hardware readiness and credential/runtime setup
  outside this task.
- This does not approve labels, model promotion, live camera integration,
  product specs, QC/SOP tolerances, production release, or production PASS/NG
  authority.

## Rollback

Revert the FQV2-041 PR to remove the HMI artifact readiness panel, tests, docs,
and gate evidence. Existing HMI QC viewport, artifact readiness endpoint,
artifact intake status, detector bridge, feedback flow, and product CI behavior
remain valid.
