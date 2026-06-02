# FLANGE QC App V2 User Flows

## Actors

- QC operator: runs or observes inspections and records feedback.
- QC/domain owner: approves SOP interpretation, product specs, and production readiness.
- Engineering/operator: runs replay, validates contracts, monitors audit evidence, and deploys.
- Detector/MLOps provider: supplies model observations through the adapter contract only.

## Critical Path: Replay Inspection

1. Operator or CI starts app in replay mode.
2. App loads runtime config, product specs, calibration state, and detector adapter.
3. Replay source provides frames.
4. Vision preprocessing and geometry measurement produce measurements.
5. Detector adapter returns observations when available.
6. SOP rule engine evaluates product, calibration, geometry, and model-dependent rules.
7. Inspection decision emits PASS, NG, BLOCKED, NOT_EVALUATED, or ASSIST reason codes.
8. Audit DB stores inspection and rule evidence.
9. WebSocket pushes HMI payload to the UI.
10. QC feedback can attach corrections or notes to the inspection evidence.

## Critical Path: Production-Like Shadow Mode

1. Owner approves shadow-mode runbook and rollback plan.
2. App receives replay or live-camera frames in non-authoritative mode.
3. Deterministic rules may produce NG/BLOCKED, but model-dependent rules remain
   advisory unless model promotion is approved.
4. QC feedback is recorded for later MLOps analysis.
5. Release evidence reports observed behavior, false positives, false negatives,
   blocked states, and rollback readiness.

## Edge Cases

- Unknown product code returns `BLOCKED`.
- Missing or pending calibration returns `BLOCKED`.
- Missing detector/model returns `NOT_EVALUATED` for model-dependent rules.
- Invalid bbox outside `[0, 1]` fails contract validation.
- Image quality failure blocks or assists according to configured rule severity.
- Audit DB unavailable makes health degraded and blocks production promotion.

## Interfaces

- HTTP health endpoint.
- HTTP inspection API.
- WebSocket HMI stream.
- SQLite audit DB.
- Product spec JSON config.
- Calibration JSON config.
- Detector adapter interface.
- Replay command-line tool.

## Acceptance Scenarios

- Replay smoke creates an inspection record and WebSocket-compatible payload.
- Unknown product cannot PASS.
- Missing calibration cannot PASS.
- Diagonal deviation above 0.5 inch produces phase 2 NG.
- Missing model does not create production PASS/NG for model-dependent defects.
