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

## Local Test Adapter

The repo includes a deterministic JSONL adapter so CI can test the memory
contract without requiring a Mem0 account:

```bash
python3 scripts/agent-memory/memory_contract.py --self-test
python3 scripts/agent-memory/memory_contract.py add \
  --task-id MEM-001 \
  --memory-type operator_note \
  --text "Use mem0 as scoped project memory only."
python3 scripts/agent-memory/memory_contract.py search \
  --query "scoped project memory"
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

The integration boundary should stay behind `scripts/agent-memory/`. Windmill
or Codex should call the same logical operations:

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
python3 -m unittest tests.test_memory_contract -v
python3 scripts/ai-factory/bootstrap_runtime.py --check
python3 scripts/agent-gate/validate_ai_factory.py --self-test
```

Expected behavior:

- token-shaped values are redacted before write
- memory records require project and task scope
- unsupported raw memory types are rejected
- mem0 does not appear as a coding, QA, or merge agent
