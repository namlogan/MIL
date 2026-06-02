# AI Delivery Coordinator

AI Delivery Coordinator mode is the default routine-delivery posture for MIL.
It prevents the owner from becoming a manual reviewer for every ordinary agent
PR while preserving hard approval boundaries.

## Routine Path

Routine PRs do not ask the owner for manual review.

The coordinator handles routine work like this:

```text
DoR-ready issue
-> label agent:auto-build
-> exactly one Codex worker
-> PR with evidence and rollback
-> Codex QA / ai-gate/final-review
-> label automerge:candidate
-> merge-controller-policy
-> GitHub auto-merge after required checks pass
```

The owner does not need to approve these PRs when they are non-restricted,
within policy limits, and all required checks pass.

## Human Exception Path

The coordinator must escalate to the owner for:

- restricted changes
- production release
- production deploy behavior
- secrets or credential changes
- billing, auth boundary, customer data, legal, or compliance behavior
- destructive migrations
- safety-critical behavior
- QC/SOP or product tolerance approval
- model promotion
- PRs over configured size or policy limits
- explicit `hold`, `owner-review`, `do-not-merge`, `blocked`, or
  `security-review` labels
- more than two auto-fix iterations

## Authority Boundary

The coordinator may label, route, watch checks, request Codex QA, request
auto-fix, and write delivery evidence. It must not author app code, merge main
directly, bypass branch protection, approve restricted changes, approve QC/SOP
tolerances, or approve production release.

GitHub remains the merge authority. `merge-controller-policy` remains the
machine approval status check for routine PRs.
