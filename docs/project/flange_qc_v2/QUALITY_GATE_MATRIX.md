# FLANGE QC App V2 Quality Gate Matrix

| Change type | Required gates | Block condition |
|---|---|---|
| Project docs | Intake review, open-question review, Delivery OS policy | Critical owner/source questions unresolved for coding dispatch |
| API/WebSocket contract | Contract tests, payload schema validation | Public payload drift without compatibility note |
| Product spec config | Schema validation, QC/domain approval, unit tests | Unapproved tolerance or unknown source |
| SOP rule engine | Unit tests, replay tests, reason-code evidence | Missing phase/reason evidence or unsafe PASS |
| Calibration | Synthetic validator, owner approval for live mode | Missing/pending calibration can PASS |
| Detector adapter | Contract tests, no PASS/NG authority | Detector decides inspection outcome |
| Audit DB | Migration contract, rollback/forward-fix plan | Destructive change without approval |
| HMI | Contract/e2e smoke, accessibility smoke when UI exists | Missing safety state or reason codes |
| Release | CI, replay smoke, rollback pack, monitoring plan, human approval | Missing rollback or shadow/staging evidence |

## PR Size Policy

Prefer PRs below 300 LOC. PRs from 300 to 800 LOC need stronger evidence.
PRs above 800 LOC require split or owner approval.
