# MIL

MIL is initialized with an agent-first software delivery control plane.

Current scaffold:

- GitHub is the source of truth for issues, PRs, CI, and merge history.
- Windmill is the cockpit for webhook handling, approvals, logs, retries, and worker routing.
- AI Factory artifacts define rules, plans, QA evidence, and final gate results.
- Codex is the default implementation and test worker.
- Auggie is the advisory review and diagnosis worker.

Start here:

- [Agent workflow](AGENTS.md)
- [Operating model](docs/agent-operating-model.md)
- [Branch protection guide](docs/branch-protection.md)
- [External blockers](docs/external-blockers.md)
- [Augment setup](docs/augment-setup.md)
- [Auggie supervised loop](docs/auggie-human-loop-runbook.md)
- [Windmill coding dispatch](.windmill/flows/coding_agent_dispatch.md)
- [AI Factory rules](.ai-factory/RULES.md)
- [Windmill cockpit notes](.windmill/README.md)
