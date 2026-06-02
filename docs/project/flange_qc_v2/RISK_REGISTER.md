# FLANGE QC App V2 Risk Register

## Risk Table

| ID | Risk | Severity | Owner | Mitigation | Status |
|---|---|---|---|---|---|
| FQV2-RISK-001 | Full generated bootstrap ZIP/folder was not available in this session | Medium | Product owner | Treat pasted text as intake brief; verify against original docs before coding dispatch | Active |
| FQV2-RISK-002 | SOP and tolerance interpretation may be incomplete | High | QC/domain owner | Require owner approval for `product_specs.bootstrap.json` before production | Active |
| FQV2-RISK-003 | Model-dependent defects could be mistaken for production decisions | High | Engineering/operator | Detector observations cannot decide PASS/NG; missing model returns `NOT_EVALUATED`, `ASSIST`, or `BLOCKED` | Active |
| FQV2-RISK-004 | Camera hardware assumptions may not match factory site | Medium | Engineering/operator | Require hardware readiness and calibration approval before live mode | Active |
| FQV2-RISK-005 | Target repo and deployment path are not confirmed | Medium | Product owner | Resolve project identity before active repo bootstrap and agent dispatch | Open |
| FQV2-RISK-006 | Production auto-reject could affect operations before validation | High | Product owner | Keep production auto-reject out of MVP; require release approval and shadow evidence | Active |

## Review Rule

High risks must be resolved, explicitly accepted, or converted into release
blockers before production promotion.
