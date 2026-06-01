# Memory Policy

Memory0/Mem0 is the project and agent memory layer for MIL. It stores curated
operational learning only. It is not source of truth.

## Source Of Truth Priority

1. Compliance, legal, and security policy
2. Current PRD, spec, SOP, and contract documents
3. Git code and tests
4. Approved ADR
5. Approved memory
6. Candidate memory
7. Conversation context

If memory conflicts with a higher-priority source, agents must ignore the
memory, create a memory conflict event, and route it through Windmill review.

## Gateway Rules

- Agents and workflows must access Memory0 through the Memory Gateway contract.
- Memory writes must include `source_ref`, `scope`, `memory_type`, `status`,
  `sensitivity`, and either `project_id` or `framework_id`.
- Agent-created memory starts as `candidate`.
- Only `approved` memory can enter task context packs.
- `candidate`, `reviewed`, `superseded`, `retired`, and `needs_review` memory
  must not be injected as authoritative context.
- Secrets, credentials, raw proprietary source, raw customer data, raw logs with
  sensitive data, raw artifacts, model weights, database dumps, and
  chain-of-thought are rejected.
- Every add, search, status update, supersede, and retire operation must be
  auditable.

## Runtime Backup

When the local JSONL adapter is active, `.ai-factory/memory/*.jsonl` is private
runtime memory. It is useful for continuing the same project, but it is not
source truth and must not be committed.

- Back up local memory before cleanup, migration, machine handoff, or starting a
  long project run.
- Store the backup in a private backup location, preferably encrypted or under
  the same access controls as project operational notes.
- Restore local memory only into the same `tenant_id`, `repo_id`, `project_id`,
  and repository scope.
- Do not copy MIL runtime memory into a new project starter, public archive, or
  different customer/team workspace.
- After restore, run memory verification before dispatching agents:
  `python3 scripts/agent-memory/check_mem0_provider.py` and
  `python3 scripts/agent-memory/memory_contract.py --self-test`.

## Lifecycle

```text
candidate -> reviewed -> approved -> superseded -> retired
```

`needs_review` is used when a conflict is detected and the memory cannot be
trusted until a human or reviewer resolves it.
