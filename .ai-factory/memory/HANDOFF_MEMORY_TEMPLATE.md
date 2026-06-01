# Memory Candidate After Task

- `memory_type`:
- `scope`:
- `project_id`:
- `framework_id`:
- `task_id`:
- `content`:
- `source_ref`:
- `source_type`:
- `why_reusable`:
- `suggested_status`: `candidate`
- `sensitivity`: `internal`
- `confidence`: `low|medium|high`

Rules:

- Do not mark agent-created memory as approved.
- Do not store secrets, raw logs, customer data, raw source, or generated patches.
- Link source evidence such as issue, PR, commit, docs page, CI run, or Windmill run.
