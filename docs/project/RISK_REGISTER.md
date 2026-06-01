# Risk Register

## Purpose

This register tracks project risks that can block safe agent work, merge, or
release. Risks are source-of-truth project artifacts after review and merge.

## Risk Table

| ID | Risk | Severity | Owner | Mitigation | Status |
|---|---|---|---|---|---|
| MIL-RISK-001 | Public webhook exposure during pilot | Medium | Project owner | Keep relay scoped, verify signatures, move to stable tunnel later | Active |
| MIL-RISK-002 | Stale or cross-project memory contaminates prompts | High | Memory reviewer | Approved-only scoped retrieval and conflict review | Active |
| MIL-RISK-003 | Product CI missing for future app stack | Medium | Tech lead | Enable `.ai-factory/product-ci.json` when app stack exists | Open |

## Review Rule

Critical and high risks must be resolved, accepted by the owner, or converted to
explicit release blockers before production promotion.
