# FLANGE QC App V2 User Flows

## Actors

- QC operator: runs or observes inspections and records feedback.
- QC/domain owner: approves SOP interpretation, product specs, and production readiness.
- Engineering/operator: runs replay, validates contracts, monitors audit evidence, and deploys.
- Detector/MLOps provider: supplies model observations through the adapter contract only.

## Critical Path: Replay Inspection

1. Operator or CI starts app in replay mode.
2. App loads runtime config, product specs, calibration state, and detector
   adapter. `/inspection/replay` may read optional env-only paths:
   `FLANGE_QC_V2_REPLAY_MANIFEST_PATH`, `FLANGE_QC_V2_PRODUCT_SPECS_PATH`, and
   `FLANGE_QC_V2_CALIBRATION_PATH`; request-supplied paths are ignored.
3. Replay source provides frames.
4. Vision preprocessing and geometry measurement produce measurements. In
   no-camera shadow replay, a sanitized frame may provide boundary corners; the
   app uses calibration scale to derive length, width, and diagonal measurements
   before running the same SOP rules.
5. App preserves measurement provenance in the inspection snapshot:
   `provided_measurements` for precomputed replay values or
   `boundary_corners_calibrated_shadow` with sanitized boundary/calibration
   evidence for boundary-derived values.
6. Detector adapter returns observations when available.
7. SOP rule engine evaluates product, calibration, geometry, and
   model-dependent rules. Phase 3 consumes sanitized detector observations as
   review-only evidence: no observations return `NOT_EVALUATED`, relevant
   observations return `ASSIST`, and neither path can emit production `PASS` or
   `NG`.
8. Inspection decision emits PASS, NG, BLOCKED, NOT_EVALUATED, or ASSIST reason codes.
9. Audit DB stores inspection and rule evidence.
10. WebSocket pushes HMI payload to the UI.
11. QC feedback can attach corrections or notes to the inspection evidence.

## Critical Path: No-Camera HMI Feedback Loop

1. Operator opens `/hmi` while camera hardware is pending.
2. HMI loads the current synthetic replay snapshot through
   `/inspection/replay` and continues to accept `/ws/inspection` updates.
   The snapshot exposes a top-level `FINAL` aggregate decision and ordered
   `phase_results` for Phase 1 through Phase 4 SOP evidence.
3. Operator first scans the signal-first QC tablet viewport. The top strip shows
   a small product number plus two independent SOP scopes: `Do luong` for
   measured length/width evidence and `Mui chi` for stitch or model-observation
   evidence. The large banner maps the current overall operator action to green
   `PASS`, red `CHECK`, or amber `REVIEW`.
4. If the viewport is green, QC continues to the next work item. If the viewport
   is red because the stitch scope is red while the measurement scope is green,
   QC inspects only the suspected stitch/defect area shown on the image well. If
   the measurement scope is red, QC self-measures before disposition. If the
   viewport is amber, QC waits for setup, calibration, approval, or model-evidence
   readiness.
5. When review-only detector observations include a normalized bbox, the image
   well draws a red suspected-region overlay. The overlay is assistive only and
   never grants production PASS/NG authority.
6. For red alerts, QC can mark `Alert correct` or `False alarm`; the HMI writes
   those buttons through the existing `/feedback` shadow endpoint as
   `CONFIRM_BLOCKED` or `MARK_FALSE_POSITIVE`.
7. Operator inspects the HMI SOP phase-results drilldown to see each phase
   decision, blockers, production-authority state, rule ids, and compact rule
   evidence without opening raw JSON.
8. HMI shows detector bridge status from `/detector/shadow/status`, including
   ready state, adapter, model reference, labels, approval status, and remaining
   authority blockers when metadata is available.
9. HMI shows a compact artifact readiness support panel from
   `/artifact-readiness/status`, including shadow model, live camera, QC
   feedback labeling, production release blocker, and recommended next actions.
   This panel is outside the primary QC tablet viewport so the green/red/amber
   operator signal remains the main QC workflow.
10. If review-only detector observations are present, the HMI detector
   observations panel shows label, confidence, bbox, model reference, and
   evidence reference without granting inspection authority.
11. When `FLANGE_QC_V2_AUDIT_DB_PATH` is configured, replay refresh initializes
   the local audit store and records the current inspection idempotently.
12. Operator refreshes the replay snapshot from the HMI header when a manual
   no-camera check is needed.
13. Operator records reviewer ID, feedback type, and note for the current
   inspection.
14. HMI submits the feedback payload to `/feedback` with the current inspection
   ID and shadow decision.
15. The feedback contract returns shadow evidence with
   `production_authority=false` and `PRODUCTION_APPROVAL_REQUIRED`.
16. When audit persistence is configured, `/feedback` stores the feedback in
   `qc_feedback` and returns audit persistence evidence for the HMI status.
17. Any production release, product spec approval, QC/SOP tolerance approval,
   live hardware approval, or production PASS/NG authority remains outside this
   flow.

## Critical Path: Artifact Intake Readiness

1. Operator prepares sanitized dataset/model/camera metadata in an ignored
   intake directory.
2. Operator sets `FLANGE_QC_V2_ARTIFACT_INTAKE_DIR` to that directory before
   starting the app.
3. HMI calls `/artifact-intake/status` and displays configured state, shadow
   model readiness, live camera readiness, next task, warnings/errors, and
   artifact names/summaries.
