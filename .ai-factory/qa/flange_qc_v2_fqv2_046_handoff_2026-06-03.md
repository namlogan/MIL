# FQV2-046 QA Handoff: Detector Shadow Next Action Alignment

## Scope

- Branch: `agent/149-detector-shadow-observation-next-action`
- Task: FQV2-046
- Issue: https://github.com/namlogan/MIL/issues/149

## Files Changed

- `apps/flange_qc_v2/detector.py`
- `tests/flange_qc_v2/test_detector_adapter.py`
- `docs/project/flange_qc_v2/MLOPS_BOUNDARY.md`
- `docs/project/flange_qc_v2/USER_FLOWS.md`
- `docs/project/flange_qc_v2/DATA_MODEL.md`
- `docs/project/flange_qc_v2/TEST_STRATEGY.md`
- `.ai-factory/gates/flange_qc_v2_fqv2_046_dor.json`
- `.ai-factory/qa/flange_qc_v2_fqv2_046_handoff_2026-06-03.md`

## Summary

- Aligned ready `/detector/shadow/status` with artifact intake and artifact
  readiness by returning `state=ready_for_shadow_observation_review`.
- Added top-level `next_task=shadow_observation_review` to ready detector shadow
  status.
- Changed ready detector `next_issue.recommended_task` to
  `shadow_observation_review`.
- Added detector `next_issue.recommended_next_actions` containing
  `submit_shadow_observation_payload` and `collect_more_qc_feedback`.
- Preserved safe unconfigured detector status, review-only observation dry-runs,
  and `production_authority=false`.
- Updated MLOps boundary, user flow, data model, and test strategy docs so the
  detector bridge uses the same next action as the current readiness lane.

## TDD Evidence

- RED:
  `python3 -m unittest tests.flange_qc_v2.test_detector_adapter.ShadowDetectorBridgeTests.test_builds_shadow_detector_metadata_from_ready_artifact_intake tests.flange_qc_v2.test_detector_adapter.ShadowDetectorBridgeTests.test_shadow_detector_status_endpoint_uses_env_only -v`
  failed because ready detector shadow status did not expose `state`,
  `next_task`, or the new review action.
- GREEN:
  the same focused tests passed after updating `apps/flange_qc_v2/detector.py`.

## Checks

- `python3 -m json.tool .ai-factory/gates/flange_qc_v2_fqv2_046_dor.json >/dev/null`
- `git diff --check`
- `python3 -m unittest tests.flange_qc_v2.test_detector_adapter -v` passed, 21 tests.
- `python3 -m unittest tests.flange_qc_v2.test_artifact_intake -v` passed, 9 tests.
- `python3 -m unittest tests.flange_qc_v2.test_artifact_readiness -v` passed, 9 tests.
- `python3 -m unittest tests.flange_qc_v2.test_hmi_screen -v` passed, 10 tests.
- `python3 -m compileall -q apps/flange_qc_v2 tests/flange_qc_v2 scripts/flange_qc_v2` passed.
- `python3 -m unittest discover -s tests/flange_qc_v2 -v` passed.
- `python3 scripts/product-ci/run_product_checks.py` passed.
- `python3 -m unittest discover -s tests -v` passed, 196 tests.

## HTTP Evidence

The local HMI preview was restarted on:

```text
http://127.0.0.1:8766/hmi
```

HTTP smoke for `/detector/shadow/status` returned:

```json
{
  "next_task": "shadow_observation_review",
  "production_authority": false,
  "ready": true,
  "recommended_next_actions": [
    "submit_shadow_observation_payload",
    "collect_more_qc_feedback"
  ],
  "recommended_task": "shadow_observation_review",
  "state": "ready_for_shadow_observation_review"
}
```

HTTP smoke for `/artifact-intake/status` returned
`recommended_task=shadow_observation_review`,
`recommended_next_actions` containing `submit_shadow_observation_payload`, and
`production_authority=false`.

HTTP smoke for `/artifact-readiness/status` returned shadow lane
`state=ready_for_shadow_observation_review`,
`recommended_task=shadow_observation_review`, aggregate
`recommended_next_actions` containing `submit_shadow_observation_payload`, and
`production_authority=false`.

The HMI HTML route returned HTTP 200. The preview adapter is HTTP-only, so live
WebSocket streaming remains outside this smoke and is covered by existing ASGI
and HMI tests.

## Restricted Change Check

No raw media, raw datasets, customer data, model weights, model binaries,
notebooks, model deserialization, inference runtime, camera SDK, live camera
capture, GPU use, secrets, credentials, destructive migrations, production
deploy/release, product spec approval, QC/SOP tolerance approval, model
promotion approval, production PASS/NG authority, production auto-reject
behavior, or Windmill credential/tunnel/runtime change is included.

## Residual Risks

- Real model quality, dataset quality, label policy approval, and model
  promotion still require external MLOps/QC evidence and human gates.
- Live camera remains blocked until hardware arrives and camera readiness is
  explicitly approved.
- Runtime daily status may still report tmux relay/tunnel and Windmill CLI
  attention; this task intentionally does not touch secret-adjacent runtime
  credentials.

## Rollback

Revert the FQV2-046 PR to restore the previous detector shadow status next
action. Existing detector status, detector observations, artifact
intake/readiness, HMI, feedback, and product CI behavior remain valid.

## Memory Candidate

- memory_type: task_lesson
- content: Detector shadow status should mirror artifact intake/readiness next
  actions after the shadow detector bridge exists, while keeping production
  authority false and observation submission review-only.
- source_ref: https://github.com/namlogan/MIL/issues/149
- why reusable: Future readiness/status endpoints should keep machine-facing
  readiness and operator-facing next actions aligned across the app.
- scope: flange_qc_v2
- suggested status: candidate
