# MIL Windmill Cockpit

This directory describes the Windmill cockpit layer for MIL.

Windmill responsibilities:

- receive GitHub webhooks
- run planning, implementation, review, QA, and fix flows
- route jobs to least-privilege worker groups
- store logs and artifacts
- request human approval for restricted or release actions
- publish PR comments and status checks

Windmill must not become the source of truth for issue scope, PR state, or merge approval. GitHub remains the source of truth and branch protection remains the hard merge boundary.

Initial implementation should import these flow contracts into Windmill after the GitHub remote and tokens exist.

See [Windmill setup](../docs/windmill-setup.md) for required secrets, webhooks, and GitHub Check payload handling.

## Auggie Supervised Advisory

Until Auggie non-interactive CLI mode is enabled, Windmill should use `flows/auggie_supervised_advisory.md` as a queue and audit contract. A local Codex operator starts Auggie through `scripts/agent-flow/auggie_interactive.sh`, verifies the output, and posts evidence back to GitHub.
