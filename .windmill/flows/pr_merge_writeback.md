# wm_pr_merge_memory_writeback

Purpose: convert reviewed PR/test/review lessons into candidate or approved
memory after gate evidence exists.

Required gates before approved write:

- tests pass
- review approved
- PR merged or source decision recorded
- `source_ref` is a PR URL, commit hash, docs page, CI run, or Windmill run

Rules:

- Developer agents may propose `memory_candidate` in handoff.
- Gateway may write `implementation_lesson`, `test_lesson`, `review_lesson`,
  `agent_handoff`, or `deprecated_decision`.
- Architecture/security/product rules require explicit approval.
- Writeback must audit the operation.
