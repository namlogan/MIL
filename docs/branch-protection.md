# MIL Branch Protection Guide

Configure this after the GitHub remote exists.

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

