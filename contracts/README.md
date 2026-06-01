# Contract-First Skeleton

Contracts are written before implementation for interfaces that other code,
agents, or systems depend on. A task that changes one of these contracts must
run the contract validator and include compatibility notes in the PR.

## Contract Areas

- `api/openapi.yaml`: HTTP API surface and health endpoint.
- `events/software_task_event.schema.json`: SDLC task event shape.
- `payloads/task_context_pack.schema.json`: Windmill-to-agent context package.
- `db/migration_contract.md`: migration safety and rollback requirements.
- `memory/memory_event.schema.json`: canonical Memory0 event schema mirror.
- `jobs/gstack_job.schema.json`: agent job manifest contract.

Use `python3 scripts/contracts/validate_contracts.py --self-test` before merge.
