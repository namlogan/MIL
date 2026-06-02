# ADR-0004: Windmill, AI Factory, And Memory0 Boundaries

## Status

Draft for owner review.

## Context

The app has realtime inspection behavior and SDLC control-plane behavior. These
must not be mixed.

## Decision

Windmill is SDLC orchestration, AI Factory is governance and gate evidence, and
Memory0 is scoped operational memory. None of them are in the realtime PASS/NG
path.

## Alternatives Considered

- Use Windmill in realtime inspection decisions: rejected because the app needs
  deterministic local runtime behavior.
- Use Memory0 as product requirement source: rejected by MIL policy.

## Consequences

Realtime inspection remains app-owned. Agents still use MIL gates for planning,
implementation, review, and memory writeback.

## Security And Data Impact

Memory0 must not store secrets, raw datasets, raw source, raw logs, or raw
customer/factory data.

## Rollback Or Migration Impact

Disabling Windmill or Memory0 must not stop the app from running replay or local
inspection.
