# wm_rollback_drill

Purpose: verify the rollback path before production promotion.

Checks:
- Rollback command or procedure is explicit.
- Owner is named.
- Data impact is documented.
- Smoke test after rollback is defined.
- Monitoring signal for rollback success is defined.

Production release is blocked when rollback is missing or unowned.
