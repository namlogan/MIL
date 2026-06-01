# Augment Setup For MIL

MIL uses Augment in two separate ways:

1. **Augment MCP context for Codex**: gives Codex codebase index, retrieval, and symbol context.
2. **Auggie supervised advisory**: optional human-in-the-loop review/diagnosis notes.

These are related but not the same. MCP context can work even if Auggie CLI non-interactive worker mode is unavailable. MIL does not use Auggie as a coding worker.

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

## MIL-Scoped Runtime Check

Use this checker to verify that Codex sees the MIL local MCP wrapper and that
the Auggie MCP server indexes `/Users/mac/Documents/MIL`, not another repo:

```bash
python3 scripts/agent-flow/check_mil_mcp_runtime.py --mcp-smoke
```

Expected passing fields:

```text
codex_mcp_list.server_present=true
codex_mcp_list.command_matches_repo=true
mcp_smoke.tool_available=true
mcp_smoke.mil_workspace_indexed=true
```

Current Codex CLI sessions can start `mil-auggie-local/codebase-retrieval`, but
tool-call approval may still cancel the actual retrieval inside nested Codex
sessions. The direct MCP smoke above proves the wrapper, token, tool list, and
MIL workspace index. If nested Codex reports `user cancelled MCP tool call`,
the remaining issue is Codex client/tool approval behavior, not Augment's MIL
workspace scope.

The auto-dispatch path avoids depending on that nested approval layer by
preloading Augment context in the local control-plane process:

```bash
python3 scripts/agent-flow/augment_context_provider.py \
  --query "Find the files involved in the scoped task."
```

The provider calls `mil-auggie-local/codebase-retrieval` directly, converts the
tool result into a compact `augment_context` pack, and passes that pack into
`plan_to_pr` before the Codex worker prompt is built. The nested worker still
receives the read-only MCP request as a fallback/instruction, but it no longer
needs to call MCP successfully to start with useful codebase context.

## Plan-To-PR Context Use

`f/mil/plan_to_pr` now creates an Augment context request before Codex worker
dispatch. The request is read-only and targets:

```text
server: mil-auggie-local
tool: codebase-retrieval
```

The orchestrator injects two things into the Codex worker prompt:

- any preloaded `augment_context` supplied by Windmill or the local control
  plane;
- a read-only Augment MCP query telling Codex what codebase context to retrieve
  before editing.

This lets Codex exploit Augment's codebase index while preserving the MIL role
boundary: Augment/Auggie may inspect and summarize code, but only Codex writes
implementation patches.

## Auggie Non-Interactive Worker

The old unattended worker smoke command is kept only as blocker evidence:

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

MIL no longer requires this mode for coding. If it is enabled later, it may be used only for read-only advisory or context workflows unless the Product Owner explicitly changes this operating model.

## Supervised Interactive Lane

MIL may still use a supervised Auggie advisory lane:

```bash
scripts/agent-flow/auggie_interactive.sh
```

Codex operates the interactive terminal session and runs workspace commands from `.augment/commands/`:

```text
/command mil-morning-triage
/command mil-plan-review issue #<id>
/command mil-pr-review PR #<id>
/command mil-ci-diagnose PR #<id>
/command mil-handoff PR #<id>
```

Windmill may queue and record this work through `.windmill/flows/auggie_supervised_advisory.md`, but it must not pretend this is unattended Auggie automation or coding work.

## Windmill Secrets

Configure these in Windmill secrets, not in repo:

```text
AUGMENT_MCP_TOKEN
AUGMENT_API_TOKEN
AUGMENT_API_URL
AUGMENT_SESSION_AUTH
```

The current credential includes `write` scope. Keep Augment/Auggie usage read-only at the Windmill/tool-permission layer for MIL. Codex is the only coding worker.

## Rotation Note

If an Augment token is pasted into a chat or terminal log, treat it as exposed. After Windmill secrets and local env are configured, rotate the token and update:

- `.env.local`
- Windmill secrets
- any local shell or launch environment that carries the token
