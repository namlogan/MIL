# FQV2-022 QA Handoff: MLOps Dataset And Evaluation Contracts

## Source

- GitHub issue: https://github.com/namlogan/MIL/issues/101
- Branch: `agent/101-mlops-dataset-eval-contracts`
- Task: FQV2-022

## Files Changed

- `apps/flange_qc_v2/mlops_handoff.py`
- `contracts/flange_qc_v2/mlops/dataset_manifest.schema.json`
- `contracts/flange_qc_v2/mlops/evaluation_report.schema.json`
- `tests/flange_qc_v2/test_mlops_handoff.py`
- `docs/project/flange_qc_v2/DATASET_MLOPS_HANDOFF.md`
- `docs/project/flange_qc_v2/MLOPS_BOUNDARY.md`
- `docs/project/flange_qc_v2/DATA_MODEL.md`
- `docs/project/flange_qc_v2/TEST_STRATEGY.md`
- `.ai-factory/gates/flange_qc_v2_fqv2_022_dor.json`
- `.ai-factory/qa/flange_qc_v2_fqv2_022_handoff_2026-06-02.md`

## Rules Applied

- One task per branch.
- GitHub issue is source of truth for requirement, acceptance criteria, and
  allowed paths.
- TDD RED/GREEN checkpoints were used before implementation.
- Handoff contracts are metadata-only and do not ingest datasets or execute
  model code.
- No raw media, raw datasets, customer data, notebooks, model weights, model
  deserialization, ONNX/PyTorch/TensorRT execution, training code, GPU/hardware
  validation, MLOps promotion, production release/deploy, secrets, destructive
  migration, product spec approval, QC/SOP tolerance approval, production
  PASS/NG authority, or production auto-reject is introduced.

## Implementation Notes

- Added `DatasetHandoffManifest` for sanitized dataset snapshot metadata.
- Added `EvaluationHandoffReport` for offline metric and latency evidence.
- Added `validate_evaluation_against_dataset()` to ensure eval reports match
  the dataset snapshot and declared label slices.
- Dataset validator requires `dataset://` snapshot refs, approved storage refs,
  labels, point-in-time split policy, positive train/validation/test counts,
  `privacy_class=sanitized_metadata_only`, no PII/customer data, no raw media,
  and no production authority.
- Evaluation validator requires approved model ref, matching dataset ref,
  precision/recall/F1, slice metrics, p95 latency within budget,
  `promotion_decision=not_approved`, and no production authority.
- Added docs explaining the owner/MLOps handoff boundary.

## Tests Run

- RED: `python3 -m unittest tests.flange_qc_v2.test_mlops_handoff -v` failed
  because `apps.flange_qc_v2.mlops_handoff` did not exist.
- GREEN: `python3 -m unittest tests.flange_qc_v2.test_mlops_handoff -v`
- `python3 -m unittest discover -s tests/flange_qc_v2 -v` passed, 101 tests.
- `python3 -m compileall -q apps/flange_qc_v2 tests/flange_qc_v2` passed.
- `python3 scripts/product-ci/run_product_checks.py` passed.
- `python3 -m unittest discover -s tests -v` passed, 196 tests.
- `git diff --check` passed.

## Residual Risks

- Dataset preparation, labeling operations, training, model registry, promotion
  criteria, privacy controls, and model rollback remain future MLOps work.
- Physical camera is still unavailable and live hardware validation is not run.
- Product specs, QC/SOP tolerances, model approval, and production release
  remain human-gated.

## Rollback

Revert the FQV2-022 PR to remove dataset/eval handoff schemas, validators,
tests, docs, and gate evidence. No production data migration, release rollback,
model rollback, or hardware rollback is required.

## Memory Candidate

- memory_type: implementation_lesson
- content: Flange QC v2 dataset/model preparation should hand off sanitized
  dataset manifests and evaluation reports before any raw data, training code,
  or model runtime is introduced.
- source_ref: https://github.com/namlogan/MIL/issues/101
- why reusable: Future MLOps tasks can use these contracts to validate dataset
  snapshots, split policy, labels, metrics, slices, and latency evidence before
  model integration.
- scope: project:flange_qc_v2
- suggested status: candidate
