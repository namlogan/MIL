# MIL Windmill Cockpit

This directory describes the Windmill cockpit layer for MIL.

Windmill responsibilities:

- receive GitHub webhooks
- dispatch exactly one coding agent for approved implementation work
- run planning, implementation, review, QA, and fix flows
- route jobs to least-privilege worker groups
- prepare scoped Codex worker command packs through `f/mil/codex_worker`
- store logs and artifacts
- retrieve and write sanitized project memory through the mem0 memory contract
- request human approval for restricted or release actions
- publish PR comments and status checks
- schedule the merge-controller dry-run or execute command on the local control station

Windmill must not become the source of truth for issue scope, PR state, or merge approval. GitHub remains the source of truth and branch protection remains the hard merge boundary.

Mem0-backed memory is optional context only. Windmill may call memory retrieval or sanitized writeback, but memory output must not approve merges, reinterpret gate policy, or bypass required GitHub status checks.

Initial implementation should import these flow contracts into Windmill after the GitHub remote and tokens exist.

See [Windmill setup](../docs/windmill-setup.md) for required secrets, webhooks, and GitHub Check payload handling.

The executable Windmill CLI project lives at:

```text
wmill.yaml
wmill-lock.yaml
f/mil/*.py
f/mil/*.script.yaml
```

Memory-specific Windmill entrypoints:

```text
f/mil/memory_contract
f/mil/mem0_retrieve
f/mil/mem0_writeback
```

`mem0_retrieve` builds strict scoped filters and a compact context pack.
`mem0_writeback` validates provenance, redacts secrets, enforces approval
policy, and emits a Mem0 add payload.

Merge controller entrypoint:

```text
f/mil/merge_controller
```

This entrypoint returns the audited command contract for
`scripts/github/merge_controller.py`. Actual GitHub approval/merge execution
requires a separate bot identity and `MIL_MERGE_BOT_TOKEN` in the local control
station or Windmill secret store.

Implementation worker entrypoints:

```text
f/mil/codex_worker_contract
f/mil/codex_worker
```

`codex_worker` is non-executing by default. It returns branch, prompt,
worktree, evidence, and `codex exec` command details for the control plane. The
local runner `scripts/agent-flow/codex_worker.py` performs real execution only
when explicitly invoked with `--execute-agent`.

The Markdown files in this directory remain the human-readable cockpit contracts. The `f/mil/**` scripts are the deployable Windmill entrypoints and are validated by `scripts/windmill/validate_windmill_project.py`.

## Auggie Supervised Advisory

Until Auggie non-interactive CLI mode is enabled, Windmill should use `flows/auggie_supervised_advisory.md` as a queue and audit contract. A local Codex operator starts Auggie through `scripts/agent-flow/auggie_interactive.sh`, verifies the output, and posts evidence back to GitHub.
