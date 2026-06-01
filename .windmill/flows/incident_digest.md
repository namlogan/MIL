# wm_incident_digest

Purpose: turn an incident or failed release into scrubbed operational learning.

Allowed writes:

- `incident_postmortem`
- `deployment_runbook`
- `test_lesson`
- `deprecated_decision`

Rules:

- Strip secrets, customer data, raw logs, raw artifacts, and credentials.
- Store summaries only.
- Link the incident, PR, release, CI run, or Windmill run as `source_ref`.
- Production deploy decisions stay in release gate and human approval.
