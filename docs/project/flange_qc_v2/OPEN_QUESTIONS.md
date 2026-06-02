# FLANGE QC App V2 Open Questions

## Questions

| ID | Question | Priority | Owner | Status | Resolution Source |
|---|---|---|---|---|---|
| FQV2-Q-001 | What is the target product repository and `repo_id`? | Critical | Product owner | Resolved for MVP-0 bootstrap: `MIL/flange-qc-v2-bootstrap` | `docs/superpowers/specs/2026-06-02-flange-qc-v2-gate-resolution-design.md` |
| FQV2-Q-002 | Should FLANGE QC V2 live inside MIL, a new repo, or an existing FLANGE repo? | Critical | Product owner | Resolved for MVP-0 bootstrap: use MIL control-plane repo only for scoped app skeleton | `docs/superpowers/specs/2026-06-02-flange-qc-v2-gate-resolution-design.md` |
| FQV2-Q-003 | Who is the named QC/domain owner for SOP and product spec approval? | Critical | Product owner | Open | TBD |
| FQV2-Q-004 | Where are the original SOP documents and source data for tolerance tables? | Critical | QC/domain owner | Open | TBD |
| FQV2-Q-005 | Which deployment target is first: local replay only, Jetson, RTX workstation, or hosted server? | Important | Product owner | Open | TBD |
| FQV2-Q-006 | What camera/lens/lighting setup is approved for first live calibration? | Important | Engineering/operator | Open | TBD |
| FQV2-Q-007 | What is the first replay fixture that can be committed or referenced safely? | Important | QC/domain owner | Open | TBD |
| FQV2-Q-008 | Who approves the product groups/tolerances imported from `/Users/mac/Desktop/flange_project_kickoff_docs.zip:.ai-factory/rules/product.md`? | Critical | QC/domain owner | Open | TBD |
| FQV2-Q-009 | Which package root is canonical for app code: `src/flange_qc/**` from the ZIP or `apps/flange_qc_v2/**` from the MIL scoped package? | Critical | Product owner + engineering | Resolved for MVP-0 bootstrap: `apps/flange_qc_v2/**` | `docs/superpowers/specs/2026-06-02-flange-qc-v2-gate-resolution-design.md` |
| FQV2-Q-010 | Which branch naming convention wins for FLANGE work when ZIP guidance conflicts with MIL AGENTS.md? | Critical | Merge controller | Resolved: current MIL AGENTS.md wins; use `agent/fqv2-001-app-skeleton` | `docs/superpowers/specs/2026-06-02-flange-qc-v2-gate-resolution-design.md` |
| FQV2-Q-011 | Which CI checks are blocking for the first app skeleton issue: pytest, ruff, mypy, config validation, replay smoke, or framework-only validators? | Critical | Merge controller + engineering | Resolved for FQV2-001: stdlib unit tests, compileall, product-CI runner, framework validators, full unittest suite | `.ai-factory/gates/flange_qc_v2_fqv2_001_dor.json` |
| FQV2-Q-012 | Should length and width aggregate use average, min/max envelope, or all-points-must-pass logic? | Critical | QC/domain owner | Open | TBD |
| FQV2-Q-013 | Are items 963 and 445 in first pilot scope? | Important | Product owner + QC/domain owner | Open | TBD |
| FQV2-Q-014 | Which product IDs correspond to `M695UN` and `M587UN` in ERP/product labels? | Important | QC/domain owner | Open | TBD |
| FQV2-Q-015 | Is diagonal deviation measured on corrected top boundary or raw detected corners? | Important | QC/domain owner + engineering | Open | TBD |
| FQV2-Q-016 | Which migration approach is canonical if SQLite audit schema is implemented: Alembic, SQLModel metadata, or custom SQL migrations? | Important | Engineering | Open | TBD |

## Rule

Open questions are not requirements. Critical questions block active coding-agent
dispatch for app-code implementation in the product repo.
