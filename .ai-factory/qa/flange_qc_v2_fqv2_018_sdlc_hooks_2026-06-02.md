# FQV2-018 QA Handoff: Memory0/Windmill SDLC Hooks

## Source

- GitHub issue: https://github.com/namlogan/MIL/issues/93
- Branch: `agent/93-sdlc-hooks-validation`
- Task: FQV2-018

## Files Changed

- `.ai-factory/gates/flange_qc_v2_fqv2_018_dor.json`
- `.ai-factory/qa/flange_qc_v2_fqv2_018_sdlc_hooks_2026-06-02.md`
- `docs/project/flange_qc_v2/BOOTSTRAP_READINESS.md`
- `docs/project/flange_qc_v2/QUALITY_GATE_MATRIX.md`

## Validation Evidence

Required checks:

- `python3 scripts/delivery/validate_delivery_os.py --self-test`
- `python3 scripts/windmill/validate_windmill_project.py --self-test`
- `python3 scripts/agent-memory/check_mem0_provider.py --self-test`
- `python3 scripts/agent-memory/memory_contract.py --self-test`
- `python3 scripts/agent-memory/mem0_framework_integration.py --self-test`
- `python3 scripts/product-ci/run_product_checks.py`
- `python3 scripts/operator/daily_status.py`
- `python3 -m unittest discover -s tests -v`
- `git diff --check`

The current Memory0 provider path is the local JSONL adapter. No external mem0
provider credentials are configured or required by this app package.

## Windmill Boundary

Windmill is valid as an orchestration and evidence layer only. It may route
ready work, create command packs, publish statuses, and request human approval,
but it cannot:

- author app code
- bypass branch protection or merge policy
- approve production release
- replace GitHub issues, PRs, docs, tests, or CI as source of truth
- expose secrets or runtime logs to agents
- continue automation past hold, owner-review, blocked, or security-review labels

No `.windmill/runtime/**` file, tunnel file, local env file, or secret-backed
flow was changed by this package.

## Memory0 Boundary

Memory0 is scoped context only. It is not source of truth and cannot store:

- secrets, tokens, credentials, or private keys
- raw artifacts, raw logs, raw media, raw transcripts, customer data, or source dumps
- generated patches or proprietary source
- project-specific memory without `source_ref`
- approved memory without review

This package does not write, approve, update, supersede, or retire any Memory0
record. Any useful lesson remains candidate-only until reviewed.

## Rules Applied

- One task per branch.
- GitHub issue is source of truth for requirement, acceptance criteria, and allowed paths.
- No app code, production deploy behavior, release approval, branch protection, or workflow file changed.
- Runtime secrets/logs and `.windmill/runtime/**` remain untouched.
- Memory0 remains source-ref-scoped context only.

## Residual Risks

- Windmill issue #4 remains open as an external-blocker for full workspace/secrets provisioning.
- Issue #3 remains ready for human review for Augment context provider setup.
- Mem0 external provider is not configured; local JSONL adapter is active.
- Production release/deploy remains blocked pending human approval and target-specific evidence.

## Rollback

Revert the FQV2-018 PR to remove validation evidence and readiness/quality-gate
doc updates. This task does not alter app code, Windmill runtime config,
Memory0 records, secrets, production infrastructure, hardware state, raw media,
customer data, migrations, or release/deploy state.

## Memory Candidate

- memory_type: implementation_lesson
- content: Flange QC v2 SDLC hook validation is evidence-only; Windmill remains orchestration/evidence only and Memory0 remains scoped source-ref context only.
- source_ref: https://github.com/namlogan/MIL/issues/93
- why reusable: Future app packages need the same boundary before allowing Windmill/Memory0 context into delivery loops.
- scope: project:flange_qc_v2
- suggested status: candidate
