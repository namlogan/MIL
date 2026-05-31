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
3. Retrieve scoped mem0 memory for related CI failure patterns.
4. Ask Codex to diagnose and make a scoped fix.
5. Run focused tests.
6. Push a commit to the same agent branch.
7. Store a sanitized fix summary and CI lesson in project memory.
8. Comment what changed and which evidence was rerun.
9. Re-run `pr_quality_gate`.

Limits:

- maximum two automated fix iterations
- no production secrets
- no out-of-scope files without human approval
- no memory writeback containing secrets, raw tokens, or raw transcripts
- Auggie advisory notes may be queued only as supervised read-only context, not as unattended coding work
