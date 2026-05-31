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
```

## Check Install

Run the runtime checker after cloning or changing factory config:

```bash
python3 scripts/ai-factory/bootstrap_runtime.py --check
python3 scripts/agent-gate/validate_ai_factory.py --self-test
```

The default checker validates required agents, workflow order, required evidence, scoped Windmill sync, and required GitHub status contexts. It does not require workstation-only tools so CI can run it.

On the local control station, also check installed tools:

```bash
python3 scripts/ai-factory/bootstrap_runtime.py --check --check-tools
```

## Operating Boundary

AI Factory defines the process:

```text
issue_to_plan -> plan_to_pr -> control_plane_ci -> auggie_advisory_review -> codex_qa_gate -> protected_merge
```

GitHub enforces the process with required checks:

```text
control-plane
ai-gate/final-review
```

Windmill runs the orchestration scripts under `f/mil/**` and publishes the AI gate status. Production credentials must stay in Windmill or GitHub secret stores, never in `.ai-factory/**`.
