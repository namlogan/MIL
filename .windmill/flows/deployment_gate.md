# wm_deployment_gate

Purpose: validate deployment readiness without embedding production secrets.

Checks:
- Deployment provider is configured through secret references.
- Environment config diff is visible.
- Health check and monitoring plan are ready.
- Production approval is present when required.

Gate: deployment is blocked when secrets are literal values or approval is
missing.
