# FQV2-015 QA Handoff: Hikrobot Camera Boundary

## Source

- GitHub issue: https://github.com/namlogan/MIL/issues/87
- Branch: `agent/87-hikrobot-camera-boundary`
- Task: FQV2-015
- Owner approval: disabled no-hardware boundary only on 2026-06-02.

## Files Changed

- `apps/flange_qc_v2/camera.py`
- `apps/flange_qc_v2/sop_registry.py`
- `contracts/flange_qc_v2/camera/camera_boundary.schema.json`
- `tests/flange_qc_v2/test_camera_boundary.py`
- `docs/project/flange_qc_v2/HARDWARE_CAMERA_READINESS.md`
- `docs/project/flange_qc_v2/DATA_MODEL.md`
- `.ai-factory/gates/flange_qc_v2_fqv2_015_dor.json`
- `.ai-factory/qa/flange_qc_v2_fqv2_015_handoff_2026-06-02.md`

## Rules Applied

- One task per branch.
- GitHub issue is source of truth for requirement, acceptance criteria, and allowed paths.
- TDD red/green was used before implementation.
- Owner approval allows disabled no-hardware boundary only.
- Live capture, SDK imports, camera credentials, raw media, production deploy, production PASS/NG authority, and destructive migrations remain blocked.

## Memory Preflight

- Query: Flange QC v2 Hikrobot camera boundary, hardware readiness, no-hardware bootstrap, live camera restrictions.
- Retrieved decisions: app must boot without camera; live hardware remains gated; calibration approval is required before live mode; no raw media/customer data in baseline CI; owner approved disabled no-hardware boundary only.
- Retrieved lessons: keep hardware adapters disabled-by-default and contract-first; use TDD first; explicit blockers beat implicit hardware assumptions.
- Restricted areas: live camera capture, SDK dependency, camera credentials/secrets, raw media, customer data, production release/deploy, destructive migrations, QC/SOP tolerance approval.
- Conflicts found: none after owner approval for disabled no-hardware boundary only.
- Sources to verify: GitHub issue #87, AGENTS.md, `docs/project/flange_qc_v2/WORK_PACKAGES.md`, `docs/project/flange_qc_v2/APP_BUILD_PLAN.md`, `docs/project/flange_qc_v2/RISK_REGISTER.md`.

## Implementation Notes

- Added `CameraBoundaryConfig`, `CameraBoundaryResult`, and `HikrobotCameraBoundary`.
- Default boundary reports Hikrobot readiness metadata while disabled.
- Boundary rejects enabled, live-capture, SDK-loaded, and credential-configured states.
- `capture_frame()` is blocked with `ValidationError`.
- Payloads cannot emit `PASS` or `NG` and cannot grant production authority.
- Added camera hardware, calibration, and live-disabled reason codes.
- Added hardware readiness documentation listing the approvals needed before live camera work.

## Tests Run

- `python3 -m unittest tests.flange_qc_v2.test_camera_boundary -v`
- `python3 -m unittest discover -s tests/flange_qc_v2 -v`
- `python3 -m compileall -q apps/flange_qc_v2 tests/flange_qc_v2`
- `python3 scripts/product-ci/run_product_checks.py`
- `python3 -m unittest discover -s tests -v`
- `git diff --check`

## Residual Risks

- Hardware model, lens, lighting, mount, trigger/source mode, resolution/FPS, and credentials remain unapproved.
- No Hikrobot SDK is imported or validated.
- No live frames are captured.
- Calibration approval and production release approval remain required before live mode.

## Rollback

Revert the FQV2-015 PR to remove the camera boundary, schema/tests, docs, and
gate evidence. This task does not alter production data, migrations, secrets,
raw media, live hardware, or deploy configuration.

## Memory Candidate

- memory_type: implementation_lesson
- content: Flange QC v2 Hikrobot camera boundary is disabled-by-default and rejects live capture, SDK loading, and credentials until hardware readiness approval.
- source_ref: https://github.com/namlogan/MIL/issues/87
- why reusable: Future live camera and deployment tasks need a clear no-hardware boundary and readiness checklist.
- scope: project:flange_qc_v2
- suggested status: candidate
