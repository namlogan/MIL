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
3. Retrieve scoped mem0 memory for prior QA notes, CI patterns, and merge risks.
4. Run required CI commands locally if configured.
5. Run Codex QA with AI Factory verify/review/security gates.
6. Store a sanitized QA gate summary in project memory.
7. Parse the last `aif-gate-result` block.
8. Run `scripts/agent-gate/final_gate_check.py`.
9. Publish a GitHub status check named `ai-gate/final-review`.
10. Comment the decision and reasons on the PR.
11. Add `agent:fix`, `blocked`, or `ready-for-human-review` labels as appropriate.

Stop conditions:

- gate result is missing or malformed
- blocking risks are present
- required CI checks fail
- restricted change lacks approval
- memory provider attempts to store secrets or raw transcripts
