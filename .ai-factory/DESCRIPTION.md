# MIL Description

MIL is initialized with an agent-first software delivery workflow.

The repository starts with the control plane before application code:

- GitHub tracks issues, pull requests, CI, and merge history.
- Windmill provides a cockpit for webhooks, approvals, logs, retries, and worker routing.
- AI Factory runtime config defines agents, workflow stages, evidence requirements, environment checks, plans, rules, QA evidence, and machine-readable gate results.
- Codex implements scoped work and test fixes.
- Auggie provides codebase-aware advisory review and diagnosis.

Application-specific product requirements should be added here once the MIL product scope is defined.
