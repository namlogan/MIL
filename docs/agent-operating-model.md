# MIL Agent Operating Model

MIL uses a controlled AI software factory model.

## Default Flow

```text
issue intake -> Augment context lookup -> plan -> Codex coding-agent dispatch -> implementation branch -> pull request -> CI -> Augment context/advisory review -> Codex QA gate -> human or bot merge
```

Agents may do planning, implementation, review, and CI fixes. They may not bypass branch protection or merge restricted changes without human approval.

## Worker Responsibilities

Codex is the only implementation worker for scoped code changes, tests, refactors, and small CI fixes.

Augment is the codebase context provider for Codex sessions. It exposes indexed repository context, symbol summaries, and retrieval results so Codex can plan, implement, and QA with better local context.

Auggie may provide supervised advisory review, diagnosis, and risk notes when a human/Codex operator starts an interactive session. It is not a developer worker in MIL and must not create branches, edit files, write commits, open PRs, or approve merges.

Windmill is the cockpit that routes work, captures logs, manages retries, and requests human approval.

GitHub is the system of record.

## Auggie Supervised Lane

When a supervised Auggie advisory session is useful, Codex operates the interactive TTY and records evidence.

```text
Windmill queues advisory request -> Codex starts Auggie interactive -> Auggie reviews/diagnoses without code edits -> Codex verifies -> GitHub records evidence
```

Auggie advisory verdicts are limited to:

```text
AUGMENT_REVIEW_PASS
AUGMENT_REVIEW_NOTES
AUGMENT_REVIEW_CHANGES_RECOMMENDED
AUGMENT_REVIEW_BLOCKED
```

Auggie output is advisory evidence only. Augment context retrieval is input context only. Neither replaces Codex implementation, Codex QA, CI, branch protection, human restricted approval, or the final merge gate.

## Gate Philosophy

The gate is intentionally layered:

1. deterministic checks: CI, lint, tests, security scans
2. AI review checks: issue scope, risks, evidence, edge cases
3. GitHub branch protection: required checks and approval enforcement
4. human approval for restricted changes

No single LLM decision is enough to merge critical code.
