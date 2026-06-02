# FQV2-013 QA Handoff: Image Quality Gate Contract

## Source

- GitHub issue: https://github.com/namlogan/MIL/issues/83
- Branch: `agent/83-image-quality-gate-contract`
- Task: FQV2-013

## Files Changed

- `apps/flange_qc_v2/image_quality.py`
- `apps/flange_qc_v2/audit.py`
- `apps/flange_qc_v2/sop_registry.py`
- `contracts/flange_qc_v2/image_quality/quality_gate.schema.json`
- `tests/flange_qc_v2/test_image_quality.py`
- `tests/flange_qc_v2/test_audit_store.py`
- `docs/project/flange_qc_v2/DATA_MODEL.md`
- `.ai-factory/gates/flange_qc_v2_fqv2_013_dor.json`
- `.ai-factory/qa/flange_qc_v2_fqv2_013_handoff_2026-06-02.md`

## Rules Applied

- One task per branch.
- GitHub issue is source of truth for requirement, acceptance criteria, and allowed paths.
- TDD red/green was used before implementation.
- Image quality evidence is metadata-only and shadow-only.
- Production release/deploy, secrets, customer data, product spec approval, QC/SOP tolerance approval, detector/MLOps artifacts, and destructive migrations remain out of scope.

## Memory Preflight

- Query: Flange QC v2 image quality gate, replay/shadow evidence, prior domain contract packages.
- Retrieved decisions: use synthetic fixtures only; production release/deploy, product spec approval, QC/SOP tolerance approval, and production PASS/NG authority remain human gates; detector observations are separate from deterministic gates.
- Retrieved lessons: keep contracts explicit; use TDD first; fail closed for missing or invalid bootstrap evidence; avoid live camera/raw media and MLOps artifacts in bootstrap contracts.
- Restricted areas: production release/deploy, secrets, customer data, destructive migrations, live camera/raw media, detector/MLOps artifacts, QC/SOP tolerance approval.
- Conflicts found: none.
- Sources to verify: GitHub issue #83, AGENTS.md, `docs/project/flange_qc_v2/WORK_PACKAGES.md`, `docs/project/flange_qc_v2/USER_FLOWS.md`, `docs/project/flange_qc_v2/TEST_STRATEGY.md`.

## Implementation Notes

- Added `evaluate_image_quality(payload)` for synthetic/replay frame metadata.
- Validates frame metadata, source URI, timestamp, source ref, and normalized brightness/sharpness/occlusion scores.
- Emits shadow `PASS`, `ASSIST`, or `BLOCKED` evidence.
- Dark, blurry, or severe occlusion evidence fails closed as `BLOCKED`.
- Moderate occlusion returns `ASSIST` with review-required reason code.
- All payloads set `production_authority` to `false` and carry `IMAGE_QUALITY_APPROVAL_REQUIRED` plus `PRODUCTION_APPROVAL_REQUIRED`.
- Added image quality reason codes to the SOP registry for shared gate vocabulary.
- Closed sqlite audit store connections explicitly after verification surfaced ResourceWarnings.

## Tests Run

- `python3 -m unittest tests.flange_qc_v2.test_image_quality -v`
- `python3 -m unittest tests.flange_qc_v2.test_audit_store -v`
- `python3 -m unittest discover -s tests/flange_qc_v2 -v`
- `python3 -m compileall -q apps/flange_qc_v2 tests/flange_qc_v2`
- `python3 scripts/product-ci/run_product_checks.py`
- `python3 -m unittest discover -s tests -v`
- `git diff --check`

## Residual Risks

- The thresholds are bootstrap defaults and require QC/domain approval before production use.
- The gate uses synthetic/replay metadata only; it does not calculate scores from raw image pixels.
- Detector adapter integration is not implemented in this task.
- Live camera hardware, raw media, customer/factory data, production deploy, and production authority remain blocked.

## Rollback

Revert the FQV2-013 PR to remove the image quality contract, schema/tests, docs,
gate evidence, and sqlite connection hygiene fix. This task does not alter
production data, migrations, secrets, or deploy configuration.

## Memory Candidate

- memory_type: implementation_lesson
- content: Flange QC v2 image quality gate evaluates synthetic/replay metadata into shadow PASS/ASSIST/BLOCKED evidence with explicit production blockers.
- source_ref: https://github.com/namlogan/MIL/issues/83
- why reusable: Future detector, HMI, replay, and release-readiness tasks need a stable pre-detector quality boundary.
- scope: project:flange_qc_v2
- suggested status: candidate
