# FLANGE QC App V2 Source Of Truth

## Rule

Git/docs/tests/issues are source of truth. Memory0 is not source of truth.
Windmill orchestrates SDLC work. AI Factory defines governance. Memory0 provides
approved, scoped memory context only.

## Matrix

| Topic | Authoritative source |
|---|---|
| Requirements | Product PRD, MVP scope, accepted GitHub issue |
| SOP interpretation | Original SOP docs plus QC/domain owner-approved rule registry |
| Product tolerances | Approved product spec config and source reference |
| Architecture | Merged ADRs |
| Contracts | `contracts/flange_qc_v2/**` after promotion to target repo |
| Code | Target repo branch, PR diff, merge commit |
| Tests | CI, product CI, replay smoke evidence |
| Release | Release manifest, rollback pack, owner approval |
| Memory | Approved scoped Memory0 record with `source_ref` only |

## Conflict Policy

When memory or pasted summaries conflict with SOP docs, approved project docs,
contracts, tests, CI, release evidence, or audit logs, the source-of-truth wins.
Conflicting memory must be routed to conflict review.
