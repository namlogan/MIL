# Quality Gate Matrix

## Purpose

Map project change types to required gates.

| Change type | Required gates | Owner |
|---|---|---|
| Product behavior | Unit, integration, product CI | QA |
| API or event contract | Contract validator and compatibility note | Architect |
| Database migration | Migration contract and rollback plan | Tech lead |
| Security | Secret scan and human approval | Security owner |
| Release | Release pack, smoke, rollback drill | Product owner |

## Gate Rule

If a change type is not listed, stop and update this matrix before dispatching
agent work.
