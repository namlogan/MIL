# Windmill Setup For MIL

Use this after a Windmill workspace is available.

## Required Secrets

Create these as Windmill secrets or resource variables:

```text
GITHUB_TOKEN_AGENT_READ
GITHUB_TOKEN_AGENT_WRITE
GITHUB_TOKEN_MERGE_BOT
OPENAI_API_KEY
AUGMENT_API_TOKEN
AUGMENT_API_URL
AUGMENT_SESSION_AUTH
```

Use separate GitHub tokens for readonly, write, and merge actions. Do not give implementation workers merge credentials.

## Webhooks

Configure GitHub webhooks to call Windmill routes for:

```text
issues
pull_request
workflow_run
issue_comment
```

Recommended routing:

- `issues` with label `agent:plan` -> `issue_to_plan`
- `issues` with label `agent:build` -> `plan_to_pr`
- `pull_request.opened` or `pull_request.synchronize` -> `pr_quality_gate`
- `workflow_run.failure` or label `agent:fix` -> `fix_ci_or_review`

## GitHub Check Payload

Windmill should use `scripts/agent-gate/github_check_payload.py` to convert final gate JSON into a GitHub Check Run payload.

Example:

```bash
python scripts/agent-gate/github_check_payload.py \
  --head-sha "$PR_HEAD_SHA" \
  .ai-factory/gates/final_gate_result.json
```

Then create a check run through the GitHub Checks API:

```text
POST /repos/{owner}/{repo}/check-runs
```

The check name should be:

```text
ai-gate/final-review
```

## Temporary Fallback

Until branch protection is available for the private repo, Windmill should still comment gate decisions and label PRs. Treat `BLOCKED_NEEDS_HUMAN`, `REQUEST_CHANGES`, and `REJECT` as hard stops by convention.

