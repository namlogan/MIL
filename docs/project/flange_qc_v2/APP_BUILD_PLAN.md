# FLANGE QC App V2 App Build Plan

## Gate-First Sequence

1. Resolve critical open questions.
2. Promote this bootstrap package into the confirmed target repo.
3. Run project intake and Delivery OS validation in the target repo.
4. Create app skeleton with health endpoint and CI baseline.
5. Add domain models and WebSocket payload contracts.
6. Add SOP rule registry and reason codes.
7. Add product specs validator and tolerance resolver.
8. Add SQLite audit schema and non-destructive migration policy.
9. Add calibration contract and synthetic validator.
10. Add geometry measurement contract.
11. Add phase gate and decision engine.
12. Add replay frame source and no-camera E2E.
13. Add WebSocket/HMI stream and minimal HMI screen.
14. Add QC feedback and shadow evidence contract.
15. Add image quality gate contract.
16. Add detector abstraction and stub adapter.
17. Add live camera adapter boundary only after hardware readiness is approved.
18. Add deployment scaffold, release, rollback, and shadow readiness evidence.

## Proposed Work Packages

| ID | Title | Scope |
|---|---|---|
| V2-001 | App skeleton, health endpoint, CI baseline | FastAPI app boots with health state |
| V2-002 | Domain models and WebSocket payload contracts | Typed models and contract tests |
| V2-003 | SOP rule registry and reason codes | Deterministic rule metadata |
| V2-004 | Product specs validator and tolerance resolver | Unknown product blocks |
| V2-005 | SQLite audit schema and migrations | Append-only audit records |
| V2-006 | Calibration contract and synthetic validator | Missing calibration blocks |
| V2-007 | Geometry measurement contract | 3 length, 3 width, 2 diagonals |
| V2-008 | Phase gate and decision engine | PASS/NG/BLOCKED state logic |
| V2-009 | Replay frame source and no-camera E2E | Replay smoke path |
| V2-010 | WebSocket/HMI payload stream | Operator payloads |
| V2-011 | Minimum HMI screen | Status, reason codes, feedback |
| V2-012 | QC feedback and shadow evidence contract | Feedback persistence |
| V2-013 | Image quality gate contract | Quality states |
| V2-014 | Detector abstraction and stub adapter | Observations only |
| V2-015 | Hikrobot camera adapter boundary | No baseline CI hardware dependency |
| V2-016 | Jetson/RTX app deployment scaffold | Deployment config without secrets |
| V2-017 | Release, rollback, and shadow readiness report | Release evidence |
| V2-018 | Memory0/Windmill SDLC hooks validation | Governance hooks |

## Dispatch Rule

Do not dispatch any of these packages until a GitHub issue or approved local task
contains acceptance criteria, allowed files, required checks, restricted-change
status, rollback note, and memory preflight scope.
