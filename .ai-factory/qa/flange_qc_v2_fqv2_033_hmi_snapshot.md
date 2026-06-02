# FQV2-033 HMI Browser Snapshot

Local target:

```text
http://127.0.0.1:8765/hmi
```

Environment:

```text
FLANGE_QC_V2_ARTIFACT_INTAKE_DIR=/Users/mac/Documents/MIL/templates/flange_qc_v2/artifact_intake
```

Verified browser state:

```json
{
  "title": "Flange QC HMI",
  "qcDeviceLayout": "rendered",
  "phaseOneHeading": "Phase 1 Dimensions",
  "phaseOneStatus": "REVIEW",
  "phaseOneDetail": "PHASE_1: BLOCKED; reasons: PRODUCT_SPEC_APPROVAL_MISSING, CALIBRATION_MISSING; authority: none",
  "phaseTwoHeading": "Phase 2 Stitch Watch",
  "phaseTwoStatus": "REVIEW",
  "phaseTwoDetail": "PHASE_2: BLOCKED; reasons: PRODUCT_SPEC_APPROVAL_MISSING, CALIBRATION_MISSING; authority: none",
  "phaseTwoStitchArea": "Suspected stitch area",
  "phaseTwoStitchStatus": "REVIEW",
  "phaseTwoTrafficState": "warn",
  "trafficMapping": {
    "PASS": "ok/green",
    "NG": "error/red",
    "reviewOrBlocked": "warn/amber"
  },
  "panels": [
    "Inspection status",
    "QC device phase layout",
    "SOP phase results",
    "Artifact intake readiness",
    "Detector shadow status",
    "Detector observations"
  ]
}
```

Screenshot:

```text
.ai-factory/qa/flange_qc_v2_fqv2_033_hmi.png
```

Residual browser note:

The temporary metadata HTTP server used for local QA does not implement
WebSocket upgrade, so the browser console reported one
`ws://127.0.0.1:8765/ws/inspection` handshake failure. The HMI still rendered
through HTTP replay/artifact/detector-status refresh, and the real ASGI app
keeps the `/ws/inspection` WebSocket handler covered by
`tests/flange_qc_v2/test_hmi_stream.py`.
