# Windmill Flow: pr_quality_gate

Trigger:

```text
GitHub pull_request opened
GitHub pull_request synchronize
manual rerun
```

Steps:

1. Checkout the PR branch.
2. Request Augment codebase context for the PR diff and affected files.
3. Run required CI commands locally if configured.
4. Run Codex QA with AI Factory verify/review/security gates.
5. Parse the last `aif-gate-result` block.
6. Run `scripts/agent-gate/final_gate_check.py`.
7. Publish a GitHub status check named `ai-gate/final-review`.
8. Comment the decision and reasons on the PR.
9. Add `agent:fix`, `blocked`, or `ready-for-human-review` labels as appropriate.

Stop conditions:

- gate result is missing or malformed
- blocking risks are present
- required CI checks fail
- restricted change lacks approval
