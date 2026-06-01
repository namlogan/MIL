# wm_contract_gate

Purpose: block contract drift before merge.

Checks:
- OpenAPI, event, payload, database, memory, and job contracts parse.
- Contract changes include compatibility notes and tests.
- Public behavior does not change without source reference and approval.

This flow is the PR-time complement to `wm_contract_bootstrap`.
