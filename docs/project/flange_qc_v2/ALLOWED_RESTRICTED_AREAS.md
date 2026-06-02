# FLANGE QC App V2 Allowed And Restricted Areas

## Bootstrap Allowed Areas

These areas are safe for documentation and contract bootstrap work:

- `docs/project/flange_qc_v2/**`
- `docs/adr/flange-qc-v2/**`
- `contracts/flange_qc_v2/**`
- `configs/flange_qc_v2/**`
- `.ai-factory/qa/flange_qc_v2_*`
- `docs/superpowers/plans/2026-06-02-flange-qc-v2-bootstrap.md`

## First Implementation Allowed Areas

These paths are proposed for the future target product repo after owner approval:

- `apps/flange_qc_v2/src/**`
- `apps/flange_qc_v2/tests/**`
- `contracts/flange_qc_v2/**`
- `configs/flange_qc_v2/**`
- `tools/**`
- `samples/replay/**` only for approved synthetic or shareable replay fixtures

## Restricted Areas

Human approval is required before touching:

- Production deployment behavior.
- Production secrets, credentials, tokens, or camera credentials.
- Customer/factory raw image datasets.
- Product tolerance changes after QC approval.
- Auth/authz boundaries.
- Destructive audit DB migrations.
- Production auto-reject behavior.
- Legal, compliance, or safety-critical behavior.

## Rule

If a future issue needs files outside its allowed paths, stop and request scope
expansion before editing.
