# MIL Mem0 Memory Layer

Status date: 2026-05-31.

Mem0 is a useful addition to MIL because it is a long-term memory layer for AI
agents, with add/search operations scoped by identifiers and metadata. The
official project supports Platform, self-hosted, SDK, CLI, and MCP paths:

- GitHub: https://github.com/mem0ai/mem0
- Documentation: https://docs.mem0.ai/
- Memory types: https://docs.mem0.ai/core-concepts/memory-types
- Add memory: https://docs.mem0.ai/core-concepts/memory-operations/add
- Search memory: https://docs.mem0.ai/core-concepts/memory-operations/search

## Role In MIL

MIL uses mem0 as optional project memory, not as an implementation agent and
not as a merge gate.

```text
GitHub Issue/PR -> Windmill route -> Augment context -> mem0 memory lookup
    -> Codex plan/code/QA -> mem0 sanitized writeback -> GitHub protected merge
```

The active runtime agent is `mem0_memory`.

Allowed:

- retrieve project/task memory before planning, implementation, QA, and fix
- store sanitized plan, handoff, QA, merge, CI-pattern, and review-note memory
- summarize repeated failure patterns
- provide memory context to Codex sessions

Forbidden:

- store secrets, raw customer data, raw tokens, or unredacted transcripts
- implement code, create branches, open PRs, approve merge, or merge main
- bypass branch protection or replace GitHub issue/PR state

## What To Store

Store small, durable operational facts:

- accepted plan summaries
- repeated CI failure causes and fixes
- recurring review risks
- merge gate rationale
- environment restore notes
- project-specific operator preferences that are not secrets

Do not store:

- access tokens, API keys, cookies, session dumps, ngrok authtokens
- raw customer data or private datasets
- raw chat transcripts
- production credentials or deployment secrets
- anything that should live only in GitHub issue/PR evidence

## Required Schema

Every memory write must include provenance and scope metadata:

```json
{
  "tenant_id": "org_mil",
  "workspace_id": "engineering",
  "repo": "MIL",
  "repo_id": "github:namlogan/MIL",
  "user_id": "repo:github:namlogan/MIL",
  "agent_id": "codex",
  "run_id": "windmill-job-123",
  "source_uri": "https://github.com/namlogan/MIL/pull/26",
  "confidence": 0.82,
  "status": "active",
  "visibility": "repo",
  "created_by": "agent"
}
```

At least one Mem0 entity scope is required: `user_id`, `agent_id`,
`app_id`, or `run_id`. Retrieval must always include `tenant_id`, `repo_id`,
`memory_type`, `status`, `visibility`, and one entity scope. Global search is
not allowed.

Auto-write memory types:

```text
agent_performance, ci_pattern, developer_handoff, failure_pattern,
incident_learning, merge_gate, operator_note, plan, qa_gate, review_note,
run_summary, tool_failure
```

Approval-required memory types:

```text
architecture_decision, human_preference, repo_convention, review_rule,
security_policy
```

Approval-required memories must include `approved_by` and must be submitted
with the approval flag. The source of truth still remains the linked PR, issue,
ADR, docs page, CI run, or Windmill job.

## Local Test Adapter

The repo includes a deterministic JSONL adapter so CI can test the memory
contract without requiring a Mem0 account:

```bash
python3 scripts/agent-memory/memory_contract.py --self-test
python3 scripts/agent-memory/memory_contract.py add \
  --task-id MEM-001 \
  --memory-type failure_pattern \
  --text "Prior CI failures in this area were caused by non-idempotent retries." \
  --metadata tenant_id=org_mil \
  --metadata workspace_id=engineering \
  --metadata repo=MIL \
  --metadata repo_id=github:namlogan/MIL \
  --metadata user_id=repo:github:namlogan/MIL \
  --metadata source_uri=https://github.com/namlogan/MIL/pull/26 \
  --metadata confidence=0.82 \
  --metadata status=active \
  --metadata visibility=repo \
  --metadata created_by=agent
python3 scripts/agent-memory/memory_contract.py search \
  --query "non-idempotent retries" \
  --tenant-id org_mil \
  --repo-id github:namlogan/MIL \
  --memory-type failure_pattern \
  --user-id repo:github:namlogan/MIL
```

Local runtime memory is written to:

```text
.ai-factory/memory/local_memory.jsonl
```

That file is ignored by git. Keep `.ai-factory/memory/.gitkeep` committed so
the portable directory exists.

## Production Provider

When moving beyond the local adapter, use one of these modes:

- `MEM0_API_KEY`: Mem0 Platform.
- `MEM0_BASE_URL`: self-hosted Mem0 server endpoint.
- `MEM0_ORG_ID` and `MEM0_PROJECT_ID`: optional provider metadata.

Store those values in Windmill or the workstation secret store. Do not commit
them and do not paste them into task memory.

Provider preflight:

```bash
python3 scripts/agent-memory/check_mem0_provider.py
```

Expected modes:

```text
local_jsonl        no external credential; acceptable for first solo pilot
mem0_self_hosted   MEM0_BASE_URL points to Mem0 OSS
mem0_platform      MEM0_API_KEY is present
```

The local CLI lives in `scripts/agent-memory/`; the deployable Windmill memory
contract lives in `f/mil/memory_contract.py`. Windmill entrypoints:

```text
f/mil/mem0_retrieve
f/mil/mem0_writeback
```

Windmill or Codex should call the same logical operations:

```text
retrieve_project_memory
retrieve_plan_memory
retrieve_gate_memory
retrieve_ci_patterns
store_plan_memory
store_handoff_memory
store_qa_memory
store_fix_memory
```

## Verification

Run these checks after changing memory policy:

```bash
python3 scripts/agent-memory/memory_contract.py --self-test
python3 scripts/agent-memory/check_mem0_provider.py --self-test
python3 -m unittest tests.test_memory_contract -v
python3 scripts/ai-factory/bootstrap_runtime.py --check
python3 scripts/agent-gate/validate_ai_factory.py --self-test
```

Expected behavior:

- token-shaped values are redacted before write
- memory records require project, task, provenance, and entity scope
- memory search requires strict metadata filters
- approval-required memory types cannot be written by agents without approval
- unsupported raw memory types are rejected
- mem0 does not appear as a coding, QA, or merge agent
