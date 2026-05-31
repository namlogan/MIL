# Windmill GitHub Webhook Ingress Evidence

Date: 2026-05-31

## Scope

Issue: https://github.com/namlogan/MIL/issues/4

Implemented repo-local Windmill webhook ingress:

```text
f/mil/github_webhook_router
f/mil/github_webhook
```

## Local Windmill Evidence

- Workspace profile: `mil-local`
- Workspace id: `admins`
- HTTP trigger path: `f/mil/github_webhook`
- HTTP route: `/api/r/admins/mil/github-webhook`
- Routed script: `f/mil/github_webhook_router`
- Trigger mode: `enabled`
- Request type: `async`
- Raw body capture: `raw_string: true`
- HTTP authentication: `none`
- Application authentication: GitHub `X-Hub-Signature-256` verified by script preprocessor
- Windmill secret: `f/mil/github_webhook_secret`, verified as `is_secret=true`

## Smoke Result

Signed local POST to `/api/r/admins/mil/github-webhook` completed on Windmill:

```json
{
  "job_id": "019e7d00-eff1-aa39-3653-d16b47407cd5",
  "success": true,
  "decision": "ROUTED_TO_FLOW",
  "flow": "issue_to_plan",
  "task_id": "MIL-004"
}
```

The smoke payload used the `issues` event, `agent:plan` label, and repository `namlogan/MIL`. The job result routed to `issue_to_plan` and produced the expected Codex plan plus Auggie advisory validation calls in the MIL flow contract.

## GitHub Webhook Status

Not yet configured in GitHub because the current Windmill instance is local-only at `http://localhost:8090`. A real GitHub webhook delivery requires a secure public Windmill URL or a tunnel that exposes only the signed webhook route, not the full local Windmill UI/API.

Required GitHub webhook events remain:

```text
issues
pull_request
workflow_run
issue_comment
```

Use the same secret value stored in `f/mil/github_webhook_secret` when configuring GitHub.
