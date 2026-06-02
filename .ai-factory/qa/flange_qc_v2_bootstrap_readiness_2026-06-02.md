# FLANGE QC V2 Bootstrap Readiness Evidence

Date: 2026-06-02

## Source Reviewed

Attached intake brief:

```text
/Users/mac/.codex/attachments/29025915-a42c-4868-98b5-9de4595af87b/pasted-text.txt
```

The brief references a sandbox ZIP and folder, but those artifacts were not
available in this environment. This bootstrap therefore treats the pasted text as
an intake brief, not as fully verified source documentation.

## Files Created

- `docs/project/flange_qc_v2/**`
- `docs/adr/flange-qc-v2/**`
- `contracts/flange_qc_v2/**`
- `configs/flange_qc_v2/**`
- `docs/superpowers/plans/2026-06-02-flange-qc-v2-bootstrap.md`

## Framework Fit

The brief is compatible with the MIL framework because it preserves these rules:

- Git/docs/tests/issues remain source of truth.
- Windmill is SDLC orchestration only.
- AI Factory is governance and evidence only.
- Memory0 is approved scoped memory only.
- Codex is the only implementation worker.
- Augment/Auggie are context/advisory only.
- Realtime PASS/NG stays inside the app, not Windmill or Memory0.
- Model-dependent rules do not produce production decisions before MLOps approval.

## Readiness Decision

The material is enough to bootstrap intake, architecture, contracts, and planning
artifacts. It is not enough to dispatch coding agents yet.

## Blockers Before Coding Dispatch

- Target repo and `repo_id` are not confirmed.
- Full referenced docs bundle is not available in this environment.
- Original SOP sources are not attached.
- QC/domain owner approval for product specs and tolerance values is missing.
- Active product CI cannot be enabled until the target app skeleton exists.
- No GitHub issue exists with Definition of Ready fields for first implementation.

## Rollback

Delete the FLANGE QC V2 scoped docs, ADRs, contracts, configs, plan, and this QA
artifact. No app runtime code was created.

```aif-gate-result
{
  "schema_version": "2.0",
  "gate": "new_project_bootstrap_readiness",
  "status": "warn",
  "blocking": true,
  "blockers": [
    "target_repo_id_missing",
    "full_source_docs_unavailable",
    "sop_source_refs_missing",
    "qc_product_spec_approval_missing",
    "definition_of_ready_issue_missing"
  ],
  "affected_files": [
    "docs/project/flange_qc_v2/**",
    "docs/adr/flange-qc-v2/**",
    "contracts/flange_qc_v2/**",
    "configs/flange_qc_v2/**",
    "docs/superpowers/plans/2026-06-02-flange-qc-v2-bootstrap.md",
    ".ai-factory/qa/flange_qc_v2_bootstrap_readiness_2026-06-02.md"
  ],
  "suggested_next": "BLOCKED_NEEDS_HUMAN"
}
```
