# MIL Agent Operating Model

MIL uses a controlled AI software factory model.

## Default Flow

```text
issue intake -> Augment context lookup -> mem0 memory lookup -> plan -> Codex coding-agent dispatch -> implementation branch -> pull request -> CI -> Augment context/advisory review -> Codex QA gate -> sanitized memory writeback -> human or bot merge
```

Agents may do planning, implementation, review, and CI fixes. They may not bypass branch protection or merge restricted changes without human approval.

## Worker Responsibilities

Codex is the only implementation worker for scoped code changes, tests, refactors, and small CI fixes.

Augment is the codebase context provider for Codex sessions. It exposes indexed repository context, symbol summaries, and retrieval results so Codex can plan, implement, and QA with better local context.

Mem0 is the optional long-term memory provider for sanitized project/task facts. It can retrieve prior plans, gate notes, CI patterns, and review lessons, then store sanitized summaries after each step. It is not allowed to write code, approve merge, bypass branch protection, or store secrets.

Auggie may provide supervised advisory review, diagnosis, and risk notes when a human/Codex operator starts an interactive session. It is not a developer worker in MIL and must not create branches, edit files, write commits, open PRs, or approve merges.

Windmill is the cockpit that routes work, captures logs, manages retries, and requests human approval.

GitHub is the system of record.

## Codex Worker Runner

The deployable dispatch path is `f/mil/plan_to_pr`, which calls
`f/mil/plan_to_pr_contract` and then `f/mil/codex_worker`. The local execution
runner is `scripts/agent-flow/codex_worker.py`.

The runner converts an approved task into:

- a deterministic branch name and isolated worktree
- a scoped prompt built from issue scope, Mem0 memory, and Augment context
- the resolved AI Factory 2.x rule hierarchy from `.ai-factory/config.yaml`
- a `codex exec` command pack
- required checks
- file-scope validation against `allowed_files` and `out_of_scope_files`
- PR evidence under `.ai-factory/qa/codex_worker/<TASK_ID>/`

By default it only returns the command pack. Real `codex exec`, push, and PR
creation require explicit flags. It still cannot merge or approve restricted
changes. If the AI Factory 2.x rule hierarchy cannot be resolved from the repo
or from preloaded `options.rule_sources`, it returns `CODEX_WORKER_BLOCKED`
instead of dispatching a worker. The GitHub webhook route for `agent:build`
preloads a bundled rulepack snapshot before calling `plan_to_pr`, which keeps
hosted Windmill usable even when the repository is not mounted.

`plan_to_pr` always prepares a read-only Augment MCP `codebase-retrieval`
request for the task and passes preloaded Augment context into the Codex worker
prompt when available. Augment remains context-only; Codex still owns the
implementation.

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

## Memory Layer

Mem0-backed memory is scoped by project, task ID, repo ID, tenant ID, and at least one Mem0 entity (`user_id`, `agent_id`, `app_id`, or `run_id`). MIL stores only concise operational facts such as accepted plan summaries, developer handoff summaries, QA gate notes, CI failure patterns, and merge rationale. Raw tokens, customer data, raw transcripts, production credentials, and deployment secrets must not be stored in memory.

Retrieval must use strict filters. Writeback must include source provenance and confidence. Architecture decisions, team preferences, repo conventions, review rules, and security policy memories require human approval and must point back to the source artifact.

## Gate Philosophy

The gate is intentionally layered:

1. deterministic checks: CI, lint, tests, security scans
2. AI review checks: issue scope, risks, evidence, edge cases
3. GitHub branch protection: required checks and approval enforcement
4. human approval for restricted changes

No single LLM decision is enough to merge critical code.
