# MIL Delivery Operating Model

This document defines the reusable SDLC operating layer for MIL-style software
delivery. It sits above GitHub, Windmill, Codex workers, Augment context, and
Memory0. It does not replace those systems; it defines when each system is
allowed to act and what evidence is required before moving forward.

## Delivery Loop

1. Project Intake Gate: confirm the project brief, business objective, users,
   MVP scope, out-of-scope items, success metrics, compliance concerns,
   deployment assumptions, open questions, risks, and final decision owner.
2. Project Bootstrap: create the project docs, contracts, CI profile, release
   path, memory namespace, and Windmill flow mapping before agent work starts.
3. Definition of Ready: every task must have a goal, business reason,
   acceptance criteria, source references, allowed and restricted areas,
   expected tests, dependencies, rollback impact, memory preflight, and handoff
   format.
4. Agent Dispatch: Windmill may route only ready work to exactly one coding
   worker. Codex is the implementation worker. Augment is context only.
   Memory0 is memory context only.
5. Quality Gates: checks are selected by change type. Contract, security,
   product CI, memory hygiene, and release checks block merge when required.
6. Definition of Done: a task is done only when code, tests, PR evidence,
   memory candidate handling, rollback note, and final gate evidence are
   complete.
7. Release Gate: local, dev, staging, shadow, and production promotion must use
   a release manifest, smoke evidence, owner approval, rollback command, and
   post-deploy observation plan.
8. Memory Hygiene: Memory0 stores distilled operational memory only. It is
   never the source of truth and never receives secrets, raw source dumps, raw
   transcripts, customer data, or unreviewed architecture policy.
9. Observability: the operator dashboard tracks WIP, blocked items, failed
   gates, review latency, memory conflicts, release readiness, and postmortem
   actions.

## Windmill Flow Map

- `wm_project_intake_gate`: validates intake completeness before bootstrap.
- `wm_project_bootstrap`: creates the initial framework pack for a new project.
- `wm_project_readiness_score`: reports whether the project is ready for agents.
- `wm_definition_of_ready_check`: blocks unclear tasks before dispatch.
- `wm_memory_preflight`: retrieves approved scoped memory before planning.
- `wm_task_context_pack`: compacts docs, memory, and Augment context for Codex.
- `wm_quality_gate_router`: selects required checks by change type.
- `wm_contract_test_gate`: blocks contract drift without explicit evidence.
- `wm_security_gate`: blocks security and secret-risk changes until reviewed.
- `wm_release_candidate_pack`: builds the release evidence bundle.
- `wm_rollback_drill`: verifies rollback is explicit before production.
- `wm_release_memory_writeback`: proposes approved release lessons as memory.

## Operating Principle

The framework can automate routing, checks, reports, and evidence collection.
It must not automate final trust decisions that belong to branch protection,
human approval, restricted escalation, or production release ownership.
