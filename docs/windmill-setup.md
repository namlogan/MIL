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

If Windmill is running only on the local control station, do not expose the
full Windmill UI/API through a tunnel. Do not expose the full Windmill UI/API.
Use the repo-local relay instead:

```bash
export MIL_GITHUB_WEBHOOK_SECRET="<same value as Windmill f/mil/github_webhook_secret>"
python3 scripts/windmill/github_webhook_public_relay.py
```

Then point the public tunnel or reverse proxy only at:

```text
http://127.0.0.1:18090/mil/github-webhook
```

The relay:

- accepts only `POST /mil/github-webhook`;
- rejects unsigned or incorrectly signed GitHub deliveries before forwarding;
- forwards only a small allowlist of GitHub webhook headers;
- forwards to local Windmill at `http://localhost:8090/api/r/admins/mil/github-webhook`.

Check non-secret relay configuration:

```bash
MIL_GITHUB_WEBHOOK_SECRET="..." \
  python3 scripts/windmill/github_webhook_public_relay.py --describe
```

For durable automation, use a stable hosted Windmill URL, a stable reverse
proxy, a reserved tunnel domain, or a Cloudflare named tunnel. Ephemeral tunnel
URLs are useful for smoke tests only because GitHub webhooks need a stable URL.

### Stable Cloudflare Named Tunnel

Use this option when Windmill remains local but GitHub needs a stable public
webhook URL. The tunnel must point to the signed local relay, not to the
Windmill UI/API port.

One-time human step on the control station:

```bash
cloudflared tunnel login
```

Log in with a Cloudflare account that controls the DNS zone for the hostname you
want to use, for example `mil-webhook.example.com`.

After login, create or reuse the named tunnel, route DNS, and write the local
runtime config:

```bash
python3 scripts/windmill/setup_cloudflare_named_tunnel.py \
  --hostname mil-webhook.example.com \
  --overwrite-dns
```

The script writes:

```text
.windmill/runtime/cloudflared/mil-github-webhook.yml
.windmill/runtime/cloudflared/mil-github-webhook.json
```

Both files are local runtime artifacts and must not be committed. The generated
Cloudflare config exposes only:

```text
https://mil-webhook.example.com/mil/github-webhook
```

Run the relay without writing the GitHub webhook secret to disk:

```bash
scripts/windmill/run_github_webhook_relay_from_windmill_secret.sh
```

Run the named tunnel:

```bash
cloudflared tunnel --config .windmill/runtime/cloudflared/mil-github-webhook.yml run mil-github-webhook
```

Then configure the GitHub webhook URL:

```text
https://mil-webhook.example.com/mil/github-webhook
```

Use the same GitHub settings listed above: `application/json`, secret
`f/mil/github_webhook_secret`, and events `issues`, `pull_request`,
`workflow_run`, and `issue_comment`.

Smoke test after the GitHub hook exists:

```bash
gh api -X POST repos/namlogan/MIL/hooks/<hook-id>/pings --silent
gh api repos/namlogan/MIL/hooks/<hook-id>/deliveries \
  --jq '.[0] | {event,status,status_code,delivered_at,duration}'
wmill --workspace mil-local job list --json --limit 5
```

Expected result: GitHub delivery status `OK`, HTTP status `201`, and a recent
Windmill job created by `HTTP-f/mil/github_webhook`.

### Stable Endpoint Without Owning A Domain

If you do not have a custom domain, use an ngrok account dev/static domain such
as:

```text
<assigned-name>.ngrok-free.app
<assigned-name>.ngrok-free.dev
```

This still gives GitHub a stable URL, but it does not require buying or moving a
domain to Cloudflare.

One-time human step:

```bash
ngrok config add-authtoken <NGROK_AUTHTOKEN>
```

Then copy the account's static/dev domain from the ngrok dashboard and validate
the MIL endpoint command:

```bash
python3 scripts/windmill/setup_ngrok_static_endpoint.py \
  --domain <assigned-name>.ngrok-free.app
```

Run the relay:

```bash
scripts/windmill/run_github_webhook_relay_from_windmill_secret.sh
```

Run the ngrok endpoint in another terminal:

```bash
ngrok http --url https://<assigned-name>.ngrok-free.app 18090
```

For a longer-running macOS control station, run both processes inside detached
`tmux` sessions:

```bash
tmux new-session -d -s mil-webhook-relay \
  'cd /Users/mac/Documents/MIL && scripts/windmill/run_github_webhook_relay_from_windmill_secret.sh'
tmux new-session -d -s mil-webhook-ngrok \
  'cd /Users/mac/Documents/MIL && ngrok http --url https://<assigned-name>.ngrok-free.app 18090'
tmux ls
```

Use the actual assigned domain; `ngrok-free.dev` works the same way.

Then configure the GitHub webhook URL:

```text
https://<assigned-name>.ngrok-free.app/mil/github-webhook
```

Use the same GitHub settings listed above. The local MIL relay still accepts
only `POST /mil/github-webhook` and still verifies the GitHub HMAC signature
before forwarding to Windmill.

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
issue_to_plan -> augment_context.provide_issue_context -> mem0_memory.retrieve_project_memory -> codex.plan -> mem0_memory.store_plan_memory
plan_to_pr -> mem0_memory.retrieve_plan_memory -> windmill.dispatch_coding_agent -> codex.implement -> codex.test -> codex.open_pr -> augment_context.provide_review_context -> mem0_memory.store_handoff_memory
pr_quality_gate -> augment_context.provide_gate_context -> mem0_memory.retrieve_gate_memory -> codex.qa -> mem0_memory.store_qa_memory
fix_ci_or_review -> augment_context.provide_ci_context -> mem0_memory.retrieve_ci_patterns -> codex.fix -> mem0_memory.store_fix_memory
```

In Windmill, `f/mil/codex_worker` is the implementation worker command-pack
entrypoint. It calls the shared `f/mil/codex_worker_contract` and is mirrored by
the local runner `scripts/agent-flow/codex_worker.py`. Augment MCP provides
codebase context, and mem0 provides sanitized memory with least-privilege
credentials. Auggie remains a supervised read-only advisory lane when
explicitly requested; it is not a coding worker.

Local runner smoke test:

```bash
python3 scripts/agent-flow/codex_worker.py --self-test
python3 scripts/agent-flow/codex_worker.py \
  --repo /Users/mac/Documents/MIL \
  --task tests/fixtures/agent_task.json \
  --dry-run \
  --out /tmp/mil-codex-worker.json
```

Memory retrieval and writeback are deployable Windmill scripts:

```text
f/mil/mem0_retrieve
f/mil/mem0_writeback
```

`mem0_retrieve` refuses unscoped/global search. `mem0_writeback` refuses
missing provenance, missing entity scope, and approval-required memory without
human approval.

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

wmill script preview f/mil/codex_worker \
  -d '{"request":{"task":{"task_id":"MIL-LOCAL","goal":"Prepare a scoped worker run.","acceptance_criteria":["Evidence is produced"],"allowed_files":["docs/**"],"checks":["git diff --check"],"restricted_changes":[]},"options":{"repo_root":"/Users/mac/Documents/MIL"}}}'
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
