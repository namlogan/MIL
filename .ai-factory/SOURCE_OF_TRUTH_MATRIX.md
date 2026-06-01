# Source Of Truth Matrix

Memory, chat, and generated context are useful, but they are not authoritative.
When sources disagree, use the most authoritative source below and route stale
memory to conflict review.

| Topic | Source of truth | Supporting evidence |
|---|---|---|
| Requirements | PRD, approved issue, acceptance criteria | User notes, memory candidates |
| Architecture decision | Merged ADR or architecture doc | Review notes, design discussion |
| Code | Git branch, PR diff, merge commit | Agent handoff |
| Task state | GitHub issue, PR state, Windmill run state | Local queue files |
| Test result | CI, product CI, Windmill evidence | Local terminal logs |
| Release state | Release manifest and deployment provider | Release memory candidate |
| Secrets | Secret manager or environment reference | Never Memory0 or docs |
| Dataset or model artifact | DVC, object store, registry, or provider | Run evidence |
| Production audit | Audit database, logs, monitoring platform | Incident notes |
| Memory | Approved scoped Memory0 record | Source references only |

## Conflict Rule

If approved memory conflicts with docs, issue, PR, tests, CI, release manifest,
or audit logs, the source-of-truth wins. The memory record must be marked
`needs_review`, `superseded`, or `retired` through the Memory Gateway.
