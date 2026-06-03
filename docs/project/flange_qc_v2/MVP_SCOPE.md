# FLANGE QC App V2 MVP Scope

## Release Target

First usable release: a replay-driven, no-camera QC app baseline that proves the
inspection API, deterministic SOP rule engine, audit DB, WebSocket payloads, and
minimal HMI can run outside an agent session.

## Workstream Status

The replay-driven, no-camera demo-only workstream is frozen as of 2026-06-03.
It remains a regression baseline and rollback path, but it is no longer the
active implementation lane for new work. The active lane is
`machine_vision` real-runtime SOP, tracked in:

```text
.ai-factory/workstreams/flange_qc_v2_machine_vision.json
docs/project/flange_qc_v2/WORKSTREAM_STATUS.md
```

New implementation work must prioritize camera hardware/readiness evidence,
calibration evidence, runtime geometry measurement evidence, product specs and
tolerance approval package, and the full SOP rule gate before advanced model
defect work.

## Must Have

- FastAPI health endpoint and inspection API.
- WebSocket payload contract for HMI updates.
- Product spec config validator and tolerance resolver.
- Deterministic SOP rule registry for geometry and state gates.
- 3-point length and width measurements.
- 2-diagonal validation with deviation threshold of 0.5 inch.
- Calibration contract and synthetic validator.
- SQLite audit persistence for inspections, rule decisions, and feedback.
- Replay frame source and no-camera E2E smoke.
- Detector adapter and stub observations.
- Image quality gate contract.
- Minimal HMI screen.
- Release, rollback, and shadow readiness evidence.

## Should Have

- Hikrobot camera adapter boundary without requiring live hardware in baseline CI.
- Jetson/RTX deployment scaffold after app baseline is green.
- QC feedback contract that produces reviewable shadow-mode evidence.
- Windmill and Memory0 SDLC hook validation for the app repo.

## Later

- Production model training and model promotion pipeline.
- Advanced model defect work after the `machine_vision` camera, calibration,
  geometry, product specs, and full SOP rule gates are recorded.
- MLOps platform implementation.
- Production auto-reject.
- ERP/MES integration.
- Raw dataset management in a separate data/MLOps repo.

## Cut Rules

Do not cut health, replay, audit, product-spec validation, calibration blocking,
or deterministic geometry rules. If time is constrained, defer live camera,
production model, and deployment hardening before cutting any safety gate.

## Definition Of Done

The MVP is acceptable only when replay smoke passes, contracts validate, app
health reports every dependency state, unknown product and missing calibration
block safely, audit evidence exists, rollback is documented, and QC/domain owner
has approved production-bound product specs.
