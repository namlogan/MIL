# MIL AI Factory Rules

## Operating Rules

1. Start work from a GitHub issue or approved local task file.
2. Keep one task per branch.
3. Keep implementation inside allowed file scope.
4. Write tests or explain why tests are not applicable.
5. Record evidence in the PR and `.ai-factory/qa/` when useful.
6. Emit a final `aif-gate-result` JSON block for automated gates.
7. Do not merge, deploy, or approve restricted work without human approval.

## Required Gate Result

Gate tools and AI reviewers should end with a fenced block:

````text
```aif-gate-result
{
  "decision": "APPROVE_MERGE",
  "blocking": false,
  "reasons": [],
  "tests": [],
  "residual_risks": []
}
```
````

Allowed decisions:

- `APPROVE_MERGE`
- `REQUEST_CHANGES`
- `REJECT`
- `BLOCKED_NEEDS_HUMAN`

## Restricted Changes

Human approval is required for:

- production deployment behavior
- production secrets or credentials
- billing, payments, or entitlement behavior
- customer data retention or deletion
- authentication and authorization boundaries
- destructive database migrations
- legal, compliance, or safety-critical behavior
