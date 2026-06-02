# FLANGE QC V2 Gate Resolution Design

Date: 2026-06-02

## Purpose

Resolve the app-code blockers recorded after reviewing
`/Users/mac/Desktop/flange_project_kickoff_docs.zip` without bypassing the MIL
startup protocol. The approved direction is to unblock a safe MVP-0 skeleton in
the MIL bootstrap workspace while keeping production SOP authority and product
tolerance approval outside Codex.

## Approved Direction

User approval was given in chat on 2026-06-02 with the response `duyet`.

The approved operating decisions are:

- Use `/Users/mac/Documents/MIL` as the bootstrap repository for MVP-0.
- Set `repo_id` for this bootstrap lane to `MIL/flange-qc-v2-bootstrap`.
- Use `apps/flange_qc_v2/**` as the canonical app package root.
- Let the current MIL `AGENTS.md` branch rules override the ZIP branch examples.
- Use `agent/fqv2-001-app-skeleton` for the first implementation branch or
  manifest branch name.
- Keep `configs/flange_qc_v2/product_specs.bootstrap.json` in
  `draft_requires_qc_owner_approval` status.
- Do not use draft product specs for production PASS/NG decisions.
- Start with `FQV2-001 App skeleton, health endpoint, CI baseline`.

## Non-Delegable Approvals

Codex can prepare evidence and request files, but cannot grant these approvals:

- QC/domain owner approval for product dimensions, tolerances, SOP
  interpretation, and source SOP revision.
- Production release approval.
- Live camera/hardware validation approval.
- Model promotion approval.

Until these approvals are recorded, deterministic production decisions remain
limited to explicitly approved scope, and model-dependent rules remain
`ASSIST`, `NOT_EVALUATED`, or blocked.

## Gate Resolution Pack

After this design is accepted, create a focused gate-resolution pack:

- Update project identity with `repo_id` and canonical package root.
- Update open questions by marking the approved bootstrap decisions resolved and
  leaving QC/SOP approvals open.
- Add an ADR for app package root, branch convention, and MVP-0 bootstrap repo
  decision.
- Add a QC approval request artifact for
  `configs/flange_qc_v2/product_specs.bootstrap.json`.
- Add a first task manifest for `FQV2-001` with allowed paths, restricted paths,
  acceptance criteria, tests, rollback, and memory preflight.
- Add gate evidence showing implementation may start only for the app skeleton,
  not SOP rule production behavior.

## First Implementation Scope

`FQV2-001` is intentionally narrow:

- Create a minimal FastAPI app skeleton under `apps/flange_qc_v2/**`.
- Add a health endpoint that reports subsystem states without requiring camera,
  GPU, model, factory data, or product tolerance approval.
- Add CI/product-CI config entries for lint, typecheck, unit tests, and health
  smoke once the app skeleton exists.
- Keep SOP decision logic, product tolerance resolver, replay processing,
  calibration, audit DB migrations, WebSocket payloads, and HMI out of this
  first issue.

## Testing Strategy

Use TDD for app-code implementation:

- First write failing tests for the health endpoint and package import.
- Add the smallest app skeleton that makes those tests pass.
- Run full repo verification before claiming completion.

Gate-resolution docs are verified with:

- `git diff --check`
- `python3 scripts/project-intake/validate_project_intake.py`
- `python3 scripts/delivery/validate_delivery_os.py --self-test`
- `python3 scripts/contracts/validate_contracts.py --self-test`
- `python3 -m unittest discover -s tests -v`
- `python3 scripts/operator/daily_status.py`

## Stop Conditions

Stop before app-code implementation if any of these are true:

- The gate-resolution pack is not accepted.
- The first task manifest lacks allowed paths, required checks, rollback, or
  memory preflight.
- Product specs are requested for production PASS/NG before QC approval.
- Work would touch secrets, raw factory data, production deploy, destructive
  migrations, model weights, TensorRT engines, or legacy runtime code.
