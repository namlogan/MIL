# FLANGE QC App V2 Work Packages

## Status

These are backlog-ready package drafts, not agent-runnable jobs. Convert each
package into a GitHub issue only after project identity, source refs, allowed
files, required checks, restricted-change status, rollback note, and memory
preflight are complete.

## Defaults

| Field | Value |
|---|---|
| Owner agent | `codex_developer` |
| Preferred lane | `codex` |
| QA | `codex_qa` |
| Restricted paths | secrets, production deploy, raw datasets, destructive migrations, production auto-reject |
| Required handoff | files changed, rules applied, tests run, risks, rollback, memory candidate or not-applicable |

## Packages

| ID | Title | Allowed paths | Required checks | Rollback |
|---|---|---|---|---|
| V2-001 | App skeleton, health endpoint, CI baseline | `apps/flange_qc_v2/**`, `tests/**`, `.ai-factory/product-ci.json` | unit, lint, typecheck, health smoke, `git diff --check` | Revert app skeleton PR |
| V2-002 | Domain models and WebSocket payload contracts | `apps/flange_qc_v2/**`, `contracts/flange_qc_v2/**`, `tests/contract/**` | contract tests, unit tests | Revert model/contract PR |
| V2-003 | SOP rule registry and reason codes | `apps/flange_qc_v2/**`, `docs/project/flange_qc_v2/SOP_RULE_REGISTRY.md`, `tests/unit/**` | unit tests, rule registry review | Revert rule registry PR |
| V2-004 | Product specs config validator and tolerance resolver | `configs/flange_qc_v2/**`, `apps/flange_qc_v2/**`, `tests/unit/**` | config validation, unit tests | Restore prior config version |
| V2-005 | SQLite audit schema and migrations | `apps/flange_qc_v2/**`, `tests/integration/**` | migration tests, integration tests | Apply forward-fix or restore prior schema |
| V2-006 | Calibration contract and synthetic validator | `configs/flange_qc_v2/**`, `apps/flange_qc_v2/**`, `tests/unit/**` | synthetic calibration tests | Revert calibration PR |
| V2-007 | Geometry measurement contract | `apps/flange_qc_v2/**`, `contracts/flange_qc_v2/**`, `tests/unit/**` | unit and contract tests | Revert measurement PR |
| V2-008 | Phase gate and decision engine | `apps/flange_qc_v2/**`, `tests/unit/**` | unit tests for PASS/NG/BLOCKED states | Revert decision engine PR |
| V2-009 | Replay frame source and no-camera E2E | `apps/flange_qc_v2/**`, `samples/replay/**`, `tests/replay/**` | replay smoke, integration tests | Disable replay source change |
| V2-010 | WebSocket/HMI payload stream | `apps/flange_qc_v2/**`, `tests/contract/**`, `tests/integration/**` | payload contract and integration tests | Revert WebSocket PR |
| V2-011 | Minimum HMI screen | `apps/flange_qc_v2/**`, `tests/**` | UI smoke, payload compatibility | Revert HMI PR |
| V2-012 | QC feedback and shadow evidence contract | `apps/flange_qc_v2/**`, `contracts/flange_qc_v2/**`, `tests/integration/**` | contract and audit tests | Disable feedback endpoint |
| V2-013 | Image quality gate contract | `apps/flange_qc_v2/**`, `tests/unit/**` | unit tests for quality states | Revert quality gate PR |
| V2-014 | Detector abstraction and stub adapter | `apps/flange_qc_v2/**`, `tests/unit/**`, `tests/contract/**` | adapter contract tests | Use stub adapter only |
| V2-015 | Hikrobot camera adapter boundary | `apps/flange_qc_v2/**`, `docs/project/flange_qc_v2/HARDWARE_CAMERA_READINESS.md` | boundary tests without live hardware | Disable live camera adapter |
| V2-016 | Jetson/RTX app deployment scaffold | `deploy/**`, `docs/project/flange_qc_v2/DEPLOYMENT.md` | deploy plan validation, no secrets scan | Revert deploy scaffold |
| V2-017 | Release, rollback, and shadow readiness report | `docs/project/flange_qc_v2/**`, `docs/release/**` | release gate, rollback checklist | Revert release docs |
| V2-018 | Memory0/Windmill SDLC hooks validation | `.windmill/**`, `.ai-factory/**`, `docs/project/flange_qc_v2/**` | Delivery OS, Windmill validator, memory contract | Revert hook changes |

## Dispatch Constraint

Each package must become its own issue and branch. Do not combine packages unless
the owner approves the larger scope and the PR size remains within MIL limits.
