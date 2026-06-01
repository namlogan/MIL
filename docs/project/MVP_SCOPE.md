# MIL MVP Scope

## Release Target

The MVP is a real-project framework that can run doc-level and code-level tasks
through issue intake, Codex implementation, CI, AI gate, mandatory review, and
protected PR merge.

## Must Have

- GitHub Issue and PR as source of truth.
- Windmill webhook routing and job evidence.
- Codex worker dispatch with isolated branch/PR creation.
- Augment context preload before complex Codex work.
- Local memory contract with optional Mem0 provider.
- Branch protection with required status checks and at least one approving
  review for real project mode.

## Should Have

- One-command operator dashboard.
- Product CI hook that can be enabled per app stack.
- Release checklist and release gate evaluator.

## Later

- Hosted Windmill or Cloudflare named tunnel for long-running operation.
- External Mem0 provider if local JSONL memory becomes insufficient for
  multi-machine or multi-project work.

## Cut Rules

Do not cut branch protection, CI, gate evidence, or restricted human approval.
Optional memory and advisory review can be disabled only when the issue says
they are not relevant and the gate records that decision.

## Definition Of Done

The framework is acceptable for a new project when intake docs exist, control
plane checks pass, a smoke PR is created by the worker, and release evidence is
recorded before any production rollout.
