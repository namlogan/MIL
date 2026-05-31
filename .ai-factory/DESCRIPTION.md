# MIL Description

MIL is initialized with an agent-first software delivery workflow.

The repository starts with the control plane before application code:

- GitHub tracks issues, pull requests, CI, and merge history.
- Windmill provides a cockpit for webhooks, approvals, logs, retries, and worker routing.
- AI Factory runtime config defines agents, workflow stages, evidence requirements, environment checks, plans, rules, QA evidence, and machine-readable gate results.
- Codex implements scoped work and test fixes through the `codex_worker` runner.
- Augment provides codebase index and context retrieval for Codex sessions.
- Mem0 provides optional sanitized long-term project/task memory.
- Auggie provides supervised advisory review and diagnosis only; it is not a coding worker.

Application-specific product requirements should be added here once the MIL product scope is defined.
