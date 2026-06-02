# FQV2-032 HMI Browser Snapshot

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
  "detectorShadowStatus": "ready: manifest-detector",
  "detectorShadowReady": "true",
  "detectorShadowAdapter": "manifest-detector",
  "detectorShadowModelRef": "registry://flange-qc-v2/detector/punch-mark/2026-06-02",
  "detectorShadowLabels": "punch_mark, corner_mark",
  "detectorShadowApprovalStatus": "candidate",
  "detectorShadowAuthorityBlockers": "MODEL_APPROVAL_REQUIRED, PRODUCTION_APPROVAL_REQUIRED",
  "artifactStatus": "valid with warning: camera boundary remains disabled; open hardware readiness before live capture",
  "observationState": "present",
  "panels": [
    "Inspection status",
    "SOP phase results",
    "Artifact intake readiness",
    "Detector shadow status",
    "Detector observations"
  ]
}
```

Screenshot:

```text
.ai-factory/qa/flange_qc_v2_fqv2_032_hmi.png
```

Residual browser note:

The temporary metadata HTTP server used for local QA does not implement
WebSocket upgrade, so the browser console reported one
`ws://127.0.0.1:8765/ws/inspection` handshake failure. The HMI still rendered
through HTTP replay/artifact/detector-status refresh, and the production ASGI
app keeps the `/ws/inspection` WebSocket handler covered by
`tests/flange_qc_v2/test_hmi_stream.py`.
