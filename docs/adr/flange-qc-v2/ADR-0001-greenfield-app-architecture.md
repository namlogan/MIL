# ADR-0001: Greenfield App Architecture

## Status

Draft for owner review.

## Context

The intake brief states the prior FLANGE runtime should be treated as reference
and safety net only. It had major SOP compliance gaps and should not be extended
as the V2 production base.

## Decision

Build FLANGE QC App V2 as a greenfield app with this runtime path:

```text
Replay / Camera
-> Vision preprocessing
-> Geometry measurement + detector observations
-> SOP rule engine
-> Inspection decision
-> Audit DB
-> HMI / WebSocket / QC feedback
```

## Alternatives Considered

- Extend V1 runtime: rejected because the brief reports large compliance gaps.
- Build MLOps first: rejected because the owner wants a real app path first.

## Consequences

V2 can run early with replay, deterministic geometry, and audit evidence. Some
legacy behavior may need deliberate reimplementation after source review.

## Security And Data Impact

The baseline must not require production data, production camera credentials, or
raw dataset access.

## Rollback Or Migration Impact

Rollback is app-level: keep V1 as reference/safety net until V2 is approved.
