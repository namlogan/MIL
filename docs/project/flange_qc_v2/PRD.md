# FLANGE QC App V2 Product Requirements

## Purpose

FLANGE QC App V2 is a greenfield quality-control application for mattress/flange
inspection. It must run a real app path early using replay/no-camera input,
deterministic SOP rules, audit evidence, and shadow-mode feedback while model
training and MLOps mature separately.

## Users

- QC operator: views inspection state, measurements, reason codes, calibration
  status, and submits feedback.
- QC/domain owner: approves product specs, tolerances, SOP interpretation, and
  production readiness.
- Engineering/operator: runs replay tests, validates contracts, deploys app
  environments, and monitors audit evidence.
- Codex worker: may implement scoped issues only after this intake package is
  promoted into the target repo and Definition of Ready passes.

## Problem

The previous FLANGE runtime should not be extended as the production base. The
attached brief states the older implementation had major SOP compliance gaps,
including product-specific tolerance, diagonal validation, punch mark, mark
offset, seam/corner behavior, and enhanced defect classes. V2 must create a
clean app architecture that can run now with deterministic core behavior and
later receive approved model observations through contracts.

## Goals

- Build a running FastAPI/WebSocket inspection app before requiring camera, GPU,
  factory data, or production model access.
- Implement deterministic SOP core for known product specs, measurements, and
  reason-coded phase decisions.
- Keep model-dependent observations separate from PASS/NG authority until MLOps
  approval exists.
- Persist inspection, rule, calibration, and feedback evidence in an audit DB.
- Support replay/no-camera E2E and shadow-mode production learning.

## Non-Goals

- Production model training.
- Full MLOps platform implementation.
- CVAT, FiftyOne, ClearML, Prefect, DVC, or MinIO buildout.
- Production auto-reject before release and owner approval.
- ERP/MES integration.
- Raw dataset management inside the app repo.

## Requirements

| ID | Requirement | Priority | Acceptance Signal |
|---|---|---|---|
| FQV2-REQ-001 | App boots without camera, GPU, model, or factory data | Must | Health endpoint reports explicit subsystem states |
| FQV2-REQ-002 | Replay/no-camera E2E path | Must | Replay command processes sample frames and writes audit evidence |
| FQV2-REQ-003 | Product spec and tolerance resolver | Must | Unknown product returns `BLOCKED`, never PASS |
| FQV2-REQ-004 | Calibration gate | Must | Missing or pending calibration returns `BLOCKED`, never PASS |
| FQV2-REQ-005 | 3 length, 3 width, and 2 diagonal measurement contract | Must | Unit/contract tests validate required measurement points |
| FQV2-REQ-006 | Diagonal deviation rule | Must | Deviation greater than 0.5 inch returns NG in phase 2 |
| FQV2-REQ-007 | Detector adapter boundary | Must | Detector returns observations only and cannot decide PASS/NG |
| FQV2-REQ-008 | Model-dependent rule states | Must | Missing model returns `NOT_EVALUATED`, `ASSIST`, or `BLOCKED` as configured |
| FQV2-REQ-009 | WebSocket/HMI payload contract | Must | Payload schema includes normalized bounding boxes in `[0, 1]` |
| FQV2-REQ-010 | Audit DB | Must | Inspection, rule results, calibration state, and feedback are stored |
| FQV2-REQ-011 | Release and rollback evidence | Must | Every release candidate includes rollback pack and smoke evidence |

## Risks

- SOP interpretation may be incomplete because only a pasted summary is available
  in this session, not the full generated ZIP/folder or original SOP PDFs.
- Product tolerance config must be approved by QC/domain owner before production.
- Camera installation details need factory-site validation.
- Model-dependent defect decisions must not silently become production PASS/NG.
- Target repo and deployment path are not confirmed.
