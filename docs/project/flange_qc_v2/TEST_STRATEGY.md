# FLANGE QC App V2 Test Strategy

## Test Layers

| Layer | Command | Required Before Merge |
|---|---|---|
| Unit | `python -m pytest tests/unit -q` | Yes for app code |
| Contract | `python -m pytest tests/contract -q` | Yes for API/payload/config changes |
| Integration | `python -m pytest tests/integration -q` | Yes for app workflow changes |
| Replay | `python -m pytest tests/replay -q` | Yes for inspection pipeline changes |
| Lint | `ruff check .` | Yes when Python app exists |
| Typecheck | `mypy apps/flange_qc_v2/src` | Yes when Python app exists |
| Config | `python tools/validate_config.py --all` | Yes for config/spec changes |
| Contracts | `python tools/validate_contracts.py --root contracts` | Yes for contract changes |
| Replay smoke | `python tools/replay_inspection.py --source samples/replay/flange_sample.mp4 --limit 50 --no-gpu` | Required before release |

## Critical Behaviors

- App start must not require camera, GPU, model, or factory data.
- Health endpoint must report DB, storage, config, calibration, camera, and model state.
- Unknown product returns `BLOCKED`.
- Missing or pending calibration returns `BLOCKED`.
- Product-specific tolerance is validated by config/schema/tests.
- 3 length points, 3 width points, and 2 diagonals are required by domain contract.
- Boundary/corners measurement derivation tests validate that sanitized replay
  corners plus `calibration.geometry.inch_per_pixel` produce the same 3 length
  points, 3 width points, and 2 diagonals consumed by product tolerance logic.
  Missing calibration scale fails closed, and derived evidence remains
  `production_authority=false`.
- Phase 1 length/width shadow evaluation blocks before product spec,
  calibration, and geometry evidence are complete; otherwise it emits rule-level
  evidence with `all_points_must_pass_bootstrap`, bounds, min/max/average, and
  out-of-tolerance point indexes.
- Length or width points outside product tolerance return shadow `NG` with
  `LENGTH_OUT_OF_TOLERANCE` and/or `WIDTH_OUT_OF_TOLERANCE`; production
  authority remains false until QC/SOP tolerance approval.
- Diagonal deviation greater than 0.5 inch returns NG in phase 2.
- Phase 3 model/vision-dependent SOP rules return safe `ASSIST` fallback
  evidence with `MODEL_REVIEW_REQUIRED` and never production authority.
- Phase 4 post-MVP SOP rules return `NOT_EVALUATED`, Phase 4 review-dependent
  rules return `ASSIST`, and fallback aggregation never maps disabled or review
  states to `PASS`.
- Health endpoint tests validate that the SOP decision engine is reported as
  `shadow_implemented_requires_qc_sop_approval`, not `not_implemented`, while
  `decision_authority=none` and QC/SOP approval blockers remain present.
- Detector returns observations only.
- Missing model produces `NOT_EVALUATED`, `ASSIST`, or `BLOCKED` for model-dependent rules.
- Model artifact manifests validate contract version, registry reference,
  declared labels, safe repository-relative evidence paths, digest, shadow mode,
  and no production authority before detector integration.
- MLOps dataset manifests validate dataset snapshot reference, label set,
  point-in-time split policy, train/validation/test counts, privacy flags, no
  raw media, and no production authority.
- MLOps evaluation reports validate model reference, matching dataset snapshot,
  precision/recall/F1, slice metrics, p95 latency budget, no promotion approval,
  and no production authority.
- WebSocket payload schema validates normalized bbox values in `[0, 1]`.
- Replay and HMI snapshot tests validate ordered SOP `phase_results`, top-level
  `FINAL` fail-closed aggregation, and audit persistence of the full snapshot
  payload.
- HMI stream endpoint tests validate that `/inspection/replay` can read replay,
  product spec, and calibration paths from env-only configuration, including the
  boundary-derived measurement fixture, while ignoring request-supplied path
  query strings.
- HMI screen tests and browser evidence validate the operator-facing
  phase-results drilldown renders ordered phase cards, rule ids, compact
  evidence summaries, authority blockers, production-authority state, and a
  safe empty state.
- HMI screen tests and browser evidence validate the QC-device phase layout,
  independent Phase 1/Phase 2 cards, and Phase 2 suspected-stitch traffic
  states for PASS/green, NG/red, and review-or-blocked/amber display.
- HMI screen tests and browser evidence validate detector observation details
  render label, confidence, bbox, model reference, evidence reference, and a
  safe empty state without changing production authority.
- HMI screen tests and browser evidence validate the signal-first QC tablet
  viewport: measurement strip, green/red/amber operator states, suspected-region
  bbox overlay well, and alarm-correct/false-alarm bindings to the existing
  shadow feedback endpoint.
- HMI screen tests and browser evidence validate that the QC tablet top strip
  separates product number, measurement SOP scope, and stitch SOP scope. Browser
  evidence should include the common case where the overall banner is red
  `CHECK`, measurement is green `OK`, and stitch is red `CHECK`.
- Artifact intake endpoint tests validate safe unconfigured state and configured
  template readiness from `FLANGE_QC_V2_ARTIFACT_INTAKE_DIR`; configured intake
  keeps `ready.shadow_model_integration_issue=true` for compatibility while
  returning `next_issue.recommended_task=shadow_observation_review` and
  `submit_shadow_observation_payload`. HMI screen tests and browser evidence
  validate the metadata-only readiness panel.
