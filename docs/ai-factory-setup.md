# MIL AI Factory Setup

The repo-local AI Factory layer is the SDLC protocol and artifact contract for MIL. It does not replace GitHub as the source of truth and it does not merge code.

## Runtime Files

```text
.ai-factory/config.yaml
.ai-factory/runtime/agents.json
.ai-factory/runtime/workflows.json
.ai-factory/runtime/evidence.json
.ai-factory/runtime/environment.json
scripts/ai-factory/bootstrap_runtime.py
scripts/agent-flow/codex_worker.py
scripts/agent-memory/memory_contract.py
f/mil/codex_worker.py
f/mil/codex_worker_contract.py
f/mil/memory_contract.py
f/mil/mem0_retrieve.py
f/mil/mem0_writeback.py
```

## AI Factory 2.x Rulepack

MIL follows the AI Factory 2.x rule hierarchy:

```text
paths.rules_file -> .ai-factory/RULES.md
rules.base       -> .ai-factory/rules/base.md
rules.<area>     -> .ai-factory/rules/<area>.md
```

Priority is:

```text
rules.<area> > rules/base.md > paths.rules_file
```

Configured area rules:

```text
implementation -> .ai-factory/rules/implementation.md
quality_gates  -> .ai-factory/rules/quality-gates.md
security       -> .ai-factory/rules/security.md
memory         -> .ai-factory/rules/memory.md
windmill       -> .ai-factory/rules/windmill.md
```

`codex_worker` resolves these files from `.ai-factory/config.yaml` and embeds
the active rule sources into the worker prompt before implementation. The
worker fails closed when no rule source is available. For GitHub webhook
`agent:build` dispatch, `f/mil/github_webhook_router` passes a bundled rulepack
snapshot so hosted Windmill can prepare Codex command packs even when the MIL
repo is not mounted. Local callers may still use a mounted `options.repo_root`
or pass pre-resolved `options.rule_sources`.

## Check Install

Run the runtime checker after cloning or changing factory config:

```bash
python3 scripts/ai-factory/bootstrap_runtime.py --check
python3 scripts/agent-memory/memory_contract.py --self-test
python3 scripts/agent-gate/validate_ai_factory.py --self-test
```

The default checker validates required agents, workflow order, required evidence, scoped Windmill sync, mem0 memory policy, and required GitHub status contexts. It does not require workstation-only tools so CI can run it.

On the local control station, also check installed tools:

```bash
python3 scripts/ai-factory/bootstrap_runtime.py --check --check-tools
```

## Operating Boundary

AI Factory defines the process:

```text
issue_to_plan -> plan_to_pr -> control_plane_ci -> augment_context_review -> codex_qa_gate -> protected_merge
```

GitHub enforces the process with required checks:

```text
control-plane
ai-gate/final-review
```

Windmill runs the orchestration scripts under `f/mil/**` and publishes the AI gate status. Production credentials must stay in Windmill or GitHub secret stores, never in `.ai-factory/**`.

Implementation dispatch now uses the real Plan-to-PR orchestrator and Codex
worker contract:

```text
f/mil/plan_to_pr -> f/mil/plan_to_pr_contract -> f/mil/codex_worker -> scripts/agent-flow/codex_worker.py -> codex exec
```

`plan_to_pr` retrieves scoped memory, prepares a read-only Augment MCP
`codebase-retrieval` request, injects any preloaded Augment context into the
Codex prompt, and then asks `codex_worker` for the command pack. The worker is
non-executing by default. It creates a command pack until `execute_agent`,
`push`, and `open_pr` are explicitly enabled by the control plane.

Unattended execution is handled by the local control-station dispatcher, not by
the hosted Windmill container:

```text
GitHub webhook -> signed relay -> Windmill router/audit
               -> local auto_dispatcher.py -> codex_worker.py --execute-agent --push --open-pr
```

The relay only launches the dispatcher when `MIL_AUTO_DISPATCH_ENABLED=1` and
the GitHub request explicitly uses `agent:auto-build` or `/agent autobuild`.
The dispatcher still requires issue scope, allowed files, required checks,
empty restricted changes, AI Factory rules, and branch-protected PR review.

GitHub webhook ingress is handled by `f/mil/github_webhook_router` through the Windmill HTTP route `mil/github-webhook`. The route is public at the HTTP layer, but the router rejects unsigned or incorrectly signed GitHub deliveries using the Windmill secret `f/mil/github_webhook_secret`.

Memory0/Mem0 is configured as optional project memory through `mem0_memory`.
During framework development, the local JSONL adapter at
`.ai-factory/memory/local_memory.jsonl` is used for deterministic tests and
local dry-runs. The Memory Gateway contract in `f/mil/memory_contract.py`
validates schema, rejects restricted payloads, enforces `source_ref`, writes
audit events, and emits optional Mem0-compatible payloads.

Agent-created memory starts as `candidate`. Only `status=approved` memory can
enter `wm_memory_preflight` or `wm_task_context_pack`. Memory0 is context only:
GitHub issues/PRs, project docs, tests, CI, and audit evidence remain source of
truth.
