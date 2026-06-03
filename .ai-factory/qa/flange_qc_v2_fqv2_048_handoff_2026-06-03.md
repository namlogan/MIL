# FQV2-048 QA Handoff: Boundary-Calibrated Shadow Measurements

## Scope

- Branch: `agent/153-boundary-calibrated-measurements`
- Task: FQV2-048
- Issue: https://github.com/namlogan/MIL/issues/153

## Files Changed

- `apps/flange_qc_v2/calibration.py`
- `apps/flange_qc_v2/geometry.py`
- `apps/flange_qc_v2/replay.py`
- `tests/flange_qc_v2/test_calibration.py`
- `tests/flange_qc_v2/test_geometry.py`
- `tests/flange_qc_v2/test_replay.py`
- `configs/flange_qc_v2/camera_calibration.synthetic.example.json`
- `samples/replay/flange_qc_v2/phase2_synthetic_boundary.json`
- `docs/project/flange_qc_v2/DATA_MODEL.md`
- `docs/project/flange_qc_v2/TEST_STRATEGY.md`
- `docs/project/flange_qc_v2/USER_FLOWS.md`
- `.ai-factory/gates/flange_qc_v2_fqv2_048_dor.json`
- `.ai-factory/qa/flange_qc_v2_fqv2_048_handoff_2026-06-03.md`

## Summary

- Added optional calibration geometry metadata:
  `source_units=pixel`, `inch_per_pixel`, and
  `method=top_down_boundary_corners_shadow_v1`.
- Added `resolve_geometry_from_boundary(...)` to derive 3 length points, 3 width
  points, and 2 diagonals from sanitized four-corner boundary metadata.
- Added measurement source/evidence fields to geometry payloads:
  `measurement_source=boundary_corners_calibrated_shadow` plus boundary source,
  calibration method, calibration source, scale, sample fractions, and corner
  order.
- Extended replay frames so sanitized `boundary` input can replace precomputed
  `measurements`; replay resolves all frames through calibration before HMI or
  decision output.
- Added a checked-in synthetic boundary replay fixture.
- Confirmed derived boundary measurements flow into the existing product
  tolerance logic while keeping `production_authority=false`.

## TDD Evidence

- RED:
  `python3 -m unittest tests.flange_qc_v2.test_calibration tests.flange_qc_v2.test_geometry tests.flange_qc_v2.test_replay -v`
  failed because `CalibrationConfig.geometry`,
  `resolve_geometry_from_boundary`, and boundary-only replay frames were missing.
- GREEN:
  the same focused suite passed after adding calibration geometry metadata,
  boundary measurement resolution, and replay boundary support.

## Checks

- `python3 -m json.tool .ai-factory/gates/flange_qc_v2_fqv2_048_dor.json >/dev/null`
- `git diff --check`
- `python3 -m unittest tests.flange_qc_v2.test_calibration tests.flange_qc_v2.test_geometry tests.flange_qc_v2.test_replay tests.flange_qc_v2.test_decision_engine tests.flange_qc_v2.test_hmi_stream -v` passed, 30 tests.
- `python3 -m unittest tests.flange_qc_v2.test_geometry tests.flange_qc_v2.test_replay tests.flange_qc_v2.test_hmi_stream -v` passed, 17 tests after replay polish.
- `python3 -m unittest discover -s tests/flange_qc_v2 -v` passed, 164 tests.
- `python3 scripts/product-ci/run_product_checks.py` passed.

## Replay And HTTP Evidence

Direct boundary replay smoke for
`samples/replay/flange_qc_v2/phase2_synthetic_boundary.json` returned:

```json
{
  "decision": "BLOCKED",
  "diagonals": [83.852549, 83.852549],
  "length_points": [75.0, 75.0, 75.0],
  "measurement_source": "boundary_corners_calibrated_shadow",
  "production_authority": false,
  "replay_id": "fqv2-phase2-synthetic-boundary-001",
  "width_points": [37.5, 37.5, 37.5]
}
```

The local preview was restarted on:

```text
http://127.0.0.1:8766/hmi
```

HTTP smoke for `/inspection/replay` returned HTTP 200, existing default replay
measurements, `decision=BLOCKED`, and all phase `production_authority=false`.
`/hmi` returned HTTP 200 and still includes the measurement panel.

## Restricted Change Check

No raw media, raw datasets, customer data, model weights, model binaries,
notebooks, model deserialization, inference runtime, camera SDK, live camera
capture, GPU use, secrets, credentials, destructive migrations, production
deploy/release, product spec approval, QC/SOP tolerance approval, model
promotion approval, production PASS/NG authority, production auto-reject
behavior, or Windmill credential/tunnel/runtime change is included.

## Residual Risks

- QC/SOP still must approve the real production measurement method, including
  whether final diagonal deviation uses corrected top boundary or raw detected
  corners.
- Product specs and tolerances remain draft until QC/domain owner approval.
- The synthetic calibration scale is bootstrap evidence only; live camera
  calibration and hardware validation remain blocked until hardware arrives and
  the owner approves the gate.
- Runtime daily status may still report tmux relay/tunnel and Windmill CLI
  attention; this task intentionally does not touch secret-adjacent runtime
  credentials.

## Rollback

Revert the FQV2-048 PR to restore replay to precomputed measurements only.
Existing product tolerance, decision engine, HMI, artifact readiness, detector
bridge, and product CI behavior remain valid.

## Memory Candidate

- memory_type: task_lesson
- content: Boundary/corners measurement derivation should stay shadow-only:
  sanitize four corners, use explicit calibration scale, emit measurement
  evidence, and feed existing product tolerance logic while production authority
  remains false.
- source_ref: https://github.com/namlogan/MIL/issues/153
- why reusable: Future live-camera measurement work can reuse the contract
  shape without treating bootstrap scale or SOP interpretation as approved.
- scope: flange_qc_v2
- suggested status: candidate
