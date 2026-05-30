# MIL Agent Workflow

Project: MIL
Workflow version: 1
Current mode: GitHub + Windmill cockpit + AI Factory protocol + Codex/Auggie workers

## Source Of Truth

Active source of truth for work:

```text
GitHub Issue -> requirement, acceptance criteria, risk, allowed files
GitHub PR -> implementation diff, CI state, review discussion, merge decision
.ai-factory/** -> local agent rules, plans, QA artifacts, gate contracts
.windmill/** -> cockpit flow definitions and worker policy
```

Windmill is an orchestrator, not the source of truth. AI Factory is the SDLC protocol and artifact layer, not a merge authority.

## Roles

| Role | Main responsibility | May edit app code? |
|---|---|---|
| Product Owner | Business goal, release approval, restricted decisions | No direct code by role |
| Merge Controller | Final gate decision, scope and evidence review | Only for emergency/unblock tasks |
| Codex Developer | Plan, implement, tests, small fixes | Yes, within issue scope |
| Auggie Reviewer / Supervised Developer | Codebase-aware advisory review, diagnosis, risk notes; implementation only when explicitly routed | No by default; yes only with explicit issue routing |
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

## Coding Agent Dispatch

Approved implementation work must dispatch exactly one coding agent before a PR exists.

Default lane:

```text
Windmill coding_agent_dispatch -> Codex Developer -> agent/<issue-id>-<slug> -> PR
```

Optional lane:

```text
Windmill coding_agent_dispatch -> Auggie supervised developer -> agent/<issue-id>-<slug> -> PR
```

The Auggie supervised developer lane is allowed only when the issue explicitly permits Auggie implementation. Codex must operate the Auggie interactive TTY, then independently verify the diff, tests, evidence, and scope before PR gate review.

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
8. If issue instructions conflict with this file or `.ai-factory/RULES.md`, the stricter rule wins unless the Product Owner approves an exception in writing.
