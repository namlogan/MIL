# Memory Rules

> Area rules for Mem0-backed project memory.

## Rules

- Treat memory as retrieval hints and operational learning only; never as source of truth for requirements, code, PR state, CI, release, or merge approval.
- Route all memory access through the Memory Gateway contract; agents must not call Memory0 directly.
- Retrieve memory only with strict tenant, repo, project/framework, memory type, `status=approved`, sensitivity, visibility, and entity-scope filters.
- Store only distilled operational summaries with provenance, confidence, source reference, lifecycle status, and sensitivity.
- Reject secrets, raw tokens, raw transcripts, customer data, full proprietary source, generated patches, raw artifacts, database dumps, model weights, and chain-of-thought.
- Agent-created memory starts as `candidate`; approved memory requires review evidence and an approver.
- Every memory context inserted into a worker prompt must be compact, provenance-bearing, and limited to 5-10 relevant memories.
- If memory conflicts with docs/spec/tests/CI/GitHub evidence, the source-of-truth wins and a memory conflict review must be opened.
- When the local JSONL adapter is active, back up `.ai-factory/memory/*.jsonl` as private runtime memory before cleanup, migration, or project handoff; do not commit it, include it in public starter bundles, or restore it into a different tenant/repo/project scope.
