# Definition of Ready

A task may be dispatched to a coding worker only when it is ready. Ready means
the agent can understand scope, risk, tests, and handoff expectations without
inventing missing requirements.

## Required Fields

- Task ID or GitHub issue reference.
- User or business goal.
- Business reason and expected outcome.
- Acceptance criteria that can be checked.
- Source references: PRD, ADR, issue, contract, design, incident, or runbook.
- Allowed files or directories.
- Out-of-scope and restricted areas.
- Expected tests and quality gates.
- Data, replay, fixture, or environment needs.
- Dependencies and blockers.
- Rollback impact.
- Memory preflight query scope.
- Required handoff format.

## Block Conditions

The task is not ready when acceptance criteria are vague, allowed files are
missing, restricted changes are unclear, required contracts do not exist,
security impact is unknown, dependencies are unresolved, or rollback impact is
not stated.

## Required Pre-Dispatch Flows

- `wm_definition_of_ready_check`
- `wm_memory_preflight`
- `wm_task_context_pack`
- `wm_quality_gate_router`

The routing result must say either `READY_FOR_AGENT` or `BLOCKED_NEEDS_HUMAN`.
