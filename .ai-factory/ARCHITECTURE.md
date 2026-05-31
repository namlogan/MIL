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
Codex worker + Augment context + mem0 memory
        |
        | context retrieval, sanitized memory lookup, plans, implementation, reviews, QA evidence
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

Codex owns scoped implementation. `f/mil/plan_to_pr` prepares the real dispatch
artifact, including scoped memory and read-only Augment MCP context requests,
then calls `f/mil/codex_worker` to build the Windmill command pack.
`scripts/agent-flow/codex_worker.py` runs `codex exec` in an isolated worktree
when execution is explicitly enabled. It writes code and tests only inside
issue-approved scope.

Local auto execution is owned by `scripts/agent-flow/auto_dispatcher.py`. The
public relay can launch it only when `MIL_AUTO_DISPATCH_ENABLED=1` and the
GitHub task explicitly uses `agent:auto-build` or `/agent autobuild`.

Rules follow the AI Factory 2.x hierarchy: `paths.rules_file` for universal
axioms, `rules.base` for project conventions, and named `rules.<area>` files for
implementation, quality gates, security, memory, and Windmill behavior.

Augment owns codebase index and context retrieval for Codex sessions. Auggie may provide supervised advisory review and diagnosis, but it is not a coding worker and does not replace final QA or branch protection.

Mem0 owns optional long-term project/task memory. It stores sanitized operational summaries only and must not store secrets, raw customer data, raw transcripts, or merge approvals.

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
scripts/agent-flow/codex_worker.py
f/mil/plan_to_pr.py
f/mil/plan_to_pr_contract.py
f/mil/codex_worker.py
f/mil/codex_worker_contract.py
```

Run `python3 scripts/ai-factory/bootstrap_runtime.py --check` before treating the local factory as ready.
