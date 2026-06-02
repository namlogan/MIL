# FLANGE QC App V2 MVP Scope

## Release Target

First usable release: a replay-driven, no-camera QC app baseline that proves the
inspection API, deterministic SOP rule engine, audit DB, WebSocket payloads, and
minimal HMI can run outside an agent session.

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
