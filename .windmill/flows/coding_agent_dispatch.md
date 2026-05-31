# Windmill Flow: coding_agent_dispatch

Trigger:

```text
approved plan_to_pr request
manual reroute from Merge Controller
failed Codex implementation requiring scoped Codex fix
```

Purpose:

Select and launch the coding agent that will create the implementation branch and PR.

Developer lanes:

- `codex`: the only supported coding lane for implementation, tests, scoped fixes, and PR creation.
- `augment_context`: context/index provider only. It may expose indexed codebase context to a Codex session, but it must not create branches, edit files, write commits, or open PRs.

Steps:

1. Read issue scope, approved plan, labels, and restricted-change notes.
2. Choose the Codex developer lane.
3. Write dispatch evidence with selected agent, branch name, allowed files, tests, and rollback note.
4. Start the selected local worker:
   - Codex worker: local Codex implementation session.
   - Augment context provider: MCP/index lookup only when the Codex session needs codebase context.
5. Require Codex to create or update `agent/<issue-id>-<slug>`.
6. Require a PR before review/gate.
7. Stop after PR readiness; do not auto-merge.

Stop conditions:

- issue lacks required scope or acceptance criteria
- restricted change lacks human approval
- Codex cannot run
- Codex attempts to touch out-of-scope files
- Codex cannot produce test/evidence output
- Augment context provider attempts to act as a coding worker

This flow is the missing coding step between planning and PR review.
