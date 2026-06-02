# FLANGE QC App V2 Acceptance Criteria

## Bootstrap Acceptance

- Project identity is recorded.
- PRD, MVP scope, user flows, data model, test strategy, deployment, risks, open
  questions, source-of-truth, and quality gate matrix exist.
- Architecture ADRs define app boundary, SOP-first rule engine, MLOps separation,
  and Windmill/AI Factory/Memory0 boundary.
- Minimum contracts exist for inspection event, Memory0 event, and job manifest.
- Product specs bootstrap config exists and is marked non-production until QC/domain
  owner approval.
- Open critical questions are visible and block coding dispatch.

## App MVP Acceptance

- App starts without camera, GPU, model, or factory data.
- Health endpoint reports DB, storage, config, calibration, camera, and model state.
- Replay source runs E2E.
- Unknown product returns `BLOCKED`.
- Missing or pending calibration returns `BLOCKED`.
- Product-specific tolerance is validated with config, schema, and tests.
- 3 length points, 3 width points, and 2 diagonals are represented in domain contracts.
- Diagonal deviation greater than 0.5 inch returns NG in phase 2.
- Detector returns observations only.
- Missing model produces safe model-dependent states.
- WebSocket payload validates bbox values in `[0, 1]`.
- HMI shows status, reason codes, measurements, calibration, and feedback.
- Audit DB stores inspection, rule, and feedback evidence.
- Release includes rollback pack.
- No secrets, tokens, or fake API keys are committed.
