# MIL Branch Protection Guide

Configure this after the GitHub remote exists.

Status as of 2026-05-30:

- Remote exists at `https://github.com/namlogan/MIL`.
- Initial CI passes on `main`.
- Enabling branch protection through the GitHub API returned HTTP 403 because this private repository requires GitHub Pro or public visibility for that feature on the current account.
- Do not make the repository public just to enable protection unless the Product Owner explicitly approves that visibility change.

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
ci / control-plane
ai-gate/final-review
```

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

Fallback until branch protection is available:

- keep `main` changes manual and deliberate
- require agents to work on `agent/*` or `fix/*` branches only
- use PRs even though GitHub cannot hard-enforce them yet
- record gate decisions in PR comments and issues
