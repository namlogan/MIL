# wm_contract_test_gate

Purpose: prevent contract drift from entering implementation unnoticed.

Checks:
- `python3 scripts/contracts/validate_contracts.py --self-test`
- OpenAPI has `openapi`, `info`, `paths`, and `/health`.
- JSON schema files parse and define `type` and `properties`.
- Memory contract mirror matches `memory/schemas/memory_event.schema.json`.
- Database migration contract is referenced when migrations change.

Output is pass, fail, or needs human review.
