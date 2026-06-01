# wm_memory_preflight

Purpose: retrieve approved framework, project, and task memory before planning
or implementation.

Inputs:

- `tenant_id`
- `repo_id`
- `project_id` or `framework_id`
- `memory_types`
- one Mem0 entity scope: `user_id`, `agent_id`, `app_id`, or `run_id`

Rules:

- Query through `f/mil/mem0_retrieve`.
- Retrieve only `status=approved`.
- Include `source_ref` for every memory in the context pack.
- If memory conflicts with docs/spec/tests, drop it and create a conflict event.
- Memory0 unavailable must degrade to an empty context pack, not block CI or release.
