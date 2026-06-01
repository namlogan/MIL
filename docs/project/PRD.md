# MIL Project Requirements

## Purpose

MIL is an agent-first software delivery control plane for a solo product owner
working with Codex, Windmill, Augment context, and scoped memory.

## Users

- Product owner who writes requirements and approves restricted decisions.
- Codex worker sessions that implement scoped GitHub issues.
- Windmill operator who observes routes, jobs, gates, and retries.

## Problem

One-person software delivery needs a repeatable SDLC loop where AI agents can
work without bypassing requirements, tests, review evidence, or protected merge.

## Goals

- Convert GitHub issues into scoped agent work.
- Produce PRs with evidence and required checks.
- Keep merge authority in GitHub branch protection and human release approval.

## Non-Goals

- Mem0, Augment, or Windmill are not coding or merge agents.
- The framework does not deploy production automatically without approval.

## Requirements

| ID | Requirement | Priority | Acceptance Signal |
|---|---|---|---|
| MIL-REQ-001 | Issue to PR automation | Must | Full smoke creates a PR from a labeled issue |
| MIL-REQ-002 | Protected merge gate | Must | `control-plane` and `ai-gate/final-review` are required |
| MIL-REQ-003 | Portable starter kit | Must | Backup archive and restore runbook exist |

## Risks

Public webhook exposure, agent overreach, stale memory, weak product-specific
CI, and missing release evidence must be controlled before broad production use.
