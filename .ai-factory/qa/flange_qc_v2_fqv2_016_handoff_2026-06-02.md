# FQV2-016 QA Handoff: Jetson/RTX Deployment Scaffold

## Source

- GitHub issue: https://github.com/namlogan/MIL/issues/89
- Branch: `agent/89-jetson-rtx-deploy-scaffold`
- Task: FQV2-016

## Files Changed

- `deploy/flange_qc_v2/deploy_plan.json`
- `deploy/flange_qc_v2/README.md`
- `scripts/deploy/validate_flange_qc_v2_deploy_plan.py`
- `tests/flange_qc_v2/test_deploy_plan.py`
- `tests/test_product_ci_config.py`
- `.ai-factory/product-ci.json`
- `docs/project/flange_qc_v2/DEPLOYMENT.md`
- `.ai-factory/gates/flange_qc_v2_fqv2_016_dor.json`
- `.ai-factory/qa/flange_qc_v2_fqv2_016_handoff_2026-06-02.md`

## Rules Applied

- One task per branch.
- GitHub issue is source of truth for requirement, acceptance criteria, and allowed paths.
- TDD red/green was used before implementation.
- Deployment scaffold remains disabled/manual and does not execute deploys.
- Production release/deploy, secrets, live camera, raw media, hardware validation, and QC/SOP approval remain human-gated.

## Memory Preflight

- Query: Flange QC v2 deployment scaffold, Jetson/RTX target, manual disabled provider, no-secrets deployment validation.
- Retrieved decisions: deployment target is still open; release/deploy remains a human gate; baseline app remains replay/shadow-only; `.ai-factory/deploy-provider.json` is manual and disabled.
- Retrieved lessons: use contract-first validation, keep deployment scaffolds disabled by default, and make blocked authorities explicit.
- Restricted areas: production deploy/release, secrets/credentials/tokens, customer data, raw media, destructive migrations, live camera/hardware validation, model weights/TensorRT engines, QC/SOP tolerance approval, product spec approval.
- Conflicts found: none because this task remains scaffold-only and does not execute deploys.
- Sources to verify: GitHub issue #89, AGENTS.md, `.ai-factory/RULES.md`, `.ai-factory/RELEASE_POLICY.md`, `docs/project/flange_qc_v2/WORK_PACKAGES.md`, `docs/project/flange_qc_v2/DEPLOYMENT.md`.

## Implementation Notes

- Added a versioned deploy plan for local replay, Jetson shadow, and RTX shadow targets.
- All targets keep deploy, production deploy, live camera, and raw media disabled.
- Added a validator that rejects production deploy, live camera, raw media, secret-like values, and executable deploy commands.
- Added product CI coverage for deploy plan validation without enabling the repo deploy provider.
- Updated deployment docs with validation command, open target decision, release gate, and rollback expectations.

## Tests Run

- `python3 -m unittest tests.flange_qc_v2.test_deploy_plan -v`
- `python3 scripts/deploy/validate_flange_qc_v2_deploy_plan.py --plan deploy/flange_qc_v2/deploy_plan.json`
- `python3 -m unittest discover -s tests/flange_qc_v2 -v`
- `python3 -m compileall -q apps/flange_qc_v2 tests/flange_qc_v2 scripts/deploy`
- `python3 scripts/product-ci/run_product_checks.py`
- `python3 -m unittest discover -s tests -v`
- `git diff --check`

## Residual Risks

- First real deployment target is still open in `FQV2-Q-005`.
- No Jetson/RTX hardware, GPU runtime, camera SDK, or live frames are validated.
- No release candidate is created by this task.
- Production release/deploy still requires separate release evidence and human approval.

## Rollback

Revert the FQV2-016 PR to remove the deployment scaffold, validator/tests,
product CI deploy-plan check, docs update, and gate evidence. This task does
not alter production infrastructure, secrets, hardware state, raw media,
customer data, migrations, or release/deploy configuration.

## Memory Candidate

- memory_type: implementation_lesson
- content: Flange QC v2 deployment scaffold is disabled/manual by default and validated to reject production deploy, live camera, raw media, secret-like values, and executable deploy commands.
- source_ref: https://github.com/namlogan/MIL/issues/89
- why reusable: Future release and deployment work needs a safe scaffold boundary before target-specific deploys.
- scope: project:flange_qc_v2
- suggested status: candidate
