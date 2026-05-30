# Windmill Flow: plan_to_pr

Trigger:

```text
approved issue_to_plan run
GitHub issue label: agent:build
```

Steps:

1. Create branch `agent/<issue-id>-<slug>`.
2. Run Codex implementation worker with the approved plan.
3. Run focused tests.
4. Run Auggie advisory review when useful.
5. Commit scoped changes.
6. Push branch.
7. Open pull request using `.github/PULL_REQUEST_TEMPLATE.md`.
8. Attach plan, evidence, and residual risks.

Stop conditions:

- implementation touches out-of-scope files
- tests cannot run and no evidence explains why
- restricted change is detected

