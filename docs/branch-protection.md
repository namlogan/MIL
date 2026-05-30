# MIL Branch Protection Guide

Configure this after the GitHub remote exists.

Status as of 2026-05-30:

- Remote exists at `https://github.com/namlogan/MIL`.
- Repository visibility is public by Product Owner approval.
- Initial CI passes on `main`.
- Branch protection is enabled for `main`.
- Required status check: `control-plane`.
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

Initial required checks:

```text
control-plane
```

`ai-gate/final-review` should be added as a required check after Windmill is provisioned and consistently writes the status through the GitHub Checks API or commit status API.

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
