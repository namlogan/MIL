# Windmill Rules

> Area rules for Windmill orchestration and webhook-driven workers.

## Rules

- Windmill is an orchestrator and audit surface, not the source of truth for requirements or merge approval.
- Windmill may prepare `codex_worker` command packs, dispatch workers, publish statuses, comment on PRs, and request human approval.
- Windmill must not reinterpret gate policy, bypass branch protection, auto-merge code, or continue a worker after PR readiness unless a separate task requires it.
- Windmill write flows must use least-privilege secrets and must not expose token values in logs, memory, prompts, or artifacts.
- GitHub webhook handlers must verify signatures before dispatch and ignore unmatched events without agent calls.
- Public relay or tunnel endpoints must route only the GitHub webhook path into Windmill.
