# Augment Setup For MIL

MIL uses Augment in two separate ways:

1. **Augment MCP context for Codex**: gives Codex a codebase retrieval tool.
2. **Auggie advisory worker**: validates plans, reviews diffs, and diagnoses hard failures.

These are related but not the same. MCP context can work even if Auggie CLI non-interactive worker mode is unavailable.

## Local Secrets

Local credentials belong in `.env.local`, which is gitignored.

Required local values:

```text
AUGMENT_MCP_TOKEN
AUGMENT_API_TOKEN
AUGMENT_API_URL
AUGMENT_SESSION_AUTH
```

Validate local config without printing secrets:

```bash
python3 scripts/agent-flow/check_augment_config.py
```

## Codex MCP

The global Codex config already has a remote Augment MCP server named `auggie_remote`:

```text
url = "https://api.augmentcode.com/mcp"
bearer_token_env_var = "AUGMENT_MCP_TOKEN"
```

For CLI sessions, run Codex through the MIL env wrapper:

```bash
scripts/agent-flow/run_codex_with_mil_env.sh exec \
  --ephemeral \
  --sandbox read-only \
  -C /Users/mac/Documents/MIL \
  "Use Augment MCP to summarize AGENTS.md"
```

For Codex Desktop, the app process must have `AUGMENT_MCP_TOKEN` in its environment before MCP startup. Do not store the token in repo files or paste it into committed config.

## Local Auggie MCP Wrapper

MIL includes a local wrapper that sources `.env.local` and starts Auggie MCP:

```bash
scripts/agent-flow/auggie_mcp_server.sh
```

You can register it in Codex without storing the token in `~/.codex/config.toml`:

```bash
codex mcp add mil-auggie-local -- /Users/mac/Documents/MIL/scripts/agent-flow/auggie_mcp_server.sh
```

This wrapper is useful when you do not want the Codex process itself to carry the Augment token globally.

## Auggie Worker

The CLI worker smoke command is:

```bash
set -a
source .env.local
set +a
auggie --print --quiet --output-format json \
  --max-turns 1 \
  --workspace-root /Users/mac/Documents/MIL \
  --rules AGENTS.md \
  "Return exactly: AUGGIE_MIL_SMOKE_OK"
```

Current observed result on 2026-05-30:

```text
CLI non-interactive mode access has been disabled for your account.
```

If this remains true, use the Auggie SDK/API route for Windmill advisory review, or keep Auggie as a manual advisory lane until non-interactive access is enabled.

## Windmill Secrets

Configure these in Windmill secrets, not in repo:

```text
AUGMENT_MCP_TOKEN
AUGMENT_API_TOKEN
AUGMENT_API_URL
AUGMENT_SESSION_AUTH
```

The current credential includes `write` scope. Keep review workers read-only at the Windmill/tool-permission layer unless a separate implementation job explicitly requires write access.

## Rotation Note

If an Augment token is pasted into a chat or terminal log, treat it as exposed. After Windmill secrets and local env are configured, rotate the token and update:

- `.env.local`
- Windmill secrets
- any local shell or launch environment that carries the token
