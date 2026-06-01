# New Project Startup Pipeline

This runbook is the persistent operating rule for starting a new project with
the MIL framework. It is accepted as a good process with one adaptation: any
prior project, including FLANGE, is used only as a lesson source. It is not a
source of truth for the new project.

Git/docs/tests/issues are source of truth. Memory0 is not source of truth.
Memory0 provides approved, scoped context only.

## Pipeline

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

## Stage 1: Project Intake

Collect project name, business objective, primary users, problem statement, MVP
scope, out-of-scope items, preferred stack, security or compliance constraints,
deployment target, success metrics, budget or time constraints, decision owner,
and approver.

Gate: business goal, users, MVP, out-of-scope, deployment target, success
metrics, owner, and critical open questions must be recorded before bootstrap.

## Stage 2: Memory Preflight

Query approved memory by framework, domain, and project scope. The output is a
context pack, not official requirement text. Candidate, stale, superseded, or
unscoped memory must not enter the task prompt. Conflicts must open memory
conflict review.

## Stage 3: Bootstrap Docs

Create `.ai-factory`, `docs/project`, `contracts`, `AGENTS.md`, and startup
evidence from templates. Required project docs include PRD, MVP scope, user
flows, data model, test strategy, deployment, risk register, open questions,
source-of-truth, and quality gate matrix.

Open questions are not requirements until an owner resolves them.

## Stage 4: Architecture / ADR Gate

Create the architecture baseline ADR before implementation. The ADR must lock
system boundaries, runtime components, control-plane components, data flow,
security model, deployment model, observability, rollback strategy,
integration points, and non-goals.

For AI or data projects, lock the MLOps source of truth separately: labels,
datasets, artifacts, experiments, pipelines, and observability must not collapse
into one ambiguous tool.

## Stage 5: Contract & Backlog Gate

Write minimum contracts before coding: API, events, payloads, database
migration policy, memory event schema, and job manifest schema. Then split the
MVP into small vertical slices. Every implementation task requires Definition
of Ready, source references, allowed areas, restricted areas, expected tests,
rollback impact, dependencies, memory preflight, and handoff format.

## Stage 6: Repo + CI Bootstrap

Only after docs and contracts are ready should a repo or module skeleton be
created. Baseline CI must run without camera, GPU, cloud, secret, or production
credential dependencies unless the project explicitly requires them.

The skeleton must include health or smoke tests, contract validation, config
validation, memory event validation, and no real or fake secrets.

## Stage 7: Agent Delivery Loop

Each task follows: context pack -> one assigned Codex worker -> branch -> PR ->
handoff. Branch policy is one task = one branch = one PR = one handoff = one
review.

Agents may propose memory candidates in handoff, but they must not approve
memory directly.

## Stage 8: QA / Review / Merge Gate

Windmill and Codex QA check acceptance criteria, tests, contracts, restricted
areas, handoff, rollback note, and review state. Merge remains protected by
GitHub branch protection and required checks.

After merge, memory writeback may create implementation, test, review, or
deprecated-decision candidates only when the source reference is the merged PR,
commit, doc, release, or incident.

## Stage 9: Release / Rollback Gate

Release requires version or tag, change summary, PR list, migration list,
config diff, artifact versions, test evidence, security notes, known risks,
rollback command, owner approval, and monitoring plan.

Rollback strategy must cover application, database, workflow, and model
rollback when applicable.

## Stage 10: Operate / Learn / Memory Maintenance

After release, track lead time, cycle time, PR review latency, build failure
rate, rework rate, escaped defects, rollback count, memory conflict count, test
flakiness, and open question aging.

Memory maintenance must deduplicate, mark stale records, supersede old
decisions, retire expired task memory, review conflicts, promote useful
candidates, and delete rejected or unsafe memory.

## Five-Day Startup Runbook

Day 0: owner or PM enters intake, readiness score is generated, and critical
open questions are created.

Day 1: memory preflight, project docs, PM/BA review, and architecture baseline
review.

Day 2: ADR-0001, source-of-truth matrix, contracts, and quality gate matrix.

Day 3: repo from golden path template, CI skeleton, Windmill job validation, and
Memory Gateway schema tests.

Day 4: backlog split into vertical slices, issues or jobs created, Definition
of Ready checked, and context packs prepared.

Day 5: first small implementation PRs, QA review, protected merge, and memory
writeback after merge.

## Non-Negotiable Startup Rules

- Do not code before PRD/MVP/Architecture/Test Strategy.
- No implementation task may start before the startup pipeline gates pass.
- Do not create an agent task without Definition of Ready.
- Do not merge without tests, handoff, and review.
- Do not release without rollback.
- Do not write Memory0 without `source_ref`.
- Do not use Memory0 as source of truth.
- Do not let project-specific memory leak into another project.
