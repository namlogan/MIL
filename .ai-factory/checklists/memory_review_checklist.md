# Memory Review Checklist

Use this before approving a Memory0 candidate.

- [ ] Memory is distilled operational knowledge, not raw transcript or code dump.
- [ ] `source_ref` points to an issue, PR, commit, CI run, release, ADR, or doc.
- [ ] Scope is framework, project, or task.
- [ ] Metadata includes tenant, repo, confidence, status, sensitivity, and actor.
- [ ] Content contains no secrets, tokens, customer data, raw logs, or credentials.
- [ ] Memory does not conflict with source-of-truth docs or tests.
- [ ] Architecture, security, compliance, and product policy memories have human approval.
- [ ] Retrieval filters are scoped before the memory is used in prompts.
