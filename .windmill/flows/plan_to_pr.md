# Windmill Flow: plan_to_pr

Trigger:

```text
approved issue_to_plan run
GitHub issue label: agent:build
```

Steps:

1. Resolve the approved plan and issue scope.
2. Dispatch exactly one coding agent:
   - Codex developer worker is the only supported coding lane.
   - Augment may provide codebase context, but it must not create branches, edit files, commit, or open PRs.
3. Create branch `agent/<issue-id>-<slug>`.
4. Run the selected developer worker with the approved plan.
5. Run focused tests.
6. Commit scoped changes.
7. Push branch.
8. Open pull request using `.github/PULL_REQUEST_TEMPLATE.md`.
9. Request Augment review context for the changed scope.
10. Queue supervised Auggie advisory notes only when explicitly requested.
11. Attach plan, implementation evidence, tests, risks, and rollback note.

Stop conditions:

- implementation touches out-of-scope files
- tests cannot run and no evidence explains why
- restricted change is detected
- no coding agent can be dispatched safely
