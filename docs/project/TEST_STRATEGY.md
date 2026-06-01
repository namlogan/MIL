# MIL Test Strategy

## Test Layers

| Layer | Command | Required Before Merge |
|---|---|---|
| Unit | `python3 -m unittest discover -s tests -v` | Yes |
| Compile | `python3 -m compileall -q scripts tests f` | Yes |
| AI Factory | `python3 scripts/ai-factory/bootstrap_runtime.py --check` | Yes |
| Windmill | `python3 scripts/windmill/validate_windmill_project.py --self-test` | Yes |
| Product CI | `python3 scripts/product-ci/run_product_checks.py` | When enabled |

## Critical Behaviors

- Webhook signature verification must reject bad signatures.
- Codex worker must enforce allowed files and restricted changes.
- PR gate must publish `ai-gate/final-review`.
- Memory search must reject unscoped retrieval.

## Fixtures And Test Data

Unit tests use local fixtures and no production secrets. Runtime queue evidence
is ignored by Git and should be attached through PR comments or QA docs when it
matters.

## Agent Verification Rules

Codex workers run task-required checks plus framework gate checks. Product
repositories should enable `.ai-factory/product-ci.json` as soon as app code
exists.

## Release Smoke

Release smoke must prove the app or control plane runs outside the worker
session and must be recorded in the release checklist.
