# MIL Auto-Merge Gate

MIL uses status-check approval for solo-owner continuous development. It does
not require fake human review for every agent PR.

## Default Flow

```text
Code agent opens PR
-> control-plane CI
-> ai-gate/final-review
-> merge-controller-policy
-> GitHub auto-merge
-> Memory0 post-merge writeback
```

GitHub branch protection is the hard merge boundary. The
`merge-controller-policy` check is the machine approval. Human review is
reserved for restricted or high-risk changes.

## Required Branch Protection

Keep `main` protected with:

```text
Require pull request before merging
Require status checks before merging
Require branches to be up to date
Require conversation resolution
Block force pushes
Block deletion
```

Required checks:

```text
control-plane
ai-gate/final-review
merge-controller-policy
```

Required approving review count should be `0` for this solo-owner automation
model. Restricted owner approval is represented by policy evidence, not by a
fake review.

## Policy

The policy lives in:

```text
.ai-factory/merge-controller.json
```

The evaluator lives in:

```text
scripts/github/merge_controller.py
```

GitHub Actions runs:

```bash
python scripts/github/merge_controller.py --repo "$REPO" --pr "$PR_NUMBER" --policy-only
```

`--policy-only` intentionally ignores other required checks. Branch protection
already enforces those checks independently, which avoids a same-workflow
deadlock.

## Auto-Merge Labels

The AI Delivery Coordinator applies routine auto labels when Definition of Ready,
Codex handoff evidence, Codex QA, rollback, and restricted-change checks are in
place. Agents may propose auto-merge with:

```text
agent:auto-build
automerge:candidate
```

Owner-only approval evidence:

```text
owner:auto-approve
```

Block labels:

```text
hold
owner-review
do-not-merge
blocked
security-review
```

The auto-dispatch path propagates safe allow labels from the source issue to
the generated PR. Restricted labels and paths still require
`owner:auto-approve`.

## Gate Rules

The gate passes only when all are true:

- PR is not draft.
- Base branch is `main`.
- Head branch uses an allowed prefix.
- PR body contains summary, evidence, restricted-change check, and rollback.
- PR size stays below configured limits, unless owner-approved.
- No block labels exist.
- Restricted labels or restricted paths have `owner:auto-approve`.

The gate fails or waits when:

- required PR evidence is missing
- `hold`, `owner-review`, `do-not-merge`, `blocked`, or `security-review` is present
- restricted/high-risk change lacks `owner:auto-approve`
- branch/path policy is violated

## Commands

Evaluate one PR with full local checks:

```bash
python3 scripts/github/merge_controller.py --pr 123
```

Evaluate policy only, matching the GitHub required check:

```bash
python3 scripts/github/merge_controller.py --pr 123 --policy-only
```

Evaluate open PRs locally:

```bash
python3 scripts/github/merge_controller.py --scan-open
```

## Owner Controls

Use these controls when you are busy but want to keep authority:

- Add `hold` to stop all automation.
- Add `owner-review` when you want to read the PR manually.
- Add `security-review` for auth, secrets, billing, customer data, or
  destructive migration changes.
- Add `owner:auto-approve` only after you accept the risk of a restricted path
  or restricted label.

Auto-merge is only for merge into the development branch. Production release
still requires release gate evidence, rollback evidence, and explicit owner
approval.
