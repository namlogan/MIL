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

The dashboard checks:

- local git cleanliness
- AI Factory and Windmill project validators
- Codex, Auggie, and Windmill CLI availability
- relay and public tunnel `tmux` sessions
- open PRs and required gate status
- latest `main` GitHub Actions run
- recent failed Windmill jobs
- Augment credential readiness
- Mem0 provider mode
- branch protection policy
- recent local auto-dispatch queue results

For the temporary ngrok endpoint, also run:

```bash
python3 scripts/windmill/check_public_endpoint.py \
  --public-url https://<assigned-name>.ngrok-free.dev/mil/github-webhook
```

This confirms that the public URL reaches the signed local relay health route
without exposing the full Windmill UI/API.

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

When the product stack exists, edit `.ai-factory/product-ci.json`. You can use
inline checks or select a profile from `.ai-factory/product-ci.profiles.json`.

Profile example:

```json
{
  "enabled": true,
  "profile": "python-unittest",
  "checks": []
}
```

Inline example:

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

Start with local JSONL memory while the framework is being developed:

```bash
python3 scripts/agent-memory/check_mem0_provider.py
python3 scripts/agent-memory/mem0_framework_integration.py --self-test
```

When the product app or a future worker explicitly needs Mem0's own package,
check the OSS library without requiring any external LLM provider:

```bash
pip install mem0ai
python3 scripts/agent-memory/check_mem0_library.py --runtime python
```

or for a Node app:

```bash
npm install mem0ai
python3 scripts/agent-memory/check_mem0_library.py --runtime node
```

Only use `--require-llm` when you intentionally want real Mem0 `Memory()` calls
that perform extraction/semantic search through a configured provider.

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

Configure the deploy provider separately in `.ai-factory/deploy-provider.json`.
The default is disabled manual release. When an app provider exists, validate
the deploy plan before release:

```bash
python3 scripts/release/deploy_provider.py --plan --environment staging
```
