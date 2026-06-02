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
- Detector adapter interface and stub adapter.
- Model artifact manifest contract and safe manifest loader.
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
