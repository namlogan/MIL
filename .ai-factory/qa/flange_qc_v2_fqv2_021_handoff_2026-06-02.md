# FQV2-021 QA Handoff: MLOps Model Artifact Boundary

## Source

- GitHub issue: https://github.com/namlogan/MIL/issues/99
- Branch: `agent/99-model-artifact-boundary`
- Task: FQV2-021

## Files Changed

- `apps/flange_qc_v2/model_artifact.py`
- `apps/flange_qc_v2/detector.py`
- `apps/flange_qc_v2/health.py`
- `contracts/flange_qc_v2/model/model_artifact_manifest.schema.json`
- `tests/flange_qc_v2/test_model_artifact.py`
- `tests/flange_qc_v2/test_detector_adapter.py`
- `tests/flange_qc_v2/test_health.py`
- `docs/project/flange_qc_v2/MLOPS_BOUNDARY.md`
- `docs/project/flange_qc_v2/DATA_MODEL.md`
- `docs/project/flange_qc_v2/TEST_STRATEGY.md`
- `.ai-factory/gates/flange_qc_v2_fqv2_021_dor.json`
- `.ai-factory/qa/flange_qc_v2_fqv2_021_handoff_2026-06-02.md`

## Rules Applied

- One task per branch.
- GitHub issue is source of truth for requirement, acceptance criteria, and
  allowed paths.
- TDD RED/GREEN checkpoints were used before implementation.
- Model artifact handling is manifest-only and shadow-only.
- No training, dataset ingestion, notebook work, raw media, model weights, model
  deserialization, ONNX/PyTorch/TensorRT execution, GPU/hardware validation,
  model promotion, production release/deploy, secrets, customer data,
  destructive migration, product spec approval, QC/SOP tolerance approval,
  production PASS/NG authority, or production auto-reject is introduced.

## Memory Preflight

- Query: flange_qc_v2 model detector MLOps artifact boundary.
- Retrieved decisions: current detector output is shadow-only and cannot emit
  PASS or NG; MLOps owns dataset management, model training/eval, registry,
  promotion criteria, raw data retention, model rollback, and shadow
  evaluation; app owns detector interface and safe missing/unapproved states.
- Retrieved lessons: integration boundaries should be ready before model
  artifacts arrive; keep raw datasets, weights, secrets, and production
  authority out of scaffold PRs.
- Restricted areas: production release/deploy, secrets/customer data/raw media,
  raw datasets, live camera/hardware validation, model weights, model runtime
  execution, MLOps promotion, destructive migrations, production DB migration
  behavior, QC/SOP tolerance approval, product spec approval, production PASS/NG
  authority.
- Conflicts found: none.
- Sources to verify: issue #99, AGENTS.md, `.ai-factory/RULES.md`,
  `MLOPS_BOUNDARY.md`, `DATA_MODEL.md`, `TEST_STRATEGY.md`, detector adapter,
  and detector tests.

## Implementation Notes

- Added `ModelArtifactManifest` and `load_model_artifact_manifest()`.
- Added JSON schema
  `contracts/flange_qc_v2/model/model_artifact_manifest.schema.json`.
- Manifest validation requires `model.artifact.v1`, registry-style `model_ref`,
  declared labels, safe repository-relative output/eval references, sha256
  digest, approval status, `production_authority=false`,
  `shadow_mode=true`, and `source_ref`.
- Loader rejects raw weight paths by requiring a JSON manifest path before
  reading payload content.
- Added `ManifestDetectorAdapter`, which uses a validated manifest to tag
  review-only observations with `model_ref`.
- Manifest detector rejects observations whose labels are not declared by the
  manifest.
- Detector results remain limited to `NOT_EVALUATED`, `ASSIST`, or `BLOCKED`
  and cannot emit `PASS` or `NG`.
- Health now exposes `model_boundary.state=manifest_ready_shadow_only` with
  approval blockers and no production authority.

## Tests Run

- RED: `python3 -m unittest tests.flange_qc_v2.test_model_artifact -v`
  failed because `apps.flange_qc_v2.model_artifact` did not exist.
- RED: `python3 -m unittest tests.flange_qc_v2.test_detector_adapter -v`
  failed because `ManifestDetectorAdapter` did not exist.
- RED: `python3 -m unittest tests.flange_qc_v2.test_health -v` failed because
  `model_boundary` did not exist.
- GREEN: `python3 -m unittest tests.flange_qc_v2.test_model_artifact -v`
- GREEN: `python3 -m unittest tests.flange_qc_v2.test_detector_adapter -v`
- GREEN: `python3 -m unittest tests.flange_qc_v2.test_health -v`
- `python3 -m unittest discover -s tests/flange_qc_v2 -v` passed, 91 tests.
- `python3 -m compileall -q apps/flange_qc_v2 tests/flange_qc_v2` passed.
- `python3 scripts/product-ci/run_product_checks.py` passed with
  `model_boundary.state=manifest_ready_shadow_only` in the health smoke.
- `python3 -m unittest discover -s tests -v` passed, 196 tests.
- `git diff --check` passed.

## Residual Risks

- No real model artifact, weights, or model registry is connected yet.
- Dataset/MLOps training, evaluation, promotion criteria, and privacy controls
  remain owned by the future MLOps workflow.
- Physical camera is still unavailable and live hardware validation is not run.
- Product specs and QC/SOP tolerances remain unapproved for production-bound
  behavior.
- Production release/deploy remains blocked pending release evidence and human
  approval.

## Rollback

Revert the FQV2-021 PR to remove the manifest contract, manifest loader,
manifest detector adapter, tests, docs, and gate evidence. This task does not
alter production data, destructive migrations, secrets, deploy configuration,
hardware state, raw media, datasets, model weights, model execution, product
spec approval, QC/SOP tolerance approval, or production PASS/NG authority.

## Memory Candidate

- memory_type: implementation_lesson
- content: Flange QC v2 should accept future model integration through a
  shadow-only JSON model artifact manifest before any weights, registry runtime,
  or model execution path is introduced.
- source_ref: https://github.com/namlogan/MIL/issues/99
- why reusable: Future MLOps/model tasks can plug into the app using manifest
  metadata, label declarations, eval references, and model refs while preserving
  safety gates.
- scope: project:flange_qc_v2
- suggested status: candidate
