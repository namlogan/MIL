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

## Implementation Registry

Bootstrap-safe rule and reason-code metadata lives in:

```text
apps/flange_qc_v2/sop_registry.py
```

This module provides lookup metadata only. It does not resolve product
tolerances, run a production PASS/NG decision engine, enable live camera/model
behavior, or grant production SOP authority. Model-dependent and post-MVP rules
return safe fallback states such as `ASSIST`, `NOT_EVALUATED`, or `BLOCKED`
until later approval gates provide evidence.

Bootstrap shadow decision evaluation lives in:

```text
apps/flange_qc_v2/decision_engine.py
```

The current engine can emit shadow Phase 1 length/width evidence and shadow
Phase 2 diagonal-deviation evidence after product spec, calibration, and
geometry blockers clear. Phase 1 uses an explicit
`all_points_must_pass_bootstrap` aggregate assumption so any length or width
point outside the configured tolerance produces shadow `NG` evidence. This is a
conservative bootstrap behavior for tests and QC comparison only; production
authority remains gated by product spec approval, QC/SOP tolerance approval, and
release approval.

The engine also emits registry-driven safe fallback results for Phase 3 and
Phase 4 rules. Model/vision-dependent rules return `ASSIST` with
`MODEL_REVIEW_REQUIRED`, while disabled post-MVP rules return `NOT_EVALUATED`
with `RULE_POST_MVP_DISABLED`. These fallback states never map to `PASS` and do
not load models, run inference, enable camera hardware, or grant production
authority.

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
- Length or width evidence outside product tolerance can return shadow `NG` in
  phase 1 with `LENGTH_OUT_OF_TOLERANCE` or `WIDTH_OUT_OF_TOLERANCE`, but
  production authority remains gated by QC/SOP tolerance approval.
- Diagonal deviation greater than 0.5 inch can return shadow `NG` evidence in
  phase 2, but production authority remains gated by QC/SOP tolerance approval.
- Missing Phase 3 model observations return `NOT_EVALUATED` with `MODEL_MISSING`.
- Phase 3 model/vision rules consume sanitized detector observations as
  shadow-only review evidence. Relevant observations return `ASSIST` with
  `MODEL_REVIEW_REQUIRED`, bbox/confidence evidence, and
  `MODEL_APPROVAL_REQUIRED`; they never emit `PASS` or `NG`.
- Phase 4 post-MVP rules currently return `NOT_EVALUATED`, while Phase 4
  review-dependent rules return `ASSIST`.
- Detector observations never decide final PASS/NG directly.
- `NOT_EVALUATED` must never be mapped to `PASS`.

## Open Rule Questions

- Confirm whether items 963 and 445 are in first pilot scope.
- Confirm aggregate method for length and width: average, min/max envelope, or
  all-points-must-pass. Current implementation is shadow-only
  `all_points_must_pass_bootstrap`.
- Map `M695UN` and `M587UN` to canonical product IDs.
- Confirm whether diagonal deviation uses corrected top boundary or raw detected corners.
