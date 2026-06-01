# Solo Agent SDLC Runbook

Status date: 2026-06-01.

This runbook describes the daily operating loop for one product owner using MIL
with Codex workers, Windmill orchestration, Augment context, and optional Mem0
memory.

## Morning Check

Run:

```bash
python3 scripts/operator/daily_status.py
```

Continue only when the dashboard is `ready`. If it reports `attention`, fix the
named check first. Do not start new `agent:auto-build` work while the control
plane is dirty or core validators fail.

## Project Intake

Before agents build product features, fill these files:

```text
.ai-factory/DESCRIPTION.md
.ai-factory/ARCHITECTURE.md
.ai-factory/RULES.md
docs/project/PRD.md
docs/project/MVP_SCOPE.md
docs/project/USER_FLOWS.md
docs/project/DATA_MODEL.md
docs/project/TEST_STRATEGY.md
docs/project/DEPLOYMENT.md
```

Validate:

```bash
python3 scripts/project-intake/validate_project_intake.py
```

## Build Loop

1. Create a GitHub issue with acceptance criteria, allowed files, checks, risk,
   and rollback note.
2. Add `agent:plan` when you want a plan only.
3. Add `agent:auto-build` only when the scope is small enough for one Codex
   worker.
4. Watch Windmill jobs and the opened PR.
5. Merge only when GitHub branch protection is clean.

## Product CI

When the product stack exists, edit `.ai-factory/product-ci.json`:

```json
{
  "enabled": true,
  "checks": [
    {
      "name": "unit",
      "command": ["python3", "-m", "unittest", "discover", "-s", "tests", "-v"],
      "required": true
    }
  ]
}
```

Use command arrays, not shell strings. The runner is:

```bash
python3 scripts/product-ci/run_product_checks.py
```

## Memory

Start with local JSONL memory. Move to Mem0 OSS when repeated tasks need durable
cross-session memory:

```bash
python3 scripts/agent-memory/check_mem0_provider.py
```

Mem0 may store scoped, sanitized operational facts. It must not store secrets,
raw source, raw transcripts, customer data, or unreviewed generated patches.

## Release

Protected merge is not release approval. For staging or production rollout,
create release evidence from `docs/templates/release/RELEASE_CHECKLIST.md` and
validate it:

```bash
python3 scripts/release/release_gate.py --evidence release-evidence.json
```

Release requires CI pass, AI gate pass, staging smoke, rollback plan, monitoring
plan, and human approval.
