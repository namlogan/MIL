# Windmill Flow: plan_to_pr

Trigger:

```text
approved issue_to_plan run
GitHub issue label: agent:build
```

Steps:

1. Resolve the approved plan and issue scope.
2. Dispatch exactly one coding agent:
   - default: Codex developer worker
   - optional: supervised Auggie developer worker only when the issue explicitly allows Auggie implementation
3. Create branch `agent/<issue-id>-<slug>`.
4. Run the selected developer worker with the approved plan.
5. Run focused tests.
6. Commit scoped changes.
7. Push branch.
8. Open pull request using `.github/PULL_REQUEST_TEMPLATE.md`.
9. Run Auggie advisory review when useful.
10. Attach plan, implementation evidence, tests, risks, and rollback note.

Stop conditions:

- implementation touches out-of-scope files
- tests cannot run and no evidence explains why
- restricted change is detected
- no coding agent can be dispatched safely
