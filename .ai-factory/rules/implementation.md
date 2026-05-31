# Implementation Rules

> Area rules for Codex implementation work and `codex_worker` sessions.

## Rules

- Run implementation through plan/checkpoint discipline: understand issue scope, apply scoped changes, run checks, then produce handoff evidence.
- `codex_worker` must load issue scope, allowed files, checks, Mem0 context, Augment context, and the AI Factory rule hierarchy before coding.
- Do not edit outside `allowed_files`; if required files are missing from scope, stop and request scope expansion.
- Do not silently continue after restricted changes are detected; return a blocked state before creating commands or edits.
- Use isolated worktrees for unattended implementation so worker state cannot pollute `main`.
- Run required checks from the task payload before commit; if a check cannot run, record the blocker as evidence.
- Keep PRs small enough for review; split unrelated work into separate tasks or branches.
- Update docs only when the task or plan requires docs, or when behavior-facing contracts changed.
