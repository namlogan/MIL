# wm_shadow_deploy

Purpose: run a production-like or read-only observation stage when the product
risk justifies it.

Allowed uses:
- Read-only traffic observation
- Feature-flagged preview
- Background job dry run
- Model or worker shadow evaluation

Shadow deploy must not mutate production data unless the release owner approves
that exact behavior in writing.
