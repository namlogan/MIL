# Release Policy

The framework supports development automation, but release remains an explicit
promotion workflow. Production changes require a release manifest and owner
approval.

## Promotion Stages

1. Local: all required local checks pass.
2. Dev: deploy preview or internal environment is updated.
3. Staging: smoke tests, migrations, and config diff are verified.
4. Shadow: production-like traffic or read-only observation is checked when
   applicable.
5. Production: owner approval, rollback command, monitoring plan, and release
   notes are complete.

## Release Manifest

Every release candidate must include change summary, linked issues and PRs,
migrations, config diff, artifact versions, test evidence, known risks,
rollback command, monitoring plan, and approval owner.

## Required Flows

- `wm_release_candidate_pack`
- `wm_staging_deploy`
- `wm_shadow_deploy`
- `wm_production_approval`
- `wm_rollback_drill`
- `wm_release_memory_writeback`

## Rollback

Production release is blocked when rollback is missing, untested, or dependent
on an unowned manual step.
