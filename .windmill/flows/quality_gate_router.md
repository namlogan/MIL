# wm_quality_gate_router

Purpose: select required quality gates by change type.

Routes:
- Product behavior -> unit, integration, product CI, Codex QA.
- API contract -> OpenAPI diff and contract tests.
- Event or payload contract -> JSON schema and producer/consumer checks.
- Database migration -> migration contract and rollback review.
- Security -> secret scan and human security approval.
- Memory event -> schema validation and scrubber.
- Release -> release candidate pack and rollback drill.

The router records required gates in PR evidence before final QA.