- Shadow detector bridge tests validate that `/detector/shadow/status` reads
  only `FLANGE_QC_V2_ARTIFACT_INTAKE_DIR`, reports safe unconfigured state, and
  returns manifest metadata only after artifact intake is ready. Ready status
  must expose `ready_for_shadow_observation_review`,
  `next_task=shadow_observation_review`, and
  `submit_shadow_observation_payload`. Adapter tests prove
  `ManifestDetectorAdapter` remains review-only and cannot emit production
  PASS/NG authority.
- Shadow detector observation dry-run tests validate that
  `/detector/shadow/observations` reads manifest metadata only from
  `FLANGE_QC_V2_ARTIFACT_INTAKE_DIR`, returns `detector.result.v1` for
  sanitized observations, fills model/evidence refs from the manifest, returns
  `NOT_EVALUATED` without observations, and rejects missing intake,
  request-supplied paths, request-supplied model/evidence refs, raw source URIs,
  invalid labels, invalid bbox/confidence, and production authority.
- Shadow detector observation request contract tests validate
  `shadow_detector_observation_request.v1`, the checked-in sample payload, and
  `scripts/flange_qc_v2/validate_shadow_detector_observations.py`; the validator
  must accept sanitized label/confidence/bbox metadata and reject raw-media
  source URIs, request-supplied artifact/model/data paths, request-supplied
  model/evidence refs, malformed bbox/confidence, extra fields, and missing
  input files.
- HMI screen tests and browser evidence validate that detector bridge status
  renders ready state, adapter, model reference, labels, approval status, and
  authority blockers from `/detector/shadow/status`.
- Replay/HMI stream tests validate optional synthetic `detector_observations`,
  invalid observation rejection, safe empty observations without artifact intake,
  and manifest-filled review-only observations when artifact intake is ready.
- Audit DB stores inspection, rule, calibration, and feedback evidence.
- QC feedback export tests validate one sanitized JSONL metadata record per
  stored feedback row, empty audit export behavior, and fail-closed missing DB
  behavior without raw payloads or production authority.
- QC feedback export validator tests validate the `qc_feedback_export.v1`
  schema, successful JSONL validation, empty-file validation, and fail-closed
  rejection of full payload dumps, `production_authority=true`, raw-media-like
  references, malformed bbox values, missing fields, and missing input files.
- QC feedback labeling review pack tests validate aggregate counts, empty-pack
  next actions, fail-closed invalid input, CLI JSON output, and absence of raw
  payload dumps or production authority.
- Artifact readiness report tests validate shadow-ready template intake advances
  to `shadow_observation_review`, recommends
  `submit_shadow_observation_payload` instead of reopening shadow integration,
  keeps live-camera and production-release blockers, handles optional labeling
  review packs, rejects malformed packs, emits CLI output, fails closed for
  missing intake, and keeps `/artifact-readiness/status` env-only.
- HMI screen tests and browser evidence validate that artifact readiness renders
  as a compact support panel outside the primary QC tablet viewport, fetches
  `/artifact-readiness/status`, displays shadow model, live camera, QC feedback,
  production release, and recommended next actions, and does not change QC
  pass/fail visual semantics.

## Fixtures And Test Data

Use synthetic fixtures and replay samples for baseline CI. Do not commit secrets,
production credentials, raw customer data, or unapproved production datasets.
Factory images and production datasets belong to a separate approved data/MLOps
source of truth.

Model artifacts from MLOps must enter the app through
`contracts/flange_qc_v2/model/model_artifact_manifest.schema.json` and
`apps/flange_qc_v2/model_artifact.py`. Do not commit model weights, TensorRT
engines, production datasets, raw factory media, or notebooks as app fixtures.

Dataset and evaluation handoff artifacts must enter through
`contracts/flange_qc_v2/mlops/dataset_manifest.schema.json`,
`contracts/flange_qc_v2/mlops/evaluation_report.schema.json`, and
`apps/flange_qc_v2/mlops_handoff.py`. Contract tests must reject raw media
paths, PII/customer-data flags, missing split or metric evidence, production
authority, and promotion approval.

Combined dataset/model/camera intake must enter through
`templates/flange_qc_v2/artifact_intake/` and
`scripts/flange_qc_v2/validate_artifact_intake.py`. Tests must prove the
template bundle validates, raw media/model/secrets-like files are rejected, and
dataset/evaluation/model references stay consistent before a shadow model
integration issue is opened.

Shadow detector metadata bridge tests use the same sanitized artifact intake
template and synthetic detector requests. They must not add model weights,
TensorRT/ONNX/PyTorch runtimes, camera SDKs, live capture, raw media, raw
datasets, or production model promotion evidence.

Replay detector observation fixtures are metadata only. They may include label,
confidence, and normalized bbox values, but must not include raw image paths,
model binaries, runtime outputs, customer data, credentials, production model
promotion evidence, or final inspection authority.

QC feedback export fixtures must use temporary SQLite audit stores and synthetic
metadata only. JSONL records must not include raw media, raw datasets, full
payload dumps, model weights, notebooks, credentials, or production authority.
The JSONL validator must run before any exported feedback is used for MLOps
labeling review.
The labeling review pack must stay aggregate-only and must not include raw media,
raw datasets, full feedback rows, model weights, notebooks, credentials, or
production authority.
The artifact readiness report must stay metadata-only and must not include raw
media, raw datasets, full feedback rows, model weights, notebooks, credentials,
or production authority.

## Agent Verification Rules

Every implementation issue must list exact checks. If a check cannot run because
the app skeleton does not exist yet, the PR handoff must record that as a blocker
or not-applicable reason. No check may be silently skipped.

## Release Smoke

Release smoke must run the app outside the worker session, execute replay/no-camera
inspection, verify health, confirm audit writes, and attach rollback evidence.
