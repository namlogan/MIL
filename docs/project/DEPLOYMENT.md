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

## Deploy Provider

The framework deploy provider is configured in:

```text
.ai-factory/deploy-provider.json
```

It defaults to disabled manual release until the product app stack and hosting
provider are selected. Validate the config:

```bash
python3 scripts/release/deploy_provider.py
```

Print a staging deploy plan:

```bash
python3 scripts/release/deploy_provider.py --plan --environment staging
```

Command-based providers must use command arrays, not shell strings. Store only
secret names in config, for example `VERCEL_TOKEN`; secret values belong in
Windmill, GitHub Actions, or the local secret store.

## Rollback

Stop the relay or remove the GitHub webhook to halt automation. Revert workflow
changes through protected PRs. Restore a prior backup bundle if a control-plane
upgrade breaks local operation.

## Observability

Use GitHub checks, Windmill job logs, local relay logs, tmux sessions, and
`python3 scripts/operator/daily_status.py` for the daily cockpit.
