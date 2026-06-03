# FQV2-035 HMI SOP Scope Strip Browser Snapshot

## Target

- URL: `http://127.0.0.1:8765/hmi`
- Viewport evidence size: `1024x768`
- Artifact intake: `templates/flange_qc_v2/artifact_intake`
- Screenshot: `.ai-factory/qa/flange_qc_v2_fqv2_035_hmi_scope_strip.png`

## Observed First Viewport

- Page title: `Flange QC HMI`
- QC tablet viewport state: `check`
- Operator banner: `CHECK`
- Operator action: `Inspect suspected area`
- Product: `611`
- Measurement SOP scope:
  - State: `ok`
  - Status: `OK`
  - Detail: `L 74.90-75.10 / W 37.40-37.60 inch`
- Stitch SOP scope:
  - State: `check`
  - Status: `CHECK`
  - Detail: `punch_mark / 0.87`
- Alarm feedback buttons visible: `Alert correct`, `False alarm`

## Compatibility Checks

- SOP drilldown remains below the first viewport.
- Detector observations remain below the first viewport.
- Artifact intake and feedback panels remain below the first viewport.
- No live camera, raw image, production data, deployment, release, model runtime,
  or production authority action was performed.
