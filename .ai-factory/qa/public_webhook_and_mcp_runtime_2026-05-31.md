# Public Webhook And MIL MCP Runtime Evidence

Date: 2026-05-31
Issues: https://github.com/namlogan/MIL/issues/3 and https://github.com/namlogan/MIL/issues/4

## Public Webhook Relay

MIL now includes:

```text
scripts/windmill/github_webhook_public_relay.py
```

Purpose:

- expose only `POST /mil/github-webhook`;
- verify GitHub `X-Hub-Signature-256` before forwarding;
- forward only allowlisted GitHub webhook headers;
- forward signed requests to local Windmill at
  `http://localhost:8090/api/r/admins/mil/github-webhook`.

Local signed relay smoke result:

```text
POST http://127.0.0.1:18091/mil/github-webhook -> HTTP 201
```

The response was a Windmill async job id. The smoke used the same secret value
as Windmill `f/mil/github_webhook_secret` without printing the secret.

Still needed for production automation:

- stable hosted/public URL;
- GitHub webhook configured for `issues`, `pull_request`, `workflow_run`, and
  `issue_comment`;
- no unauthenticated tunnel to the full Windmill UI/API.

## MIL-Scoped Augment MCP

MIL now includes:

```text
scripts/agent-flow/check_mil_mcp_runtime.py
```

Observed runtime check:

```text
codex_mcp_list.server_present=true
codex_mcp_list.command_matches_repo=true
mcp_smoke.tool_available=true
mcp_smoke.mil_workspace_indexed=true
```

Direct Auggie MCP smoke confirms:

- `mil-auggie-local` points to `/Users/mac/Documents/MIL/scripts/agent-flow/auggie_mcp_server.sh`;
- the MCP server exposes `codebase-retrieval`;
- workspace indexing completes for `/Users/mac/Documents/MIL`.

Remaining note:

Nested Codex CLI can start `mil-auggie-local/codebase-retrieval`, but the actual
tool call may still be cancelled by Codex client approval behavior. This is no
longer a repo scope problem; the MIL wrapper and Augment MCP index are scoped to
the correct project.
