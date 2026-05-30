# Agent Worker Smoke Evidence

Date: 2026-05-30
Branch: `agent/1-bootstrap-merge-gate`

## Local Tool Availability

Command:

```bash
python3 scripts/agent-flow/check_agent_tools.py
```

Observed result:

```text
codex available: codex-cli 0.134.0
auggie available: 0.28.0 (commit 63537d73)
```

## Codex Real Invocation

Command:

```bash
codex exec --ephemeral --sandbox read-only -C /Users/mac/Documents/MIL "Return exactly: CODEX_MIL_SMOKE_OK"
```

Observed result:

```text
CODEX_MIL_SMOKE_OK
```

Notes:

- The command ran in read-only sandbox mode.
- Codex printed local config warnings for malformed global agent role files, but the invocation completed successfully.
- Codex printed an MCP shutdown warning because `AUGMENT_MCP_TOKEN` for `auggie_remote` is not set. This does not block the Codex smoke invocation.

## Auggie Real Invocation

Command:

```bash
auggie --print --quiet --output-format json --max-turns 1 --workspace-root /Users/mac/Documents/MIL --rules AGENTS.md "Return exactly: AUGGIE_MIL_SMOKE_OK"
```

Observed result:

```text
CLI non-interactive mode access has been disabled for your account.
```

Verdict:

```text
Auggie CLI is installed, but real non-interactive worker execution is blocked by account policy.
```

Required follow-up:

- Enable Auggie non-interactive mode for the account, or
- Provide an approved Auggie SDK/API token path for Windmill, or
- Treat Auggie as advisory/manual until the account policy changes.

