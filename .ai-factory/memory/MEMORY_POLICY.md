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

## Lifecycle

```text
candidate -> reviewed -> approved -> superseded -> retired
```

`needs_review` is used when a conflict is detected and the memory cannot be
trusted until a human or reviewer resolves it.
