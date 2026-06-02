# FLANGE QC v2 Shadow Readiness Report

Release ID: `flange-qc-v2-shadow-readiness-2026-06-02`
Status: `BLOCKED_NEEDS_HUMAN` for release or deploy
Source commit: `f3f2375f506b3a9f29a4a0876c3396e839971b02`
Target environment: shadow/readiness only

## Summary

The replay-driven Flange QC v2 baseline is ready for local and CI validation,
but it is not approved for staging, shadow, or production deployment. Release
approval remains blocked until the product owner approves the release, the first
deployment target is selected, staging or shadow smoke evidence exists, and
QC/domain approvals are recorded for production-bound product specs.

## Merged App Scope

| Package | PR | Status |
|---|---:|---|
| FQV2-001 app skeleton | #60 | Merged |
| FQV2-002 domain models and WebSocket contracts | #62 | Merged |
| FQV2-003 SOP rule registry and reason codes | #64 | Merged |
| FQV2-004 product specs resolver | #66 | Merged, draft only |
| FQV2-005 SQLite audit store | #68 | Merged |
| FQV2-006 synthetic calibration validator | #70 | Merged |
| FQV2-007 geometry measurement contract | #72 | Merged |
| FQV2-008 shadow phase gate and decision engine | #74 | Merged |
| FQV2-009 replay source and no-camera E2E | #76 | Merged |
| FQV2-010 WebSocket/HMI stream | #78 | Merged |
| FQV2-011 minimum HMI screen | #80 | Merged |
| FQV2-012 QC feedback and shadow evidence | #82 | Merged |
| FQV2-013 image quality gate | #84 | Merged |
| FQV2-014 detector stub adapter | #86 | Merged |
| FQV2-015 Hikrobot camera no-hardware boundary | #88 | Merged |
| FQV2-016 Jetson/RTX deployment scaffold | #90 | Merged, disabled/manual |

## Evidence

- Main CI workflow `26798514006` passed on 2026-06-02 after PR #90 merged.
- Product CI is enabled and includes compile, Flange QC v2 unit discovery,
  health smoke, and deploy-plan validation.
- Deployment provider remains manual and disabled.
- Deployment scaffold validates local replay, Jetson shadow, and RTX shadow
  targets without deploy commands or secret requirements.
- Release gate has been tightened so pending or blocked human approval text
  cannot satisfy release approval.

## Shadow Readiness

Ready for local/CI shadow-style validation:

- no-camera replay flow
- health endpoint
- WebSocket/HMI payload stream and minimum HMI page
- SQLite audit evidence
- QC feedback evidence
- image quality and detector-stub boundaries
- disabled camera boundary
- disabled deployment scaffold validation

Blocked before staging, shadow, or production promotion:

- human release approval
- staging or shadow smoke evidence outside the developer workstation
- first deployment target decision
- QC/domain owner approval for production-bound product specs and tolerances
- live camera/hardware readiness and calibration approval
- model promotion or production detector authority
- production rollback drill in the selected runtime

## Release Gate

Release evidence file:

```text
docs/release/flange_qc_v2/release_gate_pending_2026-06-02.json
```

Expected release-gate result for that evidence is blocked, not approved, because
human release approval and staging/shadow smoke evidence are pending.

## Rollback

Rollback drill document:

```text
docs/release/flange_qc_v2/rollback_drill_2026-06-02.md
```

Because no deploy is executed by this readiness pack, rollback for this task is
a normal PR revert. A future deployed release must separately verify rollback in
the selected Jetson, RTX, or server runtime.

## Monitoring Plan

Before any shadow deployment, the operator must prepare monitoring for:

- app health endpoint
- product CI and main CI status
- deploy-plan validation status
- replay smoke result
- audit DB write success/failure
- WebSocket/HMI snapshot availability
- inspection decision counts by state and reason code
- QC feedback volume and unresolved corrections
- camera/model availability flags

## Decision

This report supports merging the readiness evidence, but it does not approve
release or deployment. Release/deploy remains `BLOCKED_NEEDS_HUMAN`.
