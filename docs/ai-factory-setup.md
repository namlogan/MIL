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
scripts/agent-memory/memory_contract.py
```

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

GitHub webhook ingress is handled by `f/mil/github_webhook_router` through the Windmill HTTP route `mil/github-webhook`. The route is public at the HTTP layer, but the router rejects unsigned or incorrectly signed GitHub deliveries using the Windmill secret `f/mil/github_webhook_secret`.

Mem0 is configured as optional project memory through `mem0_memory`. Until a Mem0 Platform or self-hosted endpoint is configured, the local JSONL adapter at `.ai-factory/memory/local_memory.jsonl` is used only for deterministic tests and local dry-runs. Runtime memory files are ignored by git.
