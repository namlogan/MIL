# ADR-0003: Build App Now, MLOps Parallel Later

## Status

Draft for owner review.

## Context

The intake brief explicitly separates app bootstrap from production model training
and MLOps platform work.

## Decision

Build the app around replay/no-camera, deterministic SOP core, audit storage,
feedback, and detector adapter contracts. MLOps integrates later through approved
model references and evidence.

## Alternatives Considered

- Block app work until model training is complete: rejected because it delays the
  app, audit, HMI, replay, and SOP core.
- Put raw dataset management in the app repo: rejected because data governance
  and model lifecycle need separate source of truth.

## Consequences

The app can provide early operational value and collect shadow feedback while
model work proceeds independently.

## Security And Data Impact

Raw datasets and model weights must not be stored in app repo or Memory0.

## Rollback Or Migration Impact

Model integration can be disabled by returning to stub adapter or shadow-only mode.
