# wm_memory_maintenance

Purpose: keep Memory0 useful across projects without letting stale facts leak
into future work.

Actions:

- deduplicate similar memories
- mark stale memories as `needs_review`
- supersede decisions replaced by newer source-of-truth
- retire expired task memory
- detect conflicts against docs/spec/tests

Rules:

- Maintenance never changes Git, PRs, issues, or release state.
- Supersede/retire operations require `source_ref` and audit records.
- Framework memory must remain separate from project memory.
