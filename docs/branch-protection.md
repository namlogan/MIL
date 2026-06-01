# MIL Branch Protection Guide

Configure this after the GitHub remote exists.

Status as of 2026-06-01:

- Remote exists at `https://github.com/namlogan/MIL`.
- Repository visibility is public by Product Owner approval.
- Initial CI passes on `main`.
- Branch protection is enabled for `main`.
- Required status checks: `control-plane` and `ai-gate/final-review`.
- Pull requests are required with zero required approvals for the solo-owner pilot.
- Force pushes and branch deletion are disabled.
- Conversation resolution is required.

Recommended protection for `main`:

- require pull request before merging
- block direct pushes
- block force pushes
- require status checks to pass
- require branches to be up to date before merge
- require conversation resolution
- restrict who can bypass protections
- require signed commits if the project needs stronger provenance

Required checks for the current control-plane gate:

```text
control-plane
ai-gate/final-review
```

`ai-gate/final-review` is published automatically by Windmill's GitHub webhook router after `pr_quality_gate` runs. The router uses `f/mil/github_commit_status` and the GitHub commit status API. A PR must have both required contexts on the head commit before protected merge is allowed.

Add application-specific checks after the product stack exists:

```text
test
lint
typecheck
build
security
```

Merge bot policy:

- may merge only after GitHub reports required checks passed
- must not author implementation commits
- must not merge PRs with restricted-change labels unless human approval is recorded

Fallback if branch protection must be disabled temporarily:

- keep `main` changes manual and deliberate
- require agents to work on `agent/*` or `fix/*` branches only
- use PRs even though GitHub cannot hard-enforce them yet
- record gate decisions in PR comments and issues
