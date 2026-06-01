# wm_sdlc_metrics_report

Purpose: produce an operator SDLC dashboard without changing repo state.

Metrics:
- Lead time issue to merge
- Cycle time by task type
- PR review latency
- Build failure rate
- Rework rate
- Escaped defects
- Rollback count
- Memory conflict count
- Agent handoff quality
- Test flakiness
- Release frequency

Dashboard sections include WIP, blocked tasks, aging PRs, failed gates, releases,
memory candidates waiting review, stale questions, and postmortem actions.
