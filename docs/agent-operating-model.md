# MIL Agent Operating Model

MIL uses a controlled AI software factory model.

## Default Flow

```text
issue intake -> plan -> coding-agent dispatch -> implementation branch -> pull request -> CI -> Auggie advisory review -> Codex QA gate -> human or bot merge
```

Agents may do planning, implementation, review, and CI fixes. They may not bypass branch protection or merge restricted changes without human approval.

## Worker Responsibilities

Codex is the default implementation worker for scoped code changes, tests, refactors, and small CI fixes.

Auggie is the advisory reviewer and diagnosis worker for repository-context review, plan validation, hard CI failures, and risk analysis.

Auggie may also act as a supervised developer worker only when an issue explicitly routes implementation to Auggie. In that case Codex operates the interactive Auggie terminal, then independently verifies the resulting diff, tests, and evidence.

Windmill is the cockpit that routes work, captures logs, manages retries, and requests human approval.

GitHub is the system of record.

## Auggie Supervised Lane

While Auggie CLI non-interactive mode is blocked, Auggie runs through a supervised interactive TTY operated by Codex.

```text
Windmill queues advisory request -> Codex starts Auggie interactive -> Auggie reviews/diagnoses -> Codex verifies -> GitHub records evidence
```

Auggie advisory verdicts are limited to:

```text
AUGMENT_REVIEW_PASS
AUGMENT_REVIEW_NOTES
AUGMENT_REVIEW_CHANGES_RECOMMENDED
AUGMENT_REVIEW_BLOCKED
```

Auggie output is advisory evidence only. It does not replace Codex QA, CI, branch protection, human restricted approval, or the final merge gate.

## Gate Philosophy

The gate is intentionally layered:

1. deterministic checks: CI, lint, tests, security scans
2. AI review checks: issue scope, risks, evidence, edge cases
3. GitHub branch protection: required checks and approval enforcement
4. human approval for restricted changes

No single LLM decision is enough to merge critical code.
