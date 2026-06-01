# wm_rollback_pack

Purpose: package rollback evidence for application, database, workflow, and
model changes.

Rollback areas:
- Application: redeploy prior image or tag and confirm health.
- Database: prefer backward-compatible migration or document backup restore.
- Workflow: disable new Windmill flow and restore prior approved version.
- Model: pin previous model, clear runtime cache, restart service, and run
  replay or shadow smoke.

Gate: production release is blocked without owned rollback steps.
