# FQV2-049 QA Handoff: Env-Configured Replay Sources

## Scope

- Branch: `agent/155-env-configured-replay-sources`
- Task: FQV2-049
- Issue: https://github.com/namlogan/MIL/issues/155

## Files Changed

- `apps/flange_qc_v2/hmi_stream.py`
- `tests/flange_qc_v2/test_hmi_stream.py`
- `docs/project/flange_qc_v2/DATA_MODEL.md`
- `docs/project/flange_qc_v2/TEST_STRATEGY.md`
- `docs/project/flange_qc_v2/USER_FLOWS.md`
- `.ai-factory/gates/flange_qc_v2_fqv2_049_dor.json`
- `.ai-factory/qa/flange_qc_v2_fqv2_049_handoff_2026-06-03.md`

## Summary

- Added env-only replay source configuration for `/inspection/replay`:
  `FLANGE_QC_V2_REPLAY_MANIFEST_PATH`,
  `FLANGE_QC_V2_PRODUCT_SPECS_PATH`, and
  `FLANGE_QC_V2_CALIBRATION_PATH`.
- Preserved the existing checked-in bootstrap fixtures as defaults when those
  env vars are unset.
- Verified request-supplied path query strings are ignored by the replay HTTP
  endpoint.
- Verified the boundary-derived measurement fixture now flows through
  `/inspection/replay` and into the HMI snapshot without adding live camera,
  raw media, model execution, or production authority.

## TDD Evidence

- RED:
  `python3 -m unittest tests.flange_qc_v2.test_hmi_stream -v` failed because
  `/inspection/replay` still returned `fqv2-phase2-synthetic-001` instead of
  the env-configured boundary replay id.
- GREEN:
  the same focused suite passed after `build_replay_inspection_snapshot()`
  resolved replay, product spec, and calibration paths from env-only
  configuration.

## Checks

- `python3 -m json.tool .ai-factory/gates/flange_qc_v2_fqv2_049_dor.json` passed.
- `git diff --check` passed.
- `python3 -m unittest tests.flange_qc_v2.test_hmi_stream tests.flange_qc_v2.test_hmi_screen tests.flange_qc_v2.test_replay -v` passed, 22 tests.
- `python3 -m unittest discover -s tests/flange_qc_v2 -v` passed, 166 tests.
- `python3 scripts/product-ci/run_product_checks.py` passed.

## HTTP And Browser Evidence

The local preview was restarted on:

```text
http://127.0.0.1:8766/hmi
```

with:

```text
FLANGE_QC_V2_ARTIFACT_INTAKE_DIR=templates/flange_qc_v2/artifact_intake
FLANGE_QC_V2_REPLAY_MANIFEST_PATH=samples/replay/flange_qc_v2/phase2_synthetic_boundary.json
FLANGE_QC_V2_PRODUCT_SPECS_PATH=configs/flange_qc_v2/product_specs.bootstrap.json
FLANGE_QC_V2_CALIBRATION_PATH=configs/flange_qc_v2/camera_calibration.synthetic.example.json
```

HTTP smoke for `/inspection/replay?manifest_path=/tmp/not-allowed.json`
returned:

```json
{
  "decision": "BLOCKED",
  "diagonals": [83.852549, 83.852549],
  "hmi_status": 200,
  "inspection_id": "fqv2-phase2-synthetic-boundary-001",
  "length_points": [75.0, 75.0, 75.0],
  "phase_production_authority": [false, false, false, false],
  "replay_status": 200,
  "width_points": [37.5, 37.5, 37.5]
}
```

Browser HMI verification at `http://127.0.0.1:8766/hmi` showed:

```json
{
  "decision": "BLOCKED",
  "inspectionId": "fqv2-phase2-synthetic-boundary-001",
  "measurementScopeDetail": "L 75.00-75.00 / W 37.50-37.50 inch",
  "measurementScopeStatus": "OK",
  "operatorState": "review",
  "phase": "FINAL",
  "stitchScopeState": "review"
}
```

## Restricted Change Check

No raw media, raw datasets, customer/factory data, notebooks, model weights,
model binaries, model deserialization, inference runtime, camera SDK, live
camera capture, GPU use, secrets, credentials, destructive migrations,
production deploy/release, product spec approval, QC/SOP tolerance approval,
model promotion approval, production PASS/NG authority, production auto-reject
behavior, request-supplied file paths, or Windmill credential/tunnel/runtime
change is included.

## Residual Risks

- Product specs and tolerances remain draft until QC/domain owner approval.
- QC/SOP tolerance approval is still required before production PASS/NG
  authority.
- The boundary replay fixture is sanitized shadow evidence only; live camera
  hardware, camera calibration, and model artifacts remain future gates.
- Runtime daily status may still report tmux relay/tunnel or Windmill attention;
  this task intentionally does not touch secret-adjacent runtime credentials.

## Rollback

Revert the FQV2-049 PR to restore `/inspection/replay` to default checked-in
fixtures only. Existing replay, HMI, boundary measurement, product tolerance,
and product CI behavior remain valid.

## Memory Candidate

- memory_type: task_lesson
- content: HMI replay fixture selection should use env-only paths for replay,
  product specs, and calibration so sanitized boundary-derived measurement
  artifacts can be exercised without request path injection.
- source_ref: https://github.com/namlogan/MIL/issues/155
- why reusable: Future app-code and MLOps artifact handoff tasks can connect
  sanitized fixtures through normal endpoints while keeping production
  authority false.
- scope: flange_qc_v2
- suggested status: candidate
