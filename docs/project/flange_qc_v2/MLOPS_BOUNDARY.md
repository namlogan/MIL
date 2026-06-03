# FLANGE QC App V2 MLOps Boundary

## Decision

The app is built now. MLOps and model training run separately and integrate later
through explicit contracts.

## App Owns

- Inspection API and WebSocket HMI payload.
- Product specs and deterministic SOP rule engine.
- Geometry measurement contracts.
- Calibration contract.
- Replay/no-camera E2E.
- SQLite audit evidence.
- QC feedback contract.
- Sanitized QC feedback metadata export for labeling and model-review planning.
- Detector adapter interface and stub adapter.
- Model artifact manifest contract and safe manifest loader.
- Dataset manifest and evaluation report handoff contracts.
- Safe states for missing model or unapproved model evidence.

## MLOps Owns Later

- Dataset management and labeling workflows.
- Model training and evaluation.
- Model registry and promotion criteria.
- Production model accuracy gates.
- Model binary packaging, deserialization, runtime execution, and accelerator
  selection.
- Raw dataset retention and privacy controls.
- Model rollback and shadow evaluation.

## Integration Contract

The detector adapter may return observations with labels, confidence, bbox, source
model reference, and evidence reference. The SOP rule engine remains the only
component that can produce final inspection decisions.

Bootstrap detector adapter implementation lives in:

```text
apps/flange_qc_v2/detector.py
contracts/flange_qc_v2/detector/detector_result.schema.json
```

Bootstrap model artifact boundary lives in:

```text
apps/flange_qc_v2/model_artifact.py
contracts/flange_qc_v2/model/model_artifact_manifest.schema.json
```

Bootstrap dataset and evaluation handoff contracts live in:

```text
apps/flange_qc_v2/mlops_handoff.py
contracts/flange_qc_v2/mlops/dataset_manifest.schema.json
contracts/flange_qc_v2/mlops/evaluation_report.schema.json
docs/project/flange_qc_v2/DATASET_MLOPS_HANDOFF.md
```

The combined dataset/model/camera intake bundle lives in:

```text
templates/flange_qc_v2/artifact_intake/
apps/flange_qc_v2/artifact_intake.py
scripts/flange_qc_v2/validate_artifact_intake.py
docs/project/flange_qc_v2/ARTIFACT_INTAKE.md
```

The default stub adapter returns `NOT_EVALUATED` with `MODEL_MISSING` when no
model evidence is configured, or `ASSIST` with `MODEL_REVIEW_REQUIRED` when stub
observations are supplied for review. The adapter rejects raw media paths and
validates observation label, confidence, bbox, model reference, and evidence
reference through the app domain contract. It does not load model weights,
TensorRT engines, production datasets, or MLOps artifacts, and it cannot emit
`PASS` or `NG`.

The model artifact manifest contract records the approved metadata needed to
connect future MLOps output to the detector boundary: model reference,
artifact version, declared labels, output schema, evaluation report reference,
digest, approval status, and source reference. The app loader accepts only JSON
manifests, rejects raw weight files, rejects unknown contract versions, blocks
absolute or parent-directory path references, and requires
`production_authority=false` with `shadow_mode=true`.

`ManifestDetectorAdapter` can use a validated manifest to tag review-only
observations with the manifest `model_ref`. Labels not declared by the manifest
are rejected. This is traceability and integration readiness only; it does not
deserialize model binaries, execute inference, approve model promotion, approve
production release, or grant production PASS/NG authority.

The dataset and evaluation handoff validators accept sanitized metadata only.
They reject raw media paths, missing split or metric evidence, PII/customer-data
flags, production authority, and model promotion. Passing these contracts means
the MLOps artifacts are structurally ready for shadow integration review; it
does not approve the dataset, model, live camera behavior, production
retention, or production PASS/NG authority.

The QC feedback export reads only the app audit SQLite store and emits
`qc_feedback_export.v1` JSONL metadata for MLOps labeling review. It can include
operator feedback, inspection decision, product metadata, and compact detector
observation label/confidence/bbox evidence. It must not export raw media, raw
datasets, full inspection payload dumps, model binaries, notebooks, credentials,
model promotion evidence, or production PASS/NG authority.

The artifact intake validator combines dataset, evaluation, model artifact, and
camera boundary checks into a single JSON readiness result. It rejects raw media,
model binaries, and secrets-like files in the intake directory, then reports
whether the next allowed issue is shadow model integration or intake repair.

The app exposes a metadata-only shadow detector bridge through
`GET /detector/shadow/status`. The endpoint reads only
`FLANGE_QC_V2_ARTIFACT_INTAKE_DIR`, requires the artifact intake validator to
report `ready.shadow_model_integration_issue=true`, then loads only
`model_artifact_manifest.json` to return adapter id, model reference, artifact
version, labels, evaluation report reference, approval status, shadow mode, and
approval blockers. Missing or invalid intake returns a non-ready state with
`production_authority=false`. The bridge does not load weights, deserialize model
binaries, run inference, import camera SDKs, capture frames, approve model
promotion, or grant production PASS/NG authority.

No-camera replay frames may carry optional synthetic `detector_observations`
metadata for review. The replay parser validates label, confidence, and bbox
through the detector observation domain contract, then strips any model or
evidence reference from the replay fixture. HMI snapshot generation attaches
these observations only when `FLANGE_QC_V2_ARTIFACT_INTAKE_DIR` points to a
ready intake bundle; `ManifestDetectorAdapter` fills the manifest `model_ref`
and evaluation evidence reference. Missing or invalid intake preserves the safe
empty observation state. This path is still replay/shadow evidence only and
does not execute model inference, read raw media, touch camera hardware, or
grant production PASS/NG authority.
