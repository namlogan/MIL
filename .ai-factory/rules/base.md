# Base Rules

> Project-wide base conventions loaded after `.ai-factory/RULES.md`.

## Rules

- Prefer small, reviewable changes tied to one issue and one branch.
- Preserve GitHub as the source of truth for issues, PRs, CI state, review evidence, and merge decisions.
- Keep AI Factory artifacts command-scoped: rules are owned by rule setup, plans by planning, QA by gate/review, and memory by memory writeback.
- When a task needs broad architecture decisions, produce a plan and request approval before implementation.
- Handoffs must include what changed, why it changed, tests run, risks left, and rollback note.
- Use conventional commits for local checkpoint commits and do not add AI co-author trailers.
