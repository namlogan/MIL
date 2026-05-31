# Windmill Flow: fix_ci_or_review

Trigger:

```text
GitHub workflow_run failed
PR label: agent:fix
AI gate decision: REQUEST_CHANGES
```

Steps:

1. Fetch failing CI logs and review blockers.
2. Request Augment codebase context for the failing scope.
3. Ask Codex to diagnose and make a scoped fix.
4. Run focused tests.
5. Push a commit to the same agent branch.
6. Comment what changed and which evidence was rerun.
7. Re-run `pr_quality_gate`.

Limits:

- maximum two automated fix iterations
- no production secrets
- no out-of-scope files without human approval
- Auggie advisory notes may be queued only as supervised read-only context, not as unattended coding work
