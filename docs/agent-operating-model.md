# MIL Agent Operating Model

MIL uses a controlled AI software factory model.

## Default Flow

```text
issue intake -> plan -> implementation branch -> pull request -> CI -> AI gate -> human or bot merge
```

Agents may do planning, implementation, review, and CI fixes. They may not bypass branch protection or merge restricted changes without human approval.

## Worker Responsibilities

Codex is the default implementation worker for scoped code changes, tests, refactors, and small CI fixes.

Auggie is the advisory reviewer and diagnosis worker for repository-context review, plan validation, hard CI failures, and risk analysis.

Windmill is the cockpit that routes work, captures logs, manages retries, and requests human approval.

GitHub is the system of record.

## Gate Philosophy

The gate is intentionally layered:

1. deterministic checks: CI, lint, tests, security scans
2. AI review checks: issue scope, risks, evidence, edge cases
3. GitHub branch protection: required checks and approval enforcement
4. human approval for restricted changes

No single LLM decision is enough to merge critical code.

