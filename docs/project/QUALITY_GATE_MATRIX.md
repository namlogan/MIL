# Quality Gate Matrix

## Purpose

This project matrix maps change types to required checks before merge or
release. The generic policy lives in `.ai-factory/QUALITY_GATES.md`.

| Change type | Required gates | Block condition |
|---|---|---|
| Project docs | Intake validator, Delivery OS validator | Missing owner, scope, or open question handling |
| Contract | Contract validator, contract tests | Public contract drift without evidence |
| Agent workflow | Runtime validator, Windmill validator, unit tests | Fake lane, missing handoff, unsafe auto-dispatch |
| Memory | Memory schema, scrubber, source reference | Secret, raw data, unapproved memory |
| Product code | Product CI, unit/integration/e2e as applicable | Test failure or missing product stack checks |
| Release | Release gate, rollback drill, approval | Missing rollback, smoke evidence, or owner approval |

## PR Size Policy

Prefer PRs below 300 LOC. PRs from 300 to 800 LOC require stronger evidence.
PRs above 800 LOC require split or owner approval.
