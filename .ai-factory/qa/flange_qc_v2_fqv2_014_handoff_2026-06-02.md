# FQV2-014 QA Handoff: Detector Abstraction And Stub Adapter

## Source

- GitHub issue: https://github.com/namlogan/MIL/issues/85
- Branch: `agent/85-detector-stub-adapter`
- Task: FQV2-014

## Files Changed

- `apps/flange_qc_v2/detector.py`
- `apps/flange_qc_v2/sop_registry.py`
- `contracts/flange_qc_v2/detector/detector_result.schema.json`
- `tests/flange_qc_v2/test_detector_adapter.py`
- `docs/project/flange_qc_v2/DATA_MODEL.md`
- `docs/project/flange_qc_v2/MLOPS_BOUNDARY.md`
- `.ai-factory/gates/flange_qc_v2_fqv2_014_dor.json`
- `.ai-factory/qa/flange_qc_v2_fqv2_014_handoff_2026-06-02.md`

## Rules Applied

- One task per branch.
- GitHub issue is source of truth for requirement, acceptance criteria, and allowed paths.
- TDD red/green was used before implementation.
- Detector adapter returns observations only and cannot decide PASS/NG.
- Production model training, model promotion, MLOps artifacts, live camera, raw media, production deploy, secrets, customer data, and destructive migrations remain out of scope.

## Memory Preflight

- Query: Flange QC v2 detector adapter boundary, MLOps separation, stub observations, missing model safe states.
- Retrieved decisions: detector observations never decide final PASS/NG; production model promotion and MLOps remain separate; missing model returns safe states.
- Retrieved lessons: keep adapters contract-first; use synthetic/replay metadata only; TDD first; fail closed or not-evaluated for missing model evidence.
- Restricted areas: live camera/raw media, model weights, TensorRT engines, MLOps artifacts, production release/deploy, secrets, customer data, destructive migrations, QC/SOP tolerance approval.
- Conflicts found: none.
- Sources to verify: GitHub issue #85, AGENTS.md, `docs/project/flange_qc_v2/WORK_PACKAGES.md`, `docs/project/flange_qc_v2/MLOPS_BOUNDARY.md`, `docs/project/flange_qc_v2/TEST_STRATEGY.md`.

## Implementation Notes

- Added `DetectorRequest`, `DetectorResult`, and `StubDetectorAdapter`.
- Detector requests accept synthetic/replay frame metadata only and reject raw media paths.
- Stub detector returns `NOT_EVALUATED` with `MODEL_MISSING` when no observations are configured.
- Stub detector returns `ASSIST` with `MODEL_REVIEW_REQUIRED` when validated stub observations are supplied.
- Detector observations reuse the existing `DetectorObservation` bbox/confidence contract.
- Detector results reject `PASS`, `NG`, and production authority.
- Added `MODEL_APPROVAL_REQUIRED` as a shared authority blocker reason code.

## Tests Run

- `python3 -m unittest tests.flange_qc_v2.test_detector_adapter -v`
- `python3 -m unittest discover -s tests/flange_qc_v2 -v`
- `python3 -m compileall -q apps/flange_qc_v2 tests/flange_qc_v2`
- `python3 scripts/product-ci/run_product_checks.py`
- `python3 -m unittest discover -s tests -v`
- `git diff --check`

## Residual Risks

- Stub observations are synthetic/replay contract evidence only.
- There is no production model, model promotion, raw pixel inference, or MLOps integration.
- Live camera hardware and production authority remain blocked.
- SOP interpretation for model-dependent rules still needs QC/domain approval before production use.

## Rollback

Revert the FQV2-014 PR to remove the detector adapter boundary, stub adapter,
schema/tests, docs, and gate evidence. This task does not alter production data,
migrations, secrets, or deploy configuration.

## Memory Candidate

- memory_type: implementation_lesson
- content: Flange QC v2 detector adapter boundary returns validated observations only; the stub adapter emits NOT_EVALUATED or ASSIST and never PASS/NG.
- source_ref: https://github.com/namlogan/MIL/issues/85
- why reusable: Future replay integration, HMI observations, camera boundary, and model adapter work need this non-authoritative boundary.
- scope: project:flange_qc_v2
- suggested status: candidate
