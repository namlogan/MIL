# FLANGE QC App V2 SOP Rule Registry

## Status

This registry is bootstrapped from the attached kickoff ZIP reviewed on
2026-06-02:

```text
/Users/mac/Desktop/flange_project_kickoff_docs.zip
```

Primary source file reviewed:

```text
.ai-factory/rules/product.md
```

The rules are compatible with the MIL fail-closed workflow, but they are not
production-approved SOP authority until the original SOP/product source and
QC/domain owner approval are recorded.

## Product Spec Source

Draft machine-readable product specs now live at:

```text
configs/flange_qc_v2/product_specs.bootstrap.json
```

The config includes these kickoff ZIP groups:

| Group | Product IDs | Tolerance summary |
|---|---|---|
| Standard | 611, 612, 613, 621, 622, 623, 633, 696, 697, 589, 590, 717, 718, 626, 627, 525, 899, 842, 509, 572, 406, 416, 411, 412, 421, 422, 434, 496, 497, 481 | Length +0/-0.75 in; width +/-0.5 in |
| M-series | M405, M407, M415, M417, M410, M420, M874, M571, M625, M716, M161, M162, M163 | Length +/-0.5 in; width +/-0.5 in |
| Items 695 and 587 | 695, 587 | Length +0/-0.75 in; width +/-0.5 in |
| Item 874 | 874 | Length +/-0.5 in; width +/-0.5 in |
| Item 963 | 963 | Length +0/-0.75 in; width +/-0.5 in |
| Item 445 | 445 | Length +0/-0.75 in; width +/-0.5 in |
| Items M435, M436, M437 | M435, M436, M437 | Length +0.25/-0.5 in; width +0.25/-0.75 in |
| Item M573 | M573 | Length +0.75/-0 in; width +/-0.5 in |

Implementation must not hardcode these values in service code. Unknown product
or unknown size must return `BLOCKED`.

## Core Rule IDs

| Rule ID | Phase | Rule | Production authority |
|---|---|---|---|
| M1-SOP-6.1-LENGTH-001 | PHASE_1 | Measure 3 length points, persist raw points and aggregate | Deterministic after calibration and approved config |
| M1-SOP-6.1-WIDTH-001 | PHASE_1 | Measure 3 width points, persist raw points and aggregate | Deterministic after calibration and approved config |
| M1-SOP-6.1-DIAGONAL-001 | PHASE_2 | Measure 2 diagonals and persist values in inches | Deterministic after calibration |
| M1-SOP-6.1-DIAGONAL-002 | PHASE_2 | Diagonal deviation greater than 0.5 in is `NG` | Deterministic after calibration |
| M1-SOP-6.4-PUNCH-MARK-001 | PHASE_3 | Top has 4 corner marks and 2 mid-width marks | Model/vision dependent until approved |
| M1-SOP-6.2-PUNCH-OFFSET-001 | PHASE_3 | Punch mark offset greater than 0.25 in is `NG` | Model/vision dependent until approved |
| M1-SOP-7.3-SEAM-CURVATURE-001 | PHASE_4 | Seam edge curvature must be <= 0.5 in | Post-MVP unless explicitly enabled |
| M1-SOP-7.3-CORNER-BEND-001 | PHASE_4 | Corner bend <= 0.25 in standard, <= 0.75 in for M695UN/M587UN | Post-MVP unless explicitly enabled |
| M1-SOP-9.2-SKIPPED-STITCH-001 | PHASE_4 | Skipped/loose stitches unacceptable | Assist or not evaluated until approved |
| M1-SOP-9.1-TORN-TOP-001 | PHASE_4 | Visible tear unacceptable | Assist or not evaluated until approved |
| M1-SOP-9.3-FABRIC-DEFECT-001 | PHASE_4 | Fabric defect unacceptable | Assist or not evaluated until approved |
| M1-SOP-9.4-FABRIC-FOLD-001 | PHASE_4 | Fabric folding during sewing unacceptable | Assist or not evaluated until approved |
| M1-SOP-9.5-FOAM-GAP-001 | PHASE_4 | Foam joint gap must be <= 0.5 in | Post-MVP unless explicitly enabled |
| M1-SOP-8.WRINKLE-* | PHASE_4 | Product-specific wrinkle rules | Out of MVP |

## Safe State Rules

- Unknown product returns `BLOCKED`.
- Unknown size returns `BLOCKED`.
- Missing product spec returns `BLOCKED`.
- Missing or pending calibration returns `BLOCKED`.
- Missing required length, width, or diagonal points returns `BLOCKED`.
- Missing model returns `NOT_EVALUATED`, `ASSIST`, or `BLOCKED` for model-dependent rules.
- Detector observations never decide final PASS/NG directly.
- `NOT_EVALUATED` must never be mapped to `PASS`.

## Open Rule Questions

- Confirm whether items 963 and 445 are in first pilot scope.
- Confirm aggregate method for length and width: average, min/max envelope, or all-points-must-pass.
- Map `M695UN` and `M587UN` to canonical product IDs.
- Confirm whether diagonal deviation uses corrected top boundary or raw detected corners.
