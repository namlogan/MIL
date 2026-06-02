# FLANGE QC V2 Product Specs Approval Request

## Request

Please review the draft product dimensions and tolerances imported from the
kickoff ZIP into:

```text
configs/flange_qc_v2/product_specs.bootstrap.json
```

Source reviewed by Codex:

```text
/Users/mac/Desktop/flange_project_kickoff_docs.zip:.ai-factory/rules/product.md
```

## Required Decision

- approver_name:
- approver_role:
- source_sop_revision:
- decision: pending
- decision_date:
- notes:

## Decision Options

- `approved_for_bootstrap_tests`: values may be used for deterministic unit and
  replay tests, but not production release.
- `approved_for_shadow_mode`: values may be used in shadow-mode evidence with
  manual QC comparison.
- `rejected_needs_revision`: values must be corrected before use.
- `blocked_needs_original_sop`: original SOP/product source is required before
  approval.

## Current Restrictions

- Draft specs must not drive production PASS/NG decisions.
- Unknown product or size must remain `BLOCKED`.
- Product dimensions and tolerances must not be hardcoded in service code.
- Model-dependent punch, seam, corner, and defect behavior remains `ASSIST`,
  `NOT_EVALUATED`, or blocked until separately approved.

## Bootstrap Resolver

Runtime draft config validation and lookup lives in:

```text
apps/flange_qc_v2/product_specs.py
```

The resolver may be used for bootstrap unit and replay-test setup. It carries
the config approval status into the result and returns `production_authority:
false` for the current draft config. Known products and sizes expose nominal
dimensions and tolerances, but the decision remains `BLOCKED` until approval
evidence exists. Unknown products and sizes also return `BLOCKED` with stable
reason codes.
