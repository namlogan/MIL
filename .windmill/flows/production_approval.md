# wm_production_approval

Purpose: request and record explicit human approval for production promotion.

Inputs:
- Release manifest
- Staging and shadow evidence
- Rollback drill result
- Monitoring plan
- Known risks

Outputs:
- `PRODUCTION_APPROVED`
- `PRODUCTION_REJECTED`
- `PRODUCTION_DEFERRED`

Windmill records the decision but does not invent approval.
