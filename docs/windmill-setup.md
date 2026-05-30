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

GitHub Checks API note:

- `POST /repos/{owner}/{repo}/check-runs` requires GitHub App authentication.
- If Windmill only has a regular GitHub token, use commit statuses as a fallback:

```bash
python scripts/agent-gate/github_status_payload.py \
  --target-url "$PR_URL" \
  .ai-factory/gates/final_gate_result.json
```

Then publish it with:

```text
POST /repos/{owner}/{repo}/statuses/{sha}
```

## Local Flow Harness

Before importing or changing Windmill flows, run the local executable contract:

```bash
python scripts/agent-flow/mil_flow.py --self-test
```

To produce a dry-run artifact for one flow:

```bash
python scripts/agent-flow/mil_flow.py \
  --flow issue_to_plan \
  --task tests/fixtures/agent_task.json \
  --out .ai-factory/gates/sample_issue_to_plan.json
```

The harness verifies expected routing:

```text
issue_to_plan -> codex.plan -> auggie.validate_plan
plan_to_pr -> windmill.dispatch_coding_agent -> codex.implement -> codex.test -> auggie.review
pr_quality_gate -> codex.qa
fix_ci_or_review -> auggie.diagnose -> codex.fix
```

In Windmill, the dry-run adapter should be replaced by worker scripts that call the actual Codex and Auggie CLIs or SDKs with least-privilege credentials.

## CLI Project Setup

Windmill CLI is installed with:

```bash
npm install -g windmill-cli
wmill --version
```

MIL now includes a Windmill CLI project:

```text
wmill.yaml
wmill-lock.yaml
f/mil/*.py
f/mil/*.script.yaml
```

Validate the deployable project files without workspace credentials:

```bash
python3 scripts/windmill/validate_windmill_project.py --self-test
wmill lint .
```

Preview a local script without deploying after a workspace profile is configured:

```bash
wmill script preview f/mil/plan_to_pr \
  -d '{"task":{"task_id":"MIL-LOCAL","checks":["git diff --check"],"restricted_changes":[]}}'
```

With `wmill` CLI 1.712.0, `script preview` still requires an active workspace profile even though it does not deploy.

After a real Windmill workspace exists, bind and dry-run the sync:

```bash
export WINDMILL_TOKEN="..."
export WINDMILL_WORKSPACE_ID="..."
export WINDMILL_BASE_URL="https://app.windmill.dev"
scripts/windmill/bootstrap_workspace.sh
```

Only run `wmill sync push` after the dry-run diff is reviewed and the workspace secrets below are present.

To check whether the local machine has the worker CLIs installed:

```bash
python scripts/agent-flow/check_agent_tools.py
```

This check is intentionally not required in GitHub Actions because cloud runners do not have the local Codex/Auggie worker setup.

## Temporary Fallback

Until branch protection is available for the private repo, Windmill should still comment gate decisions and label PRs. Treat `BLOCKED_NEEDS_HUMAN`, `REQUEST_CHANGES`, and `REJECT` as hard stops by convention.
