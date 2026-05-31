# Windmill Flow: plan_to_pr

Trigger:

```text
approved issue_to_plan run
GitHub issue label: agent:build
```

Steps:

1. Resolve the approved plan and issue scope.
2. Retrieve scoped mem0 memory for related plans, review notes, and CI lessons.
3. Dispatch exactly one coding agent:
   - Codex developer worker is the only supported coding lane.
   - Augment may provide codebase context, but it must not create branches, edit files, commit, or open PRs.
   - mem0 may provide sanitized memory, but it must not write code, commit, open PRs, or approve merge.
4. Create branch `agent/<issue-id>-<slug>`.
5. Run the selected developer worker with the approved plan.
6. Run focused tests.
7. Commit scoped changes.
8. Push branch.
9. Open pull request using `.github/PULL_REQUEST_TEMPLATE.md`.
10. Request Augment review context for the changed scope.
11. Queue supervised Auggie advisory notes only when explicitly requested.
12. Store a sanitized handoff/review summary in project memory.
13. Attach plan, implementation evidence, tests, risks, and rollback note.

Stop conditions:

- implementation touches out-of-scope files
- tests cannot run and no evidence explains why
- restricted change is detected
- no coding agent can be dispatched safely
- memory provider attempts to store secrets or raw transcripts
