# MIL MVP Scope

## Release Target

The MVP is a controlled pilot framework that can run a doc-level and code-level
task through issue intake, Codex implementation, CI, AI gate, and protected PR
merge.

## Must Have

- GitHub Issue and PR as source of truth.
- Windmill webhook routing and job evidence.
- Codex worker dispatch with isolated branch/PR creation.
- Augment context preload before complex Codex work.
- Local memory contract with optional Mem0 provider.

## Should Have

- One-command operator dashboard.
- Product CI hook that can be enabled per app stack.
- Release checklist and release gate evaluator.

## Later

- Hosted Windmill or Cloudflare named tunnel for long-running operation.
- Team-mode branch protection with mandatory human review.

## Cut Rules

Do not cut branch protection, CI, gate evidence, or restricted human approval.
Optional memory and advisory review can be disabled for small pilot tasks.

## Definition Of Done

The framework is acceptable for a new project when intake docs exist, control
plane checks pass, a smoke PR is created by the worker, and release evidence is
recorded before any production rollout.
