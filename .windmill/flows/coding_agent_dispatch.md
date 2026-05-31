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
- `mem0_memory`: sanitized project/task memory provider only. It may retrieve prior lessons and store summaries, but it must not create branches, edit files, write commits, open PRs, or approve merges.

Steps:

1. Read issue scope, approved plan, labels, and restricted-change notes.
2. Retrieve scoped memory for relevant prior plans, review notes, and CI patterns.
3. Choose the Codex developer lane.
4. Write dispatch evidence with selected agent, branch name, allowed files, tests, and rollback note.
5. Start the selected local worker:
   - Codex worker: `f/mil/codex_worker` prepares the command pack; `scripts/agent-flow/codex_worker.py --execute-agent` runs the local implementation session when explicitly enabled.
   - Augment context provider: MCP/index lookup only when the Codex session needs codebase context.
   - mem0 memory provider: sanitized memory lookup/writeback only.
6. Require Codex to create or update `agent/<issue-id>-<slug>` in an isolated worktree.
7. Validate changed files against `allowed_files` and `out_of_scope_files`.
8. Require a PR before review/gate.
9. Store sanitized handoff/review memory after PR readiness.
10. Stop after PR readiness; do not auto-merge.

Stop conditions:

- issue lacks required scope or acceptance criteria
- restricted change lacks human approval
- Codex cannot run
- Codex attempts to touch out-of-scope files
- Codex cannot produce test/evidence output
- Augment context provider attempts to act as a coding worker
- mem0 memory provider attempts to store secrets or act as a coding worker

This flow is the missing coding step between planning and PR review.
