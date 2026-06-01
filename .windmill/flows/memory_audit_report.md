# wm_memory_audit_report

Purpose: produce an audit summary of Memory0 operations for the operator daily
status and release review.

Report fields:

- add/search/update/supersede/retire counts
- memories missing `source_ref`
- candidate memories older than review SLA
- conflicts needing review
- project memory referenced outside its project scope

Rules:

- Audit reports are evidence, not merge approval.
- Do not print secrets or raw memory payloads.
- Link back to source refs and Windmill run IDs.
