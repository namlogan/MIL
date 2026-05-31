# MIL Agent Factory Architecture

```text
GitHub Issue / PR / CI
        |
        | webhook, labels, status checks
        v
Windmill cockpit
        |
        | routes work, records logs, requests approval
        v
Codex and Auggie workers
        |
        | plans, implementation, reviews, QA evidence
        v
.ai-factory artifacts
        |
        | final gate result
        v
GitHub branch protection and merge gate
```

## Responsibilities

GitHub remains the system of record. It owns issues, pull requests, branch protection, required checks, review threads, and merge history.

Windmill owns orchestration. It receives GitHub events, starts workers, records logs, manages secrets, enforces retry limits, and asks for human approval.

AI Factory owns workflow artifacts. It defines runtime agent contracts, workflow stages, evidence requirements, rules, plans, QA outputs, and the final machine-readable `aif-gate-result` block.

Codex owns scoped implementation. It writes code and tests only inside issue-approved scope.

Auggie owns advisory context review and diagnosis. It does not replace final QA or branch protection.

## Merge Boundary

The LLM gate may recommend `APPROVE_MERGE`, but it does not merge by itself. GitHub branch protection and required status checks are the hard enforcement layer.

## Runtime Install

The executable install contract lives in:

```text
.ai-factory/runtime/agents.json
.ai-factory/runtime/workflows.json
.ai-factory/runtime/evidence.json
.ai-factory/runtime/environment.json
scripts/ai-factory/bootstrap_runtime.py
```

Run `python3 scripts/ai-factory/bootstrap_runtime.py --check` before treating the local factory as ready.
