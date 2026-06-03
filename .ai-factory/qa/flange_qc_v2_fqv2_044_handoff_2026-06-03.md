# FQV2-044 QA Handoff: Artifact Readiness Next Actions

## Scope

- Branch: `agent/145-artifact-readiness-shadow-observation-next-actions`
- Task: FQV2-044
- Issue: https://github.com/namlogan/MIL/issues/145

## Files Changed

- `apps/flange_qc_v2/artifact_readiness.py`
- `tests/flange_qc_v2/test_artifact_readiness.py`
- `docs/project/flange_qc_v2/USER_FLOWS.md`
- `docs/project/flange_qc_v2/DATA_MODEL.md`
- `docs/project/flange_qc_v2/DATASET_MLOPS_HANDOFF.md`
- `docs/project/flange_qc_v2/TEST_STRATEGY.md`
- `.ai-factory/gates/flange_qc_v2_fqv2_044_dor.json`
- `.ai-factory/qa/flange_qc_v2_fqv2_044_handoff_2026-06-03.md`

## Summary

- Advanced the artifact readiness shadow lane from the stale
  `ready_for_shadow_integration` state to
  `ready_for_shadow_observation_review`.
- Changed the ready shadow lane recommended task from
  `shadow_model_integration` to `shadow_observation_review`.
- Changed aggregate recommended next actions from
  `open_shadow_model_integration_issue` to
  `submit_shadow_observation_payload`.
- Preserved live camera, model promotion, production release, QC/SOP tolerance,
  product spec, and production PASS/NG authority blockers.
- Updated docs so the app readiness chain points to sanitized shadow
  observation payload review after the shadow detector bridge and request
  contract exist.

## TDD Evidence

- RED:
  `python3 -m unittest tests.flange_qc_v2.test_artifact_readiness.ArtifactReadinessReportTests.test_report_advances_shadow_lane_to_observation_review_without_production_authority -v`
  failed because the report still returned `ready_for_shadow_integration`.
- GREEN:
  the same test passed after updating `artifact_readiness.py`.

## Checks

- `python3 -m json.tool .ai-factory/gates/flange_qc_v2_fqv2_044_dor.json >/dev/null`
- `git diff --check`
- `python3 -m unittest tests.flange_qc_v2.test_artifact_readiness -v` passed, 9 tests.
- `python3 -m unittest tests.flange_qc_v2.test_hmi_screen -v` passed, 10 tests.
- `python3 -m unittest tests.flange_qc_v2.test_detector_adapter -v` passed, 21 tests.
- `python3 -m compileall -q apps/flange_qc_v2 tests/flange_qc_v2 scripts/flange_qc_v2` passed.
- `python3 -m unittest discover -s tests/flange_qc_v2 -v` passed.
- `python3 scripts/product-ci/run_product_checks.py` passed.
- `python3 -m unittest discover -s tests -v` passed, 196 tests.

## HTTP And Browser Evidence

The local HMI preview was restarted on:

```text
http://127.0.0.1:8766/hmi
```

HTTP smoke for `/artifact-readiness/status` returned:

```json
{
  "shadow_state": "ready_for_shadow_observation_review",
  "shadow_task": "shadow_observation_review",
  "actions": [
    "submit_shadow_observation_payload",
    "schedule_camera_hardware_readiness",
    "collect_more_qc_feedback",
    "keep_production_release_blocked"
  ]
}
```

In-app browser snapshot showed:

- `artifact readiness metadata loaded`
- `ready_for_shadow_observation_review: shadow_observation_review`
- `submit_shadow_observation_payload`

The preview server is HTTP-only, so the HMI WebSocket attempted
`/ws/inspection` and received 404. This does not affect the artifact readiness
HTTP evidence for this task.

## Restricted Change Check

No raw media, raw datasets, customer data, model weights, model binaries,
notebooks, model deserialization, inference runtime, camera SDK, live camera
capture, GPU use, secrets, credentials, destructive migrations, production
deploy/release, product spec approval, QC/SOP tolerance approval, model
promotion approval, production PASS/NG authority, or production auto-reject
behavior is included.

## Residual Risks

- The readiness report now points to the correct next app-safe metadata loop,
  but real model quality, real dataset quality, label policy approval, and model
  promotion still require external MLOps/QC evidence and human gates.
- Live camera remains blocked until hardware arrives and camera readiness is
  explicitly approved.
- Runtime daily status still reports tmux relay/tunnel and Windmill CLI
  attention; this task intentionally did not touch secret-adjacent runtime
  credentials.

## Rollback

Revert the FQV2-044 PR to restore the previous artifact readiness next-action
wording. Existing artifact intake, detector status, shadow observation request
validator, HMI, feedback, and product CI behavior remain valid.

## Memory Candidate

- memory_type: task_lesson
- content: After FQV2 shadow detector bridge and request contract are merged,
  artifact readiness should recommend `shadow_observation_review` and
  `submit_shadow_observation_payload`, not another shadow integration issue.
- source_ref: https://github.com/namlogan/MIL/issues/145
- why reusable: Future MLOps/camera handoff tasks should advance readiness
  actions after completed implementation stages.
- scope: flange_qc_v2
- suggested status: candidate
