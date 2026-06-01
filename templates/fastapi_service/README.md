# FastAPI Service Template

Baseline for a backend service in this framework.

Include:
- `app/main.py` with `/health`.
- OpenAPI contract before routes.
- Pydantic request and response models.
- Unit and integration tests.
- Config through environment variables and secret references.
- Structured logs with request IDs.
- CI commands for lint, typecheck, tests, and build.

Do not add production secrets, default admin credentials, or hidden network
dependencies to the template.
