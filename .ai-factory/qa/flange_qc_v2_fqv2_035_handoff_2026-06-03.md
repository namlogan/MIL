# FQV2-035 QA Handoff: QC Tablet SOP Scope Strip

## Source

- GitHub issue: https://github.com/namlogan/MIL/issues/127
- Branch: `agent/127-qc-tablet-sop-scopes`
- Task: FQV2-035

## Files Changed

- `apps/flange_qc_v2/static/hmi.html`
- `tests/flange_qc_v2/test_hmi_screen.py`
- `docs/project/flange_qc_v2/USER_FLOWS.md`
- `docs/project/flange_qc_v2/DATA_MODEL.md`
- `docs/project/flange_qc_v2/TEST_STRATEGY.md`
- `.ai-factory/gates/flange_qc_v2_fqv2_035_dor.json`
- `.ai-factory/qa/flange_qc_v2_fqv2_035_handoff_2026-06-03.md`
- `.ai-factory/qa/flange_qc_v2_fqv2_035_hmi_snapshot.md`
- `.ai-factory/qa/flange_qc_v2_fqv2_035_hmi_scope_strip.png`

## Rules Applied

- One task per branch.
- GitHub issue is source of truth for requirement, acceptance criteria, and
  allowed paths.
- TDD RED/GREEN checkpoints were used before implementation.
- HMI uses existing replay snapshot, measurements, phase results, detector
  observations, and feedback contract only.
- No backend authority change, production PASS/NG authority, product spec
  approval, QC/SOP tolerance approval, model runtime/training, model promotion,
  raw media/data, live camera enablement, camera SDK loading, destructive
  migration, deploy, or release is introduced.

## Implementation Notes

- Replaced the four-chip top strip with a three-part scope strip.
- Product number is now a smaller first chip.
- Measurement SOP scope renders independent `OK`, `CHECK`, or `REVIEW` state
  plus measured length/width ranges.
- Stitch SOP scope renders independent `OK`, `CHECK`, or `REVIEW` state plus
  suspected observation label/confidence.
- The overall banner can remain red `CHECK` while measurement remains green
  `OK`, so QC focuses on the suspected stitch/defect area only.

## Tests Run

- RED: `python3 -m unittest tests.flange_qc_v2.test_hmi_screen -v` failed
  before implementation because HMI lacked SOP scope card ids and helper names.
- GREEN: `python3 -m unittest tests.flange_qc_v2.test_hmi_screen -v` passed,
  9 tests.
- `python3 -m json.tool .ai-factory/gates/flange_qc_v2_fqv2_035_dor.json >/dev/null`
  passed.
- `git diff --check` passed.
- `python3 -m compileall -q apps/flange_qc_v2 tests/flange_qc_v2` passed.
- `python3 -m unittest discover -s tests/flange_qc_v2 -v` passed, 129 tests.
- `python3 scripts/product-ci/run_product_checks.py` passed.
- `python3 -m unittest discover -s tests -v` passed, 196 tests.
- Browser evidence on `http://127.0.0.1:8765/hmi` at `1024x768` with
  template artifact intake showed banner `CHECK`, measurement `OK`
  (`L 74.90-75.10 / W 37.40-37.60 inch`), and stitch `CHECK`
  (`punch_mark / 0.87`).
- Browser snapshot artifact:
  `.ai-factory/qa/flange_qc_v2_fqv2_035_hmi_snapshot.md`.
- Browser screenshot artifact:
  `.ai-factory/qa/flange_qc_v2_fqv2_035_hmi_scope_strip.png`.

## Residual Risks

- Browser verification used no-camera synthetic/replay evidence, not live
  hardware.
- Measurement scope uses current measurement payload values for display. Product
  spec approval and production tolerance authority remain human-gated below.
- Detector observations remain review-only and cannot decide final production
  PASS/NG.

## Rollback

Revert the FQV2-035 PR to restore the previous QC tablet top strip. Existing
backend replay, decision engine, detector bridge, artifact intake, SOP
drilldown, and feedback contracts remain valid.
