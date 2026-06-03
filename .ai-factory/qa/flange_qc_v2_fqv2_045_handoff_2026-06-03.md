# FQV2-045 QA Handoff: Artifact Intake Next Issue Alignment

## Scope

- Branch: `agent/147-artifact-intake-shadow-observation-next-issue`
- Task: FQV2-045
- Issue: https://github.com/namlogan/MIL/issues/147

## Files Changed

- `apps/flange_qc_v2/artifact_intake.py`
- `tests/flange_qc_v2/test_artifact_intake.py`
- `docs/project/flange_qc_v2/ARTIFACT_INTAKE.md`
- `docs/project/flange_qc_v2/DATA_MODEL.md`
- `docs/project/flange_qc_v2/TEST_STRATEGY.md`
- `.ai-factory/gates/flange_qc_v2_fqv2_045_dor.json`
- `.ai-factory/qa/flange_qc_v2_fqv2_045_handoff_2026-06-03.md`

## Summary

- Kept `ready.shadow_model_integration_issue=true` for compatible detector and
  gate behavior.
- Changed valid artifact intake `next_issue.recommended_task` from
  `shadow_model_integration` to `shadow_observation_review`.
- Added `next_issue.recommended_next_actions` for valid intake:
  `submit_shadow_observation_payload` and `collect_more_qc_feedback`.
- Preserved missing/unconfigured/invalid intake repair behavior and production
  authority false.
- Updated docs and test strategy so lower-level intake status matches aggregate
  artifact readiness.

## TDD Evidence

- RED:
  `python3 -m unittest tests.flange_qc_v2.test_artifact_intake.ArtifactIntakeTemplateTests.test_template_bundle_validates_all_required_artifacts tests.flange_qc_v2.test_artifact_intake.ArtifactIntakeStatusEndpointTests.test_status_endpoint_validates_configured_intake_dir_from_env -v`
  failed because both paths still returned `shadow_model_integration`.
- GREEN:
  the same tests passed after updating `artifact_intake.py`.

## Checks

- `python3 -m json.tool .ai-factory/gates/flange_qc_v2_fqv2_045_dor.json >/dev/null`
- `git diff --check`
- `python3 -m unittest tests.flange_qc_v2.test_artifact_intake -v` passed, 9 tests.
- `python3 -m unittest tests.flange_qc_v2.test_artifact_readiness -v` passed, 9 tests.
- `python3 -m unittest tests.flange_qc_v2.test_detector_adapter -v` passed, 21 tests.
- `python3 -m unittest tests.flange_qc_v2.test_hmi_screen -v` passed, 10 tests.
- `python3 -m compileall -q apps/flange_qc_v2 tests/flange_qc_v2 scripts/flange_qc_v2` passed.
- `python3 -m unittest discover -s tests/flange_qc_v2 -v` passed.
- `python3 scripts/product-ci/run_product_checks.py` passed.
- `python3 -m unittest discover -s tests -v` passed, 196 tests.

## HTTP And Browser Evidence

The local HMI preview was restarted on:

```text
http://127.0.0.1:8766/hmi
```

HTTP smoke for `/artifact-intake/status` returned:

```json
{
  "task": "shadow_observation_review",
  "actions": [
    "submit_shadow_observation_payload",
    "collect_more_qc_feedback"
  ],
  "ready": {
    "shadow_model_integration_issue": true,
    "live_camera_implementation_issue": false
  }
}
```

HTTP smoke for `/artifact-readiness/status` returned artifact intake lane
`recommended_task=shadow_observation_review` and aggregate action
`submit_shadow_observation_payload`.

In-app browser snapshot showed:

- `Next Task`
- `shadow_observation_review`
- `ready_for_shadow_observation_review: shadow_observation_review`
- `submit_shadow_observation_payload`

The preview server is HTTP-only, so the HMI WebSocket attempted
`/ws/inspection` and received 404. This does not affect the artifact intake or
readiness HTTP evidence for this task.

## Restricted Change Check

No raw media, raw datasets, customer data, model weights, model binaries,
notebooks, model deserialization, inference runtime, camera SDK, live camera
capture, GPU use, secrets, credentials, destructive migrations, production
deploy/release, product spec approval, QC/SOP tolerance approval, model
promotion approval, production PASS/NG authority, production auto-reject
behavior, or Windmill credential/tunnel/runtime change is included.

## Residual Risks

- Real model quality, real dataset quality, label policy approval, and model
  promotion still require external MLOps/QC evidence and human gates.
- Live camera remains blocked until hardware arrives and camera readiness is
  explicitly approved.
- Runtime daily status still reports tmux relay/tunnel and Windmill CLI
  attention; this task intentionally did not touch secret-adjacent runtime
  credentials.

## Rollback

Revert the FQV2-045 PR to restore the previous artifact intake next-issue
wording. Existing artifact intake validation, artifact readiness, detector
status, shadow observation request validator, HMI, feedback, and product CI
behavior remain valid.

## Memory Candidate

- memory_type: task_lesson
- content: Artifact intake should keep the compatibility readiness flag
  `shadow_model_integration_issue=true` while advancing `next_issue` to
  `shadow_observation_review` and `submit_shadow_observation_payload` after the
  shadow detector bridge exists.
- source_ref: https://github.com/namlogan/MIL/issues/147
- why reusable: Future readiness/status endpoints can keep stable machine flags
  while advancing operator-facing next actions.
- scope: flange_qc_v2
- suggested status: candidate
