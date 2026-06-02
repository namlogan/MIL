# FLANGE QC App V2 Artifact Intake

## Purpose

This is the entry point for real dataset, model, and camera handoff artifacts.
It prepares the next implementation issue without putting raw data, model
weights, notebooks, camera credentials, or secrets into the app repository.

## Template Bundle

Tracked template:

```text
templates/flange_qc_v2/artifact_intake/
```

Files:

- `dataset_manifest.json`
- `evaluation_report.json`
- `model_artifact_manifest.json`
- `camera_boundary.json`

Copy the template to an ignored working location and replace only metadata
fields with real references from the dataset/MLOps/camera source of truth:

```bash
mkdir -p .ai-factory/tmp/flange_qc_v2/intake-YYYY-MM-DD
cp templates/flange_qc_v2/artifact_intake/*.json .ai-factory/tmp/flange_qc_v2/intake-YYYY-MM-DD/
```

## Validation

Run:

```bash
python3 scripts/flange_qc_v2/validate_artifact_intake.py \
  --intake-dir .ai-factory/tmp/flange_qc_v2/intake-YYYY-MM-DD
```

The validator checks:

- dataset manifest contract;
- evaluation report contract;
- model artifact manifest contract;
- camera boundary contract;
- dataset/evaluation snapshot consistency;
- model/evaluation `model_ref` consistency;
- model labels are declared by the dataset manifest;
- no raw media, model binaries, or secrets-like files in the intake directory.

## Next Issue Rules

If `ready.shadow_model_integration_issue=true`, the next allowed issue is a
shadow model integration task. That task may read metadata and connect a model
reference to the detector boundary, but it still cannot run production PASS/NG
or approve model promotion.

If `ready.live_camera_implementation_issue=false`, hardware work remains blocked.
Open camera hardware readiness only after the physical camera, lens, lighting,
mount geometry, calibration plan, and credential handling plan are available.

## Forbidden

Do not put these in the intake directory or repo:

- raw factory/customer images or video;
- raw datasets or labeling exports;
- PII or customer data;
- notebooks;
- model weights, ONNX files, TensorRT engines, checkpoints, or binary runtime
  artifacts;
- registry credentials, API keys, camera credentials, or storage secrets;
- production deploy/release approval evidence.
