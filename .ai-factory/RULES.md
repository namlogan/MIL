# MIL AI Factory Rules

AI Factory 2.x-compatible top-level axioms. Area-specific rules live under
`.ai-factory/rules/` and are registered in `.ai-factory/config.yaml`.

Rule priority: `rules.<area> > rules/base.md > paths.rules_file`.

## Rules

- Start work from a GitHub issue or approved local task file.
- Keep one task per branch and keep implementation inside `allowed_files`.
- Codex is the only implementation worker; Augment, Mem0, and Auggie are context, memory, or advisory lanes only.
- Run implementation through the configured `codex_worker` runner or an explicitly approved local equivalent.
- Write tests or record why tests are not applicable.
- Record developer handoff, checks, risks, rollback note, and worker evidence in the PR or `.ai-factory/qa/`.
- Do not dispatch agent work until Definition of Ready is satisfied.
- Do not mark work done until Definition of Done evidence is complete.
- Write or update contracts before implementation when APIs, events, payloads, jobs, database migrations, or memory events change.
- Emit the final machine-readable `aif-gate-result` block after the human summary.
- Allowed MIL merge decisions are `APPROVE_MERGE`, `REQUEST_CHANGES`, `REJECT`, and `BLOCKED_NEEDS_HUMAN`.
- Never merge, deploy, bypass branch protection, or approve restricted work without human approval.
- Never store secrets, raw tokens, customer data, raw proprietary source, or raw transcripts in memory.
- Restricted changes include production deploy behavior, production secrets, billing, customer data retention/deletion, auth boundaries, destructive migrations, legal/compliance behavior, and safety-critical behavior.

## Memory Policy

- Read approved memory before task planning.
- Use memory only as context, never as source of truth.
- If memory conflicts with docs/spec/tests, docs/spec/tests win.
- Do not write approved memory directly from an agent session.
- Propose `memory_candidate` in handoff after completing task.
- Every memory candidate must include `source_ref`.
- Never store secrets, raw data, credentials, private logs, raw artifacts, database dumps, model weights, or chain-of-thought.
- Route all Memory0 add/search/update/supersede/retire operations through the Memory Gateway contract.

## Delivery OS Policy

- Delivery Operating Model, Definition of Ready, Definition of Done, Quality
  Gates, Release Policy, Escalation Policy, and Source of Truth Matrix are
  binding framework rules for agent-runnable work.
- Preferred PR size is below 300 LOC. PRs from 300 to 800 LOC require stronger
  test evidence. PRs above 800 LOC require human approval or splitting.
- Contract changes require `scripts/contracts/validate_contracts.py`.
- Production release requires release manifest, staging smoke evidence,
  rollback drill, monitoring plan, and human approval.

## New Project Startup Pipeline

- No implementation task may start before the startup pipeline gates pass.
- New projects must follow: Project Intake -> Memory Preflight -> Bootstrap
  Docs -> Architecture / ADR Gate -> Contract & Backlog Gate -> Repo + CI
  Bootstrap -> Agent Delivery Loop -> QA / Review / Merge Gate -> Release /
  Rollback Gate -> Operate / Learn / Memory Maintenance.
- Git/docs/tests/issues are source of truth for new project work.
- Memory0 is not source of truth and must not leak project-specific context
  across projects.
- Open questions are not requirements until resolved by an owner in a source of
  truth artifact.
