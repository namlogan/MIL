# MIL User Flows

## Actors

- Product owner: writes goals, approves restricted changes, merges protected PRs.
- Codex worker: plans, edits, tests, commits, pushes, and opens PRs within scope.
- Windmill bot: receives webhook events and routes flows.
- Augment context provider: supplies read-only codebase context.

## Critical Path

1. Product owner creates a GitHub issue with acceptance criteria.
2. Owner adds `agent:auto-build` or comments `/agent autobuild`.
3. GitHub calls the public relay and Windmill router.
4. Windmill preloads memory and Augment context, then dispatches Codex.
5. Codex opens a PR and records evidence.
6. CI and AI gate publish required checks.
7. Owner merges only after branch protection is clean.

## Edge Cases

- Missing allowed files blocks dispatch.
- Restricted changes require human approval.
- Augment context timeout falls back only when the task allows fallback.
- Failed CI routes to the fix flow with capped iterations.

## Screens Or Interfaces

Primary interfaces are GitHub Issues, GitHub PRs, Windmill jobs, local tmux
runtime sessions, and the operator dashboard command.

## Acceptance Scenarios

- Doc-only smoke issue creates and gates a PR.
- Code task runs product CI after product checks are enabled.
- Release gate blocks missing rollback or smoke evidence.
