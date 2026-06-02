# FLANGE QC App V2 SOP Rule Registry

## Status

This registry is bootstrapped from the pasted intake brief. It must be reconciled
against original SOP documents and approved by the QC/domain owner before
production use.

## Core Rules

| Rule ID | Phase | Rule | Production authority |
|---|---|---|---|
| SOP-GEOM-001 | PHASE_1 | Capture 3 length points | Deterministic after calibration |
| SOP-GEOM-002 | PHASE_1 | Capture 3 width points | Deterministic after calibration |
| SOP-GEOM-003 | PHASE_2 | Capture 2 diagonals | Deterministic after calibration |
| SOP-GEOM-004 | PHASE_2 | Diagonal deviation greater than 0.5 inch is NG | Deterministic after calibration |
| SOP-SPEC-001 | PHASE_1 | Apply product-specific width/length tolerance | Requires approved product spec |
| SOP-MARK-001 | PHASE_3 | Punch mark at 4 corners and 2 mid-width locations | Model/vision dependent until approved |
| SOP-MARK-002 | PHASE_3 | Mark deviation tolerance is +/- 0.25 inch | Model/vision dependent until approved |
| SOP-SEAM-001 | PHASE_4 | Seam curvature threshold is 0.5 inch | Model/vision dependent until approved |
| SOP-CORNER-001 | PHASE_4 | Corner bend threshold is 0.25 inch, with special group threshold 0.75 inch | Model/vision dependent until approved |
| SOP-DEFECT-001 | PHASE_4 | Skipped stitch, loose stitch, torn, dirty, fabric defect, fabric fold, foam gap | Model/vision dependent until approved |

## Safe State Rules

- Unknown product returns `BLOCKED`.
- Missing product spec returns `BLOCKED`.
- Missing or pending calibration returns `BLOCKED`.
- Missing model returns `NOT_EVALUATED`, `ASSIST`, or `BLOCKED` for model-dependent rules.
- Detector observations never decide PASS/NG directly.
