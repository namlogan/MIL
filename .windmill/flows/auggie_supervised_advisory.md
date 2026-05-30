# Windmill Flow: auggie_supervised_advisory

Trigger:

```text
manual request
GitHub pull_request label: auggie-review-requested
GitHub issue label: auggie-review-requested
failed CI/gate requiring advisory diagnosis
```

Purpose:

Record and route Auggie advisory work while Auggie CLI non-interactive mode is blocked. This flow does not directly run `auggie --print`.

Steps:

1. Read the issue, PR, or failing check target.
2. Create a Windmill job record with target, requested command, and scope.
3. Comment on the issue or PR that Auggie supervised review is queued.
4. Notify the local Codex operator.
5. Codex runs `scripts/agent-flow/auggie_interactive.sh`.
6. Codex invokes the matching Auggie command:
   - `mil-morning-triage`
   - `mil-plan-review`
   - `mil-pr-review`
   - `mil-ci-diagnose`
   - `mil-handoff`
7. Codex verifies Auggie output, tests, and repo state.
8. Codex posts advisory evidence to GitHub using `.ai-factory/qa/auggie_advisory_template.md`.
9. Windmill records the evidence link and clears the queue item.

Stop conditions:

- Auggie authentication or interactive session is unavailable.
- Auggie output does not include an allowed advisory verdict.
- Auggie requests access to production secrets.
- Auggie wants to edit without explicit issue routing.
- Codex verification fails.
- Restricted changes require human approval.

This flow is an audit and queue contract. It is not final QA, branch protection, or merge approval.
