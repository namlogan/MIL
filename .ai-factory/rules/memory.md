# Memory Rules

> Area rules for Mem0-backed project memory.

## Rules

- Treat memory as retrieval hints and operational learning only; never as source of truth for requirements, code, PR state, CI, or merge approval.
- Retrieve memory only with strict tenant, repo, task, memory type, status, visibility, and entity-scope filters.
- Store only distilled operational summaries with provenance, confidence, source URI, and approval state when required.
- Never write secrets, raw tokens, raw transcripts, customer data, full proprietary source, or generated patches before review.
- Architecture decisions, human preferences, repo conventions, review rules, and security policy memory require explicit human approval before writeback.
- Every memory context inserted into a worker prompt must be compact and provenance-bearing.
