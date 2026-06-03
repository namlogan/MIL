# QC Tablet Viewport Design

## Source

- Issue: https://github.com/namlogan/MIL/issues/125
- Task: FQV2-034
- User approval: revised option A, signal-first tablet viewport.
- Framework starter repo confirmed before implementation work:
  https://github.com/namlogan/MIL-agent-factory-starter
- Local framework backup artifacts also exist:
  `/Users/mac/Desktop/MIL-framework-bootstrap-pre-app-code-941e92a-20260603.bundle`

## Goal

Redesign the QC-facing HMI first viewport so the operator does not read a dense
dashboard during normal work. The screen should behave like an operating signal:

- Green means the automated checks passed and QC can continue other work.
- Red means QC should look at the marked product region or self-measure the
  product.
- Amber means the app is not ready to make a confident operator signal because
  data, authority, or review evidence is missing.

The detailed SOP/debug evidence remains available below the first viewport or
through a details affordance, but it must not compete with the primary QC signal.

## State Model

The viewport uses exactly three operator states:

| Operator state | Visual | Meaning | Primary QC action |
|---|---|---|---|
| `PASS` | Green | Required automated measurements are within configured tolerance and no suspected defect needs attention | Continue / next product |
| `CHECK` | Red | Measurement or detector evidence requires QC attention | Inspect circled area or self-measure |
| `REVIEW` | Amber | App lacks enough approved data, calibration, authority, or model confidence | Wait, review setup, or inspect details |

Backend decision authority does not change. The HMI maps existing
`phase_results`, `measurements`, `decision`, `reason_codes`, and review-only
`observations` into the operator state.

## First Viewport Layout

The tablet-first layout uses a 4:3 landscape composition:

1. Top measurement strip
   - Product code.
   - Length status.
   - Width status.
   - Diagonal or stitch status.
   - Chips should show `OK`, `CHECK`, or `REVIEW`, not raw debug text.

2. Large signal banner
   - `PASS` green with supporting text `Continue`.
   - `CHECK` red with supporting text `Inspect suspected area`.
   - `REVIEW` amber with supporting text `Wait / review`.

3. Product image panel
   - Dominant center area.
   - In current no-camera mode, render a replay/placeholder image well so the
     layout can be verified without raw media.
   - When detector observations include normalized `bbox` values, draw the
     suspected area overlay directly on the image panel.
   - When there is no suspect region, show a calm pass outline or empty
     inspection area.

4. Operator action row
   - Green state: `Next product` and `Details`.
   - Red state with app alarm: `Alert correct` and `False alarm`.
   - Amber state: `Details` / `Review setup`.

## Alarm Feedback

The red alarm feedback is for future model quality improvement. It does not
approve production decisions.

- `Alert correct` records that QC agrees the app alarm should be treated as a
  true positive candidate.
- `False alarm` records that QC believes the app alarm is a false positive.
- The first implementation should use the existing `/feedback` endpoint and
  existing feedback authority where possible:
  - `Alert correct` maps to a confirm/review feedback payload.
  - `False alarm` maps to `MARK_FALSE_POSITIVE`.
- Feedback must include the current inspection id, operator id, decision state,
  and a concise note indicating the selected alarm feedback.

If the existing feedback contract cannot express the true-positive case cleanly,
the implementation should keep the UI mapping to the closest existing feedback
type and record the limitation in QA handoff rather than changing backend
contracts in the same task.

## Data Flow

The HMI continues to use existing sources:

- `/inspection/replay` for no-camera snapshot refresh.
- `/ws/inspection` for the normal inspection snapshot stream.
- `/detector/shadow/status` for detector bridge readiness.
- `/artifact-intake/status` for artifact readiness.
- `/feedback` for operator feedback evidence.

The new viewport derives:

- Measurement chips from `measurements` and Phase 1/Phase 2 `phase_results`.
- Overall operator state from current phase decisions and top-level decision.
- Suspected image overlays from `observations[].bbox` when present.
- Alarm feedback context from current inspection id and selected observation.

## Error And Safe States

- Unknown product, missing calibration, missing product-spec approval, missing
  hardware readiness, or model review blockers must map to amber `REVIEW`,
  unless existing decision evidence clearly requires red `CHECK`.
- Invalid or missing observation bbox should not draw an overlay.
- Lack of live camera must not block the layout; no-camera replay/placeholder
  remains the test surface.
- The UI must not use red for policy/authority blockers alone. Red is reserved
  for QC action on suspected product or measurement issues.

## Testing

Required verification:

- HMI screen tests prove the new first viewport IDs, status labels, measurement
  chips, image panel, overlay renderer hooks, and alarm feedback buttons exist.
- Tests prove the three-state mapping exists for green, red, and amber display.
- Browser/tablet screenshot evidence verifies the first viewport at a tablet
  landscape size.
- Existing Flange QC tests, product CI, full repo tests, compileall, JSON
  validation for gate artifacts, and `git diff --check` must pass before merge.

## Scope Boundaries

In scope:

- HMI HTML/CSS/JS layout.
- HMI tests.
- Documentation and gate evidence.
- Browser/tablet screenshot evidence.

Out of scope:

- Live camera enablement.
- Camera SDK loading.
- Raw image/media ingestion.
- Model weights, model binaries, model deserialization, or inference runtime.
- Training code or notebooks.
- Product spec approval.
- QC/SOP tolerance approval.
- Production PASS/NG authority.
- Production auto-reject.
- Production deploy or release.

## Open Implementation Notes

- The current app has no approved live image source. The first implementation
  should render an image well and overlay normalized detector bbox metadata from
  replay/shadow observations.
- Real camera frames can later replace the placeholder only after the hardware
  and camera readiness gate opens.
- The previous detailed HMI panels should move below the primary viewport and
  stay available for audit/debug evidence.
