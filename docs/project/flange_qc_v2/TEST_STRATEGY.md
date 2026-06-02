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
- Diagonal deviation greater than 0.5 inch returns NG in phase 2.
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
- Audit DB stores inspection, rule, calibration, and feedback evidence.

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

## Agent Verification Rules

Every implementation issue must list exact checks. If a check cannot run because
the app skeleton does not exist yet, the PR handoff must record that as a blocker
or not-applicable reason. No check may be silently skipped.

## Release Smoke

Release smoke must run the app outside the worker session, execute replay/no-camera
inspection, verify health, confirm audit writes, and attach rollback evidence.
