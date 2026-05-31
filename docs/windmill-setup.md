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

Configure GitHub webhooks to call this Windmill HTTP route:

```text
POST <public-windmill-base-url>/.../mil/github-webhook
```

The exact URL depends on the deployed Windmill base URL and workspace route prefix. The repo-local trigger spec is:

```text
f/mil/github_webhook.http_trigger.yaml
script_path: f/mil/github_webhook_router
route_path: mil/github-webhook
http_method: post
raw_string: true
authentication_method: none
```

GitHub webhook settings:

- Content type: `application/json`
- Secret: value stored in Windmill as `f/mil/github_webhook_secret`
- Events: `issues`, `pull_request`, `workflow_run`, `issue_comment`

The route itself uses `authentication_method: none` so GitHub can call it directly. The Python preprocessor verifies `X-Hub-Signature-256` against the raw body before any MIL flow is routed.

Implemented routing:

- `issues` with label `agent:plan` -> `issue_to_plan`
- `issues` with label `agent:build` -> `plan_to_pr`
- `pull_request.opened`, `pull_request.reopened`, `pull_request.synchronize`, or `pull_request.ready_for_review` -> `pr_quality_gate`
- failed `workflow_run.completed` with PR context -> `fix_ci_or_review`
- successful `workflow_run.completed` with PR context -> `pr_quality_gate`
- issue comment commands `/agent plan`, `/agent build`, `/agent qa`, `/agent gate`, `/agent fix` -> matching flow

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
issue_to_plan -> augment_context.provide_issue_context -> codex.plan
plan_to_pr -> windmill.dispatch_coding_agent -> codex.implement -> codex.test -> codex.open_pr -> augment_context.provide_review_context
pr_quality_gate -> augment_context.provide_gate_context -> codex.qa
fix_ci_or_review -> augment_context.provide_ci_context -> codex.fix
```

In Windmill, the dry-run adapter should be replaced by worker scripts that call Codex for implementation/QA and Augment MCP for codebase context with least-privilege credentials. Auggie remains a supervised read-only advisory lane when explicitly requested; it is not a coding worker.

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
f/mil/folder.meta.yaml
f/mil/*.py
f/mil/*.script.yaml
f/mil/*.script.lock
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

The bootstrap script defaults to a MIL-only dry run:

```bash
wmill sync push --dry-run --includes "f/mil/**"
```

Override `WMILL_SYNC_INCLUDE_PATTERN` only when intentionally deploying a wider Windmill workspace scope.

Only run `wmill sync push` after the dry-run diff is reviewed and the workspace secrets below are present.

## GitHub Commit Status Publisher

MIL includes `f/mil/github_commit_status.py` for publishing `ai-gate/final-review` to the GitHub commit status API from a Windmill worker.

Required Windmill secret variable:

```text
f/mil/github_status_token
f/mil/github_webhook_secret
```

Both variables must be created as `is_secret=true`. For local development, the status token must have permission to write commit statuses for `namlogan/MIL`; production should use a least-privilege GitHub App or fine-grained token instead of a broad developer token.

Smoke run without touching GitHub:

```bash
wmill script run f/mil/github_commit_status \
  -d '{"status":{"owner":"namlogan","repo":"MIL","sha":"<sha>","state":"pending","description":"dry run","target_url":"https://github.com/namlogan/MIL/pull/<n>","dry_run":true}}'
```

Real publish after the secret exists:

```bash
wmill script run f/mil/github_commit_status \
  -d '{"status":{"owner":"namlogan","repo":"MIL","sha":"<sha>","state":"success","description":"APPROVE_MERGE: Windmill gate passed","target_url":"https://github.com/namlogan/MIL/pull/<n>"}}'
```

To check whether the local machine has the worker CLIs installed:

```bash
python scripts/agent-flow/check_agent_tools.py
```

This check is intentionally not required in GitHub Actions because cloud runners do not have the local Codex/Augment worker setup.

## Temporary Fallback

Until branch protection is available for the private repo, Windmill should still comment gate decisions and label PRs. Treat `BLOCKED_NEEDS_HUMAN`, `REQUEST_CHANGES`, and `REJECT` as hard stops by convention.
