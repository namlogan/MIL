# MIL Agent Workflow

Project: MIL
Workflow version: 1
Current mode: GitHub + Windmill cockpit + AI Factory protocol + Codex workers + Augment context + mem0 memory

## Source Of Truth

Active source of truth for work:

```text
GitHub Issue -> requirement, acceptance criteria, risk, allowed files
GitHub PR -> implementation diff, CI state, review discussion, merge decision
.ai-factory/** -> local agent rules, plans, QA artifacts, gate contracts
.windmill/** -> cockpit flow definitions and worker policy
contracts/** -> contract-first interface skeletons
docs/adr/** -> approved architecture decisions
docs/release/** -> release manifests and approval evidence
```

Windmill is an orchestrator, not the source of truth. AI Factory is the SDLC protocol and artifact layer, not a merge authority.

## Roles

| Role | Main responsibility | May edit app code? |
|---|---|---|
| Product Owner | Business goal, release approval, restricted decisions | No direct code by role |
| Merge Controller | Final gate decision, scope and evidence review | Only for emergency/unblock tasks |
| Codex Developer | Plan, implement, tests, small fixes | Yes, within issue scope |
| Augment Context Provider | Expose codebase index, retrieval, symbol summaries, and context to Codex sessions | No |
| Mem0 Memory Layer | Retrieve and store sanitized project/task memory | No |
| Auggie Advisory Reviewer | Supervised advisory review, diagnosis, and risk notes when explicitly requested | No |
| Codex QA | Final AI QA review and gate evidence | Review/test only |
| Windmill Bot | Run flows, write comments/checks/labels, request approval | No app-code authorship |
| GitHub Bot | Create status checks and merge only when protections pass | No app-code authorship |

## Branch Naming

Use one task per branch.

```text
agent/<issue-id>-<slug>
fix/<issue-id>-<slug>
review/<issue-id>-<slug>
release/<version-or-date>
```

No agent may push directly to `main`.

## Required Issue Fields

Each agent-runnable issue should include:

- task ID or issue number
- user/business goal
- acceptance criteria
- allowed files and out-of-scope files
- required checks
- data or replay evidence, when relevant
- security/restricted escalation check
- rollback note

Before the first agent-runnable issue in a new project, these intake documents
must exist and be specific enough for Codex workers to infer scope and tests:

```text
.ai-factory/DESCRIPTION.md
.ai-factory/ARCHITECTURE.md
.ai-factory/RULES.md
docs/project/PRD.md
docs/project/MVP_SCOPE.md
docs/project/USER_FLOWS.md
docs/project/DATA_MODEL.md
docs/project/TEST_STRATEGY.md
docs/project/DEPLOYMENT.md
```

Validate intake with:

```bash
python3 scripts/project-intake/validate_project_intake.py
```

## Delivery OS Gates

Agent work must follow the repo Delivery Operating System:

```text
project intake -> definition of ready -> context pack -> exactly one Codex worker
-> quality gate router -> contract/security/product checks -> Codex QA
-> protected merge -> release candidate -> rollback drill -> human release approval
```

Required framework documents:

```text
.ai-factory/DELIVERY_OPERATING_MODEL.md
.ai-factory/DEFINITION_OF_READY.md
.ai-factory/DEFINITION_OF_DONE.md
.ai-factory/QUALITY_GATES.md
.ai-factory/RELEASE_POLICY.md
.ai-factory/ESCALATION_POLICY.md
.ai-factory/SOURCE_OF_TRUTH_MATRIX.md
contracts/**
templates/**
```

Validate this layer with:

```bash
python3 scripts/delivery/validate_delivery_os.py --self-test
python3 scripts/contracts/validate_contracts.py --self-test
```

## Required PR Evidence

Before review, the developer agent must attach or reference:

- issue ID
- branch
- files changed
- rules applied
- tests run
- gate artifacts generated
- residual risks
- rollback note
- Definition of Ready and Definition of Done evidence
- contract, security, product, release, or memory gate evidence when routed

## Coding Agent Dispatch

Approved implementation work must dispatch exactly one coding agent before a PR exists.

Default lane:

```text
Windmill coding_agent_dispatch -> Codex Developer -> agent/<issue-id>-<slug> -> PR
```

Augment/Auggie is not a coding lane:

```text
Codex session -> Augment MCP/codebase index -> retrieved context -> Codex plan/implementation/QA
Codex session -> mem0 project/task memory -> sanitized facts -> Codex plan/implementation/QA
```

Codex remains the only implementation worker. Augment may provide indexed codebase context, mem0 may provide sanitized long-term project/task memory, and Auggie may provide supervised advisory notes, but none of those context/review lanes may create branches, edit files, write commits, open PRs, or approve merges.

## Memory Preflight

Every agent-runnable task must document the memory preflight in the plan or
handoff:

- Query:
- Retrieved decisions:
- Retrieved lessons:
- Restricted areas:
- Conflicts found:
- Sources to verify:

Use approved memory only. If memory conflicts with GitHub issues, PRD/spec,
docs, tests, CI, or audit evidence, the source-of-truth wins and the memory must
be routed to conflict review.

## Memory Candidate After Task

Agents may propose a memory candidate after useful work, but must not mark it
approved:

- memory_type:
- content:
- source_ref:
- why reusable:
- scope:
- suggested status: candidate

Do not store secrets, raw logs, raw artifacts, raw customer data, raw source,
generated patches, or chain-of-thought.

## Gate Decisions

Final AI gate decisions must use exactly one of:

```text
APPROVE_MERGE
REQUEST_CHANGES
REJECT
BLOCKED_NEEDS_HUMAN
```

The gate decision is advisory until GitHub branch protection and required status checks pass. Production release and restricted changes always require human approval.

## Non-Negotiable Rules

1. Agents do not merge `main` directly.
2. Agents do not bypass branch protection, required checks, or human approval gates.
3. Windmill write flows must run with least-privilege tokens.
4. Production secrets must not be exposed to planning, implementation, or review agents.
5. Auto-fix loops are limited to two iterations before human review.
6. Every gate result must include decision, reasons, tests, and residual risks.
7. Restricted areas require human approval before merge: production deploy, secrets, billing, customer data, destructive migrations, legal/compliance behavior, security boundaries.
8. Memory must store sanitized operational summaries only; never store raw tokens, secrets, customer data, or raw transcripts.
9. Product-specific CI must be enabled in `.ai-factory/product-ci.json` once app code exists.
10. Release requires CI pass, AI gate pass, staging smoke evidence, rollback plan, monitoring plan, and human approval.
11. If issue instructions conflict with this file or `.ai-factory/RULES.md`, the stricter rule wins unless the Product Owner approves an exception in writing.
