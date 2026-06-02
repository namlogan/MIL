# FLANGE QC App V2 Dataset And MLOps Handoff

## Purpose

This handoff defines the metadata artifacts that must exist before a trained
detector model can be connected to the app boundary.

The app does not own raw datasets, labeling workflows, notebooks, model weights,
model registry credentials, or production model promotion. Those remain in the
MLOps source of truth.

## Required Artifacts

Use the artifact intake template and validator before opening the next
implementation issue:

```text
templates/flange_qc_v2/artifact_intake/
scripts/flange_qc_v2/validate_artifact_intake.py
docs/project/flange_qc_v2/ARTIFACT_INTAKE.md
```

### Dataset Manifest

Contract:

```text
contracts/flange_qc_v2/mlops/dataset_manifest.schema.json
apps/flange_qc_v2/mlops_handoff.py
```

Required metadata:

- `dataset_snapshot_ref` using `dataset://...`
- `entity_grain` as `frame` or `inspection`
- `storage_ref` using approved dataset registry/storage reference
- declared `labels`
- point-in-time `split_policy`
- positive `split_counts` for train, validation, and test
- `privacy_class=sanitized_metadata_only`
- `contains_pii=false`
- `contains_customer_data=false`
- `raw_media_included=false`
- `production_authority=false`
- `source_ref` to the issue, PR, registry record, or eval report

### Evaluation Report

Contract:

```text
contracts/flange_qc_v2/mlops/evaluation_report.schema.json
apps/flange_qc_v2/mlops_handoff.py
```

Required metadata:

- registry-style `model_ref`
- matching `dataset_snapshot_ref`
- `precision`, `recall`, and `f1`
- non-empty per-label or per-slice metrics
- p95 latency and p95 latency budget evidence
- `promotion_decision=not_approved`
- `production_authority=false`
- `source_ref`

## Forbidden In App Repo

- Raw factory/customer images or video.
- Raw datasets or labeling exports.
- PII or customer data.
- Notebooks used for exploration/training.
- Model weights, ONNX files, TensorRT engines, PyTorch checkpoints, or binary
  runtime artifacts.
- Registry credentials, API keys, or storage secrets.

## Gate Meaning

Passing these contracts means only that MLOps metadata is structurally ready for
shadow integration review. It does not approve model promotion, production
release, production PASS/NG authority, QC/SOP tolerances, product specs, live
camera hardware, or production data retention.
