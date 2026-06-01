# wm_architecture_review

Purpose: gate a new project after bootstrap docs and before implementation.

Checks:
- System boundaries are clear.
- Runtime, workflow, memory, data, deployment, and observability layers are
  separated.
- Public API, event, payload, database, and job contracts are listed.
- Security model, integration points, rollback strategy, and non-goals are
  documented.
- Major decisions have ADR coverage.

Output: `ARCHITECTURE_READY` or `ARCHITECTURE_BLOCKED`.
