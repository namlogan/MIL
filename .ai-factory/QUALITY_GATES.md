# Quality Gates

Quality gates are selected by change type. A PR may require more than one gate.
When a gate applies, it blocks merge until evidence is present.

| Change type | Required checks | Required reviewer or owner |
|---|---|---|
| Product behavior | Unit, integration, product CI, acceptance criteria evidence | Codex QA |
| API contract | Contract validator, OpenAPI diff, client impact note | Codex QA or architect |
| Event or payload contract | JSON schema validation, producer/consumer test | Codex QA |
| Database migration | Migration contract, rollback plan, data safety note | Human approval for destructive change |
| Security | Secret scan, auth boundary review, dependency review | Human approval |
| Memory event | Memory schema validation, scrubber, source reference | Memory reviewer |
| Agent workflow | Runtime validator, Windmill validator, smoke flow | Merge controller |
| Release | Release manifest, staging smoke, rollback drill | Product owner |

## Standard Commands

```bash
python3 scripts/delivery/validate_delivery_os.py --self-test
python3 scripts/contracts/validate_contracts.py --self-test
python3 scripts/agent-memory/memory_contract.py --self-test
python3 scripts/agent-gate/validate_ai_factory.py --self-test
python3 scripts/windmill/validate_windmill_project.py --self-test
python3 scripts/product-ci/run_product_checks.py --self-test
python3 scripts/release/release_gate.py --self-test
python3 -m unittest discover -s tests -v
git diff --check
```

## Merge Blocks

Merge is blocked when a PR lacks handoff evidence, test evidence, restricted
change declaration, rollback note, source references, contract evidence, or a
clean final gate result.
