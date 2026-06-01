# MIL Deployment

## Environments

| Environment | Purpose | Owner | URL Or Runtime |
|---|---|---|---|
| local | Control-plane development | Product owner | Local Windmill and relay |
| pilot | GitHub-driven agent workflow | Product owner | Public relay endpoint |
| production | Future hardened operation | Product owner | Hosted or tunneled Windmill |

## Required Secrets

- Windmill `f/mil/github_webhook_secret`
- Windmill `f/mil/github_status_token`
- Tunnel credential for ngrok or Cloudflare
- Augment local credential
- Optional Mem0 credential

## Deploy Steps

1. Push Windmill scripts with `wmill sync push`.
2. Start the webhook relay and public tunnel.
3. Configure GitHub webhook events.
4. Confirm branch protection required contexts.
5. Run a doc-only smoke issue before app code tasks.

## Rollback

Stop the relay or remove the GitHub webhook to halt automation. Revert workflow
changes through protected PRs. Restore a prior backup bundle if a control-plane
upgrade breaks local operation.

## Observability

Use GitHub checks, Windmill job logs, local relay logs, tmux sessions, and
`python3 scripts/operator/daily_status.py` for the daily cockpit.
