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

## AI Delivery Coordinator Mode

Routine agent delivery is coordinated by `ai_delivery_coordinator`. The
coordinator checks Definition of Ready, applies `agent:auto-build` to ready
routine issues, watches worker PRs, requests Codex QA, applies
`automerge:candidate` to routine PRs, and lets GitHub auto-merge proceed after
`control-plane`, `ai-gate/final-review`, and `merge-controller-policy` pass.

Routine PRs do not require owner review. The owner is escalated only for
restricted changes, production release, QC/SOP or product tolerance approval,
policy exceptions, explicit hold labels, or auto-fix loops beyond the configured
limit.

## New Project Startup Pipeline

Use `docs/runbooks/new_project_startup_pipeline.md` when applying the framework
to a new repo or product. The startup sequence is:

```text
Project Intake
-> Memory Preflight
-> Bootstrap Docs
-> Architecture / ADR Gate
-> Contract & Backlog Gate
-> Repo + CI Bootstrap
-> Agent Delivery Loop
-> QA / Review / Merge Gate
-> Release / Rollback Gate
-> Operate / Learn / Memory Maintenance
```

The key constraint is timing: implementation starts only after project intake,
source-of-truth docs, architecture baseline, minimum contracts, backlog slicing,
and CI baseline are ready.

## Windmill Flow Map

- `wm_project_intake_gate`: validates intake completeness before bootstrap.
- `wm_project_bootstrap`: creates the initial framework pack for a new project.
- `wm_project_readiness_score`: reports whether the project is ready for agents.
- `wm_ai_delivery_coordinator`: routes routine ready work and escalates only
  exceptions.
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

The framework can automate routine routing, checks, reports, evidence
collection, PR labeling, and auto-merge candidacy. GitHub branch protection and
`merge-controller-policy` handle routine merge approval. Human approval remains
mandatory for restricted escalation, QC/SOP authority, and production release
ownership.
