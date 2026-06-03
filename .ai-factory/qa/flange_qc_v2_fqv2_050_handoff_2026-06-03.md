# FQV2-050 QA Handoff: Measurement Source Evidence In HMI

## Scope

- Branch: `agent/157-measurement-source-evidence-hmi`
- Task: FQV2-050
- Issue: https://github.com/namlogan/MIL/issues/157

## Files Changed

- `apps/flange_qc_v2/domain.py`
- `apps/flange_qc_v2/hmi_stream.py`
- `apps/flange_qc_v2/static/hmi.html`
- `contracts/flange_qc_v2/websocket/inspection_snapshot.schema.json`
- `tests/flange_qc_v2/test_domain_contracts.py`
- `tests/flange_qc_v2/test_hmi_stream.py`
- `tests/flange_qc_v2/test_hmi_screen.py`
- `docs/project/flange_qc_v2/DATA_MODEL.md`
- `docs/project/flange_qc_v2/TEST_STRATEGY.md`
- `docs/project/flange_qc_v2/USER_FLOWS.md`
- `.ai-factory/gates/flange_qc_v2_fqv2_050_dor.json`
- `.ai-factory/qa/flange_qc_v2_fqv2_050_handoff_2026-06-03.md`

## Summary

- Extended `InspectionMeasurements` with non-authoritative
  `measurement_source` and sanitized `measurement_evidence`.
- Preserved replay frame provenance when building HMI inspection snapshots.
- Updated the WebSocket inspection snapshot schema to document measurement
  source/evidence.
- Added HMI Frame Source rows for measurement source and compact evidence.
- Updated docs/tests so boundary-derived measurements are visible as shadow
  evidence without approving live calibration, QC/SOP tolerances, or production
  PASS/NG authority.

## TDD Evidence

- RED:
  `python3 -m unittest tests.flange_qc_v2.test_domain_contracts tests.flange_qc_v2.test_hmi_stream tests.flange_qc_v2.test_hmi_screen -v`
  failed because `InspectionMeasurements` did not accept
  `measurement_source`, snapshot payloads did not include source/evidence,
  schema did not require those fields, and HMI lacked
  `measurement-source` / `measurement-evidence`.
- GREEN:
  the same focused suite passed after adding domain/schema fields, replay
  snapshot provenance preservation, and HMI rendering.

## Checks

- `python3 -m json.tool .ai-factory/gates/flange_qc_v2_fqv2_050_dor.json` passed.
- `git diff --check` passed.
- `python3 -m unittest tests.flange_qc_v2.test_domain_contracts tests.flange_qc_v2.test_hmi_stream tests.flange_qc_v2.test_hmi_screen -v` passed, 24 tests.
- `python3 -m unittest discover -s tests/flange_qc_v2 -v` passed, 167 tests.
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
  "boundary_source": "synthetic_boundary_corners",
  "calibration_method": "top_down_boundary_corners_shadow_v1",
  "decision": "BLOCKED",
  "diagonals": [83.852549, 83.852549],
  "inspection_id": "fqv2-phase2-synthetic-boundary-001",
  "length_points": [75.0, 75.0, 75.0],
  "measurement_source": "boundary_corners_calibrated_shadow",
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
  "measurementEvidence": "Evidence: boundary_source=synthetic_boundary_corners; calibration_method=top_down_boundary_corners_shadow_v1; calibration_source_ref=synthetic bootstrap fixture; corner_order=top_left|top_right|bottom_right|bottom_left",
  "measurementScopeStatus": "OK",
  "measurementSource": "boundary_corners_calibrated_shadow",
  "phaseProductionAuthority": "false"
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
- Boundary/corners measurement provenance is sanitized replay evidence only;
  live camera calibration and hardware validation remain future gates.
- Runtime daily status may still report tmux relay/tunnel or Windmill attention;
  this task intentionally does not touch secret-adjacent runtime credentials.

## Rollback

Revert the FQV2-050 PR to remove measurement provenance display from
snapshots/HMI. Existing replay, boundary-derived measurements, HMI signal
layout, product tolerance, and product CI behavior remain valid.

## Memory Candidate

- memory_type: task_lesson
- content: Inspection snapshots should preserve sanitized measurement
  provenance (`measurement_source` and `measurement_evidence`) so HMI, QA, and
  audit evidence agree while production authority remains false.
- source_ref: https://github.com/namlogan/MIL/issues/157
- why reusable: Future live-camera and MLOps artifact work can reuse this
  contract to compare provided, boundary-derived, and later camera-derived
  measurements without granting production approval.
- scope: flange_qc_v2
- suggested status: candidate
