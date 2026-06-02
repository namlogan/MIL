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
- Safe states for missing model or unapproved model evidence.

## MLOps Owns Later

- Dataset management and labeling workflows.
- Model training and evaluation.
- Model registry and promotion criteria.
- Production model accuracy gates.
- Raw dataset retention and privacy controls.
- Model rollback and shadow evaluation.

## Integration Contract

The detector adapter may return observations with labels, confidence, bbox, source
model reference, and evidence reference. The SOP rule engine remains the only
component that can produce final inspection decisions.
