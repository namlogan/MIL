# MIL External Blockers

Status as of 2026-05-31.

The repo-local agent framework is in place on PR #2, and local tests cover all four specified flow contracts. The remaining items below require account, platform, or credential changes outside the repository.

## GitHub Branch Protection

Tracking issue: https://github.com/namlogan/MIL/issues/5

Current state:

- Repository visibility is public by Product Owner approval.
- `main` exists and CI runs.
- Branch protection is enabled for `main`.
- `control-plane` is required and branches must be up to date.
- Pull requests are required with zero required approvals for the solo-owner pilot.
- Force pushes and branch deletion are disabled.
- Conversation resolution is required.
- `ai-gate/final-review` can be published through the commit status API and is required by branch protection.

Required decision:

- Keep the Windmill publisher healthy so every PR head and merged `main` commit receives `ai-gate/final-review`.

## Augment Context Provider / Auggie Advisory

Tracking issue: https://github.com/namlogan/MIL/issues/3

Current state:

- Auggie CLI is installed.
- `auggie --version` works.
- Non-interactive `auggie --print` execution is blocked by account policy, but this is no longer a blocker for coding because MIL uses Codex as the only coding worker.
- Local Augment credential config can be validated with `scripts/agent-flow/check_augment_config.py`.
- Augment MCP is the desired codebase index/context provider for Codex sessions.
- `scripts/agent-flow/check_mil_mcp_runtime.py --mcp-smoke` verifies that Codex has a `mil-auggie-local` server and that Auggie MCP indexes `/Users/mac/Documents/MIL`.
- Nested Codex sessions may still cancel the actual `codebase-retrieval` call depending on Codex client/tool approval behavior.
- Supervised Auggie interactive review remains optional advisory evidence only; Windmill should queue and record this lane rather than call `auggie --print`.

Required decision:

- Resolve Codex client/tool approval behavior for nested automatic `codebase-retrieval` calls, or keep direct MCP smoke plus Codex file inspection as the fallback.
- Keep Auggie non-interactive as optional future read-only advisory capability, not as a coding worker.

## Windmill Cockpit

Tracking issue: https://github.com/namlogan/MIL/issues/4

Current state:

- Windmill CLI is installed locally as `wmill` and reports version `1.712.0`.
- Repo flow contracts exist under `f/mil/**`.
- Deployable Windmill CLI project files exist in `wmill.yaml`, `wmill-lock.yaml`, and `f/mil/**`.
- `scripts/windmill/validate_windmill_project.py --self-test` validates the Windmill project files without credentials.
- Local dry-run harness exists under `scripts/agent-flow/`.
- Required secret names are documented in `.ai-factory/runtime/environment.json` and `docs/windmill-setup.md`.
- A local Windmill workspace profile `mil-local` targets workspace `admins`.
- `f/mil/github_commit_status` has been imported and has published real `ai-gate/final-review` commit statuses.
- `f/mil/github_webhook_router` and `f/mil/github_webhook.http_trigger.yaml` define the repo-local GitHub webhook ingress.
- `scripts/windmill/github_webhook_public_relay.py` exposes only `POST /mil/github-webhook`, verifies GitHub HMAC signatures before forwarding, and forwards signed deliveries to local Windmill.
- `scripts/windmill/setup_cloudflare_named_tunnel.py` can create or reuse a Cloudflare named tunnel, route DNS, and write the local cloudflared config for the signed relay.
- `scripts/windmill/run_github_webhook_relay_from_windmill_secret.sh` starts the relay by reading `f/mil/github_webhook_secret` from Windmill without storing the secret in repo files.
- `scripts/windmill/setup_ngrok_static_endpoint.py` supports the no-custom-domain fallback with an ngrok account static/dev domain such as `<assigned-name>.ngrok-free.app`.
- A temporary Cloudflare quick tunnel smoke on 2026-05-31 proved GitHub -> public tunnel -> signed relay -> Windmill routing with HTTP 201 and Windmill success jobs.

Required decision:

- If using Cloudflare, complete Cloudflare login on the control station and choose the stable hostname in a Cloudflare-managed zone.
- If no custom domain is available, add an ngrok authtoken locally and provide the assigned static/dev `ngrok-free.app` domain.
- Add the GitHub webhook for `issues`, `pull_request`, `workflow_run`, and `issue_comment` once the stable public URL exists.
- Do not expose the whole local Windmill UI/API through an unauthenticated tunnel.
