# wm_release_gate

Purpose: decide whether a release candidate may move toward production
approval.

Required evidence:
- Version or tag.
- Change summary and PR list.
- Migration list and config diff.
- Artifact versions.
- Test and staging smoke evidence.
- Security notes and known risks.
- Rollback command.
- Owner approval request.

Gate: release is blocked without rollback and smoke evidence.
