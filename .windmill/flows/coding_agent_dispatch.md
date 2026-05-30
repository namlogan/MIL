# Windmill Flow: coding_agent_dispatch

Trigger:

```text
approved plan_to_pr request
manual reroute from Merge Controller
failed Codex implementation requiring alternate developer lane
```

Purpose:

Select and launch the coding agent that will create the implementation branch and PR.

Developer lanes:

- `codex`: default implementation, tests, scoped fixes, and PR creation.
- `auggie_supervised`: interactive Auggie developer lane operated by Codex; allowed only when the issue explicitly permits Auggie implementation.

Steps:

1. Read issue scope, approved plan, labels, and restricted-change notes.
2. Choose exactly one developer lane.
3. Write dispatch evidence with selected agent, branch name, allowed files, tests, and rollback note.
4. Start the selected local worker:
   - Codex worker: local Codex implementation session.
   - Auggie supervised worker: `scripts/agent-flow/auggie_interactive.sh` with the relevant `.augment/commands/` prompt.
5. Require the developer worker to create or update `agent/<issue-id>-<slug>`.
6. Require a PR before review/gate.
7. Stop after PR readiness; do not auto-merge.

Stop conditions:

- issue lacks required scope or acceptance criteria
- restricted change lacks human approval
- selected worker cannot run
- selected worker attempts to touch out-of-scope files
- selected worker cannot produce test/evidence output

This flow is the missing coding step between planning and PR review.
