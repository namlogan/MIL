# Project Source Of Truth

## Rule

Git/docs/tests/issues are source of truth. Memory0 is not source of truth.
Windmill orchestrates workflow. AI Factory defines delivery governance. Memory0
provides approved, scoped memory context only.

## Matrix

| Topic | Authoritative source |
|---|---|
| Requirements | PRD, MVP scope, accepted issue |
| Architecture | Merged ADR and `.ai-factory/ARCHITECTURE.md` |
| Contracts | `contracts/**` |
| Code | Git branch, PR diff, merge commit |
| Task state | GitHub issue and PR |
| Test result | CI, product CI, local evidence when CI is unavailable |
| Release state | Release manifest and deployment evidence |
| Operational learning | Approved Memory0 record with source reference |

## Conflict Policy

When memory conflicts with GitHub, docs, contracts, tests, CI, release evidence,
or audit logs, the source-of-truth wins and the memory record goes to conflict
review.
