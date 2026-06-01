# MIL Branch Protection Guide

Configure this after the GitHub remote exists.

Status as of 2026-06-01:

- Remote exists at `https://github.com/namlogan/MIL`.
- Repository visibility is public by Product Owner approval.
- Initial CI passes on `main`.
- Branch protection is enabled for `main`.
- Required status checks: `control-plane`, `ai-gate/final-review`, and
  `merge-controller-policy`.
- Pull requests are required.
- Real project mode uses status-check approval. Required approving review count
  should be `0` for solo-owner automation.
- CODEOWNERS review is optional and should not be globally required unless a
  second real reviewer/bot identity is configured.
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

Check the current policy:

```bash
python3 scripts/github/check_branch_protection.py
```

For real project mode, this command must pass without override:

```bash
python3 scripts/github/check_branch_protection.py
```

Zero approving reviews are valid only when `merge-controller-policy` is a
required status check.

Required checks for the current control-plane gate:

```text
control-plane
ai-gate/final-review
merge-controller-policy
```

`ai-gate/final-review` is published automatically by Windmill's GitHub webhook
router after `pr_quality_gate` runs. `merge-controller-policy` is produced by
GitHub Actions from `scripts/github/merge_controller.py --policy-only`. A PR
must have all required contexts on the head commit before protected merge is
allowed.

Add application-specific checks after the product stack exists:

```text
test
lint
typecheck
build
security
```

Auto-merge policy:

- may merge only after GitHub reports required checks passed
- must not use admin bypass
- must not merge PRs with restricted-change labels unless owner approval evidence is recorded
- must not merge PRs with `hold`, `owner-review`, `do-not-merge`, `blocked`, or `security-review`

See [Auto-Merge Gate](merge-controller-bot.md) for the solo-owner
continuous approval model.

Fallback if branch protection must be disabled temporarily:

- keep `main` changes manual and deliberate
- require agents to work on `agent/*` or `fix/*` branches only
- use PRs even though GitHub cannot hard-enforce them yet
- record gate decisions in PR comments and issues
- restore real project protection before dispatching implementation work
