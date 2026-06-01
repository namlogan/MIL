# Merge Controller Flow

Purpose: evaluate open PRs and publish the `merge-controller-policy` machine
approval check. GitHub auto-merge merges only after all required checks pass.

Default trigger:

```text
GitHub pull_request opened/synchronize/reopened/ready_for_review/labeled/unlabeled/edited
```

Local command:

```bash
python3 scripts/github/merge_controller.py --scan-open
```

GitHub required-check command:

```bash
python3 scripts/github/merge_controller.py --pr <PR_NUMBER> --policy-only
```

Windmill entrypoint:

```text
f/mil/merge_controller
```

The entrypoint emits the command contract. GitHub Actions is the default
runtime for the required `merge-controller-policy` check.

Required stop conditions:

- `hold`, `owner-review`, `do-not-merge`, `blocked`, or `security-review` label
- draft PR
- missing evidence or rollback note
- restricted path without `owner:auto-approve`
- restricted label without `owner:auto-approve`
