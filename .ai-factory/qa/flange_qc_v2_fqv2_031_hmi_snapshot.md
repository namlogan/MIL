# FQV2-031 HMI Browser Snapshot

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
  "observationState": "present",
  "detectorText": "punch_markASSISTconfidence: 0.87bbox: 0.42, 0.25, 0.12, 0.08model_ref: registry://flange-qc-v2/detector/punch-mark/2026-06-02evidence_ref: templates/flange_qc_v2/artifact_intake/evaluation_report.json",
  "artifactStatus": "valid with warning: camera boundary remains disabled; open hardware readiness before live capture",
  "shadowReady": "true",
  "connection": "closed",
  "panels": [
    "Inspection status",
    "SOP phase results",
    "Artifact intake readiness",
    "Detector observations"
  ]
}
```

Screenshot:

```text
.ai-factory/qa/flange_qc_v2_fqv2_031_hmi.png
```

Residual browser note:

The temporary stdlib HTTP server used for local QA does not implement WebSocket
upgrade, so the in-app browser console reported one `ws://127.0.0.1:8765/ws/inspection`
handshake failure. The HMI still rendered through HTTP replay/artifact refresh,
and the production ASGI app keeps the `/ws/inspection` WebSocket handler covered
by `tests/flange_qc_v2/test_hmi_stream.py`.
