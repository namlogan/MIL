# FLANGE QC v2 Rollback Drill

Release ID: `flange-qc-v2-shadow-readiness-2026-06-02`
Drill type: documentation and command-path review
Runtime affected: none

## Scope

This drill covers the current readiness pack only. It does not execute staging,
shadow, or production rollback because no staging, shadow, or production deploy
is performed by FQV2-017.

## Rollback Path

1. Stop release promotion. Do not deploy the readiness pack.
2. Revert the FQV2-017 PR if the release readiness evidence itself must be
   removed.
3. Keep `.ai-factory/deploy-provider.json` disabled/manual.
4. Keep `deploy/flange_qc_v2/deploy_plan.json` disabled unless a later release
   issue approves a target runtime.
5. Preserve SQLite audit evidence and QC feedback; do not delete audit data as
   part of rollback.
6. Return the app to replay/shadow-only operation.

## Expected Recovery

- Readiness-pack rollback: normal Git PR revert.
- Runtime rollback after a future deployed release: pending target decision.
- Data recovery: no production data is modified by this pack.
- Hardware recovery: no camera, GPU, or PLC state is modified by this pack.

## Blockers For Production Rollback Approval

- First deployment target is not selected.
- No staging/shadow environment smoke has run.
- No production artifact/version registry exists.
- No hardware live-camera rollback has been validated.
- No product owner release approval exists.

## Result

Rollback path for the current evidence pack is documented and non-destructive.
Production rollback remains unapproved until a real deployment target and human
release approval exist.
