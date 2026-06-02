# FLANGE QC App V2 Project Identity

## Identity

| Field | Value |
|---|---|
| Project ID | `flange-qc-v2` |
| Product name | FLANGE QC App V2 |
| Repo ID | `MIL/flange-qc-v2-bootstrap` |
| Bootstrap location | `docs/project/flange_qc_v2/` in the MIL control-plane repo |
| Canonical app root | `apps/flange_qc_v2/**` |
| First implementation branch | `agent/fqv2-001-app-skeleton` |
| Owner | Logan / product owner |
| Initial source brief | `/Users/mac/.codex/attachments/29025915-a42c-4868-98b5-9de4595af87b/pasted-text.txt` |
| Kickoff ZIP reviewed | `/Users/mac/Desktop/flange_project_kickoff_docs.zip` |
| Bootstrap date | 2026-06-02 |

## Intended Stack

- FastAPI service with WebSocket output.
- Minimal HMI for operator status, reason codes, measurements, calibration state, and feedback.
- SQLite audit storage for bootstrap and replay mode.
- Replay/no-camera E2E path before factory hardware is required.
- Detector adapter boundary with stub implementation until MLOps/model gates approve a production model.
- Jetson/RTX deployment scaffold after app baseline and release gates are ready.

## Operating Boundary

MIL remains the SDLC control plane. FLANGE QC App V2 is the product being bootstrapped.
This package is an intake and architecture baseline. It permits only the scoped
FQV2-001 app skeleton task after Definition of Ready evidence is recorded.
Production SOP authority, product tolerance approval, live hardware validation,
model promotion, and release approval remain unresolved.