4. Engineering/operator can call `/artifact-readiness/status`, and HMI can
   display it as a compact support panel, to see the combined readiness report
   for artifact intake, shadow model, live camera, QC feedback labeling review,
   and production release authority. The endpoint reads only configured env
   paths and never accepts request-supplied paths.
5. If `ready.shadow_model_integration_issue=true`, the next allowed app task is
   shadow observation review: validate and submit sanitized detector observation
   metadata while keeping model promotion and production PASS/NG authority
   blocked.
6. If `ready.live_camera_implementation_issue=false`, hardware work remains
   blocked until camera readiness and credential handling are approved.
7. If the env var is missing or the bundle is invalid, the HMI stays in a safe
   repair/configuration state and no production authority is granted.

## Critical Path: Shadow Detector Metadata Bridge

1. Operator keeps `FLANGE_QC_V2_ARTIFACT_INTAKE_DIR` pointed at a validated
   metadata-only intake bundle.
2. App calls `/detector/shadow/status` to check detector integration readiness.
3. If artifact intake is missing or invalid, the endpoint returns
   `ready=false`, approval blockers, and an actionable next task without loading
   model metadata.
4. If `ready.shadow_model_integration_issue=true`, the endpoint loads only
   `model_artifact_manifest.json` and returns the `manifest-detector` adapter id,
   model reference, artifact version, labels, evaluation report reference,
   approval status, shadow mode, production-authority blockers, and
   `next_task=shadow_observation_review`.
5. HMI calls this endpoint and renders the detector bridge status without
   opening raw JSON or changing decision authority.
6. MLOps/engineering can post sanitized review-only observation metadata to
   `/detector/shadow/observations`. The endpoint reads the model manifest only
   from `FLANGE_QC_V2_ARTIFACT_INTAKE_DIR`, rejects request-supplied artifact or
   model paths, fills `model_ref` and `evidence_ref` from the manifest, and
   returns `detector.result.v1` with `production_authority=false`.
7. Before posting observation metadata, MLOps/engineering validates payload
   files with `scripts/flange_qc_v2/validate_shadow_detector_observations.py`
   against `shadow_detector_observation_request.v1`. The checked-in sample
   payload is metadata-only and contains no raw media, model refs, or evidence
   refs from the request.
8. Replay frames may provide sanitized synthetic `detector_observations`.
   During HMI snapshot generation, those observations are attached only through
   `ManifestDetectorAdapter` after artifact intake is ready. The adapter fills
   the manifest model reference and evaluation evidence reference.
9. Model weights, runtime inference, camera access, model promotion, product
   spec approval, QC/SOP tolerance approval, and production release remain
   outside this flow.

## Critical Path: Production-Like Shadow Mode

1. Owner approves shadow-mode runbook and rollback plan.
2. App receives replay or live-camera frames in non-authoritative mode.
3. Deterministic rules may produce NG/BLOCKED, but model-dependent rules remain
   advisory unless model promotion is approved.
4. QC feedback is recorded for later MLOps analysis.
5. Release evidence reports observed behavior, false positives, false negatives,
   blocked states, and rollback readiness.

## Edge Cases

- Unknown product code returns `BLOCKED`.
- Missing or pending calibration returns `BLOCKED`.
- Missing detector/model returns `NOT_EVALUATED` for model-dependent rules.
- Invalid bbox outside `[0, 1]` fails contract validation.
- Image quality failure blocks or assists according to configured rule severity.
- Audit DB unavailable makes health degraded and blocks production promotion.

## Interfaces

- HTTP health endpoint.
- HTTP replay inspection API at `/inspection/replay`.
- HTTP QC feedback validation endpoint at `/feedback`.
- HTTP artifact intake readiness endpoint at `/artifact-intake/status`.
- HTTP shadow detector metadata endpoint at `/detector/shadow/status`.
- WebSocket HMI stream.
- SQLite audit DB.
- Product spec JSON config.
- Calibration JSON config.
- Detector adapter interface.
- Replay command-line tool.

## Acceptance Scenarios

- Replay smoke creates an inspection record and WebSocket-compatible payload.
- Unknown product cannot PASS.
- Missing calibration cannot PASS.
- Diagonal deviation above 0.5 inch produces phase 2 NG.
- Missing model does not create production PASS/NG for model-dependent defects.
- HMI refresh returns the current no-camera replay snapshot.
- HMI renders a signal-first QC tablet viewport with a top measurement strip,
  large green/red/amber operator state, suspected-region overlay well, and
  alarm-correct/false-alarm buttons for red alerts.
- HMI renders artifact readiness from `/artifact-readiness/status` as a compact
  support panel outside the primary QC tablet viewport.
- HMI feedback submits the current inspection ID to `/feedback` and receives
  shadow-only authority blockers.
- Shadow detector status returns a safe unconfigured state without env setup and
  returns manifest metadata from the template bundle when intake is ready.
- Shadow detector observation dry-run returns `detector.result.v1` from sanitized
  request/observation metadata and rejects request-supplied paths or model refs.
- Shadow detector observation request validation accepts the checked-in sample
  payload and rejects raw-media source URIs, request-supplied artifact paths,
  model refs, evidence refs, malformed bbox/confidence, and missing files.
- Replay/HMI snapshots keep observations empty without ready intake and attach
  review-only manifest detector observations when ready intake and synthetic
  replay observation metadata are present.
