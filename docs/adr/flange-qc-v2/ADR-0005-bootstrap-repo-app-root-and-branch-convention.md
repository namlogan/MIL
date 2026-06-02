# ADR-0005: Bootstrap Repo, App Root, And Branch Convention

## Status

Accepted for MVP-0 bootstrap on 2026-06-02.

## Context

The FLANGE kickoff ZIP proposes a `src/flange_qc/**` app root and branch naming
examples that differ from the current MIL control-plane rules. The MIL startup
protocol requires project identity, repo ID, canonical package root, branch
convention, and Definition of Ready evidence before app-code implementation.

The user approved the gate-resolution direction in chat on 2026-06-02.

## Decision

- Use `/Users/mac/Documents/MIL` as the bootstrap repository for MVP-0.
- Set the bootstrap `repo_id` to `MIL/flange-qc-v2-bootstrap`.
- Use `apps/flange_qc_v2/**` as the canonical app root for this bootstrap lane.
- Let the current MIL `AGENTS.md` branch rules override ZIP branch examples.
- Use `agent/fqv2-001-app-skeleton` for the first implementation branch.
- Start implementation with `FQV2-001 App skeleton, health endpoint, CI baseline`.

## Consequences

- `FQV2-001` may create a minimal app package, health endpoint, tests, and
  product-CI checks in the MIL bootstrap repo.
- Draft product specs remain `draft_requires_qc_owner_approval`.
- No production PASS/NG SOP decision logic is approved by this ADR.
- No live camera/hardware validation, model promotion, production deploy, or
  destructive migration is approved by this ADR.
- Future product-repo migration needs a separate ADR or owner-approved issue.

## Source References

- `docs/superpowers/specs/2026-06-02-flange-qc-v2-gate-resolution-design.md`
- `/Users/mac/Desktop/flange_project_kickoff_docs.zip`
- `AGENTS.md`
