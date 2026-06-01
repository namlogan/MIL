# wm_contract_bootstrap

Purpose: create or validate minimum project contracts before backlog work.

Expected contracts:
- `contracts/api/openapi.yaml`
- `contracts/events/*.schema.json`
- `contracts/payloads/*.schema.json`
- `contracts/db/migration_contract.md`
- `contracts/memory/memory_event.schema.json`
- `contracts/jobs/*.schema.json`

Gate: no implementation task may be generated for public API, event, payload,
database, memory, or job behavior until its contract exists.
