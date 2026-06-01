# Definition of Done

A task is done when implementation, verification, evidence, and cleanup are all
complete. A merged PR without the required evidence is not done.

## Required Evidence

- GitHub issue or approved local task reference.
- One branch and one PR for the task.
- Developer handoff with files changed, rules applied, tests run, risks, and
  rollback note.
- Required CI, product CI, contract, security, memory, and release checks.
- Codex QA gate decision.
- Human approval for restricted or production-impacting changes.
- Memory candidate or explicit `memory_not_applicable` note.
- Updated docs, contracts, or ADRs when behavior changed.

## Done Decisions

- `DONE_READY_TO_MERGE`: all required checks and evidence are complete.
- `DONE_AFTER_HUMAN_APPROVAL`: restricted work is complete and approved.
- `NOT_DONE_REQUEST_CHANGES`: evidence, tests, or scope are incomplete.
- `BLOCKED_NEEDS_HUMAN`: the task cannot proceed safely without a decision.

## Cleanup

After merge, release writeback may create memory candidates for durable lessons,
but those candidates must remain unapproved until reviewed.
