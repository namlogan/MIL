# wm_staging_deploy

Purpose: deploy a release candidate to staging or record why staging is not
available for the project.

Inputs:
- Release manifest
- Deployment provider configuration
- Artifact version

Outputs:
- Staging URL or environment reference
- Deploy log reference
- Smoke test command and result
- Failure summary when deployment is blocked
