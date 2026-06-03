# FQV2-034 HMI Tablet Browser Snapshot

## Target

- URL: `http://127.0.0.1:8765/hmi`
- Viewport evidence size: `1024x768`
- Artifact intake: `templates/flange_qc_v2/artifact_intake`
- Screenshot: `.ai-factory/qa/flange_qc_v2_fqv2_034_hmi_tablet.png`

## Observed First Viewport

- Page title: `Flange QC HMI`
- QC tablet viewport state: `check`
- Operator banner state: `check`
- Operator label: `CHECK`
- Operator action: `Inspect suspected area`
- Measurement strip visible: product `611`, length `REVIEW`, width `REVIEW`, diagonal/stitch `CHECK`
- Suspected-region overlay visible: yes
- Suspected-region label: `punch_mark / 0.87`
- Alarm feedback buttons visible:
  - `Alert correct` -> `CONFIRM_BLOCKED`
  - `False alarm` -> `MARK_FALSE_POSITIVE`

## Compatibility Checks

- SOP phase-results detail panel remains present.
- Detector observations panel remains present.
- Artifact intake status panel remains present.
- Feedback form remains present.
- Browser console error logs: none observed during evidence capture.

## Notes

Temporary local metadata HTTP server was used for browser evidence because this
environment does not require a live camera or production ASGI deployment for
HMI static/replay verification. No live camera, raw image, model runtime,
production data, deployment, or release action was performed.
