# Quality Gate Rules

> Area rules for AI Factory gates, Codex QA, and merge-controller decisions.

## Rules

- Gate output must keep human-readable findings first and append exactly one final `aif-gate-result` JSON block.
- `aif-gate-result` must include `schema_version`, `gate`, `status`, `blocking`, `blockers`, `affected_files`, and `suggested_next`.
- AI Factory 2.x gate status values are lowercase `pass`, `warn`, and `fail`; MIL merge decisions remain `APPROVE_MERGE`, `REQUEST_CHANGES`, `REJECT`, and `BLOCKED_NEEDS_HUMAN`.
- `blocking: true` is allowed only when explicit hard-rule violations, failed required checks, missing required evidence, or restricted-change approval gaps exist.
- Gate checks must inspect issue acceptance criteria, diff scope, required checks, security/restricted triggers, unresolved review threads, memory write policy, and rollback note.
- Final merge remains protected by GitHub branch protection and required status contexts, not by an LLM-only decision.
