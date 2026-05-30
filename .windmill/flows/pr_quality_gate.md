# Windmill Flow: pr_quality_gate

Trigger:

```text
GitHub pull_request opened
GitHub pull_request synchronize
manual rerun
```

Steps:

1. Checkout the PR branch.
2. Run required CI commands locally if configured.
3. Run AI Factory verify/review/security gates.
4. Parse the last `aif-gate-result` block.
5. Run `scripts/agent-gate/final_gate_check.py`.
6. Publish a GitHub status check named `ai-gate/final-review`.
7. Comment the decision and reasons on the PR.
8. Add `agent:fix`, `blocked`, or `ready-for-human-review` labels as appropriate.

Stop conditions:

- gate result is missing or malformed
- blocking risks are present
- required CI checks fail
- restricted change lacks approval

