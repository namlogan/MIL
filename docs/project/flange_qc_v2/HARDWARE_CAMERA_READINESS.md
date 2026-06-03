# Flange QC V2 Hardware Camera Readiness

## Current Status

FQV2-015 is approved for disabled no-hardware boundary work only. The app must
continue to run in CI and local bootstrap without a camera, SDK, credentials,
raw media, GPU, model weights, or production datasets.

Camera hardware/readiness is now the first gate in the active
`machine_vision` real-runtime SOP workstream. Demo-only replay/HMI work is
frozen except for regression fixes, evidence corrections, policy repairs, or
owner-approved emergency unblocks.

The current boundary lives in:

```text
apps/flange_qc_v2/camera.py
contracts/flange_qc_v2/camera/camera_boundary.schema.json
```

It is intentionally disabled:

- `enabled`: `false`
- `live_capture_enabled`: `false`
- `sdk_loaded`: `false`
- `credentials_configured`: `false`
- `production_authority`: `false`

## Required Before Live Camera Work

Live camera work remains blocked until the owner/engineering operator approves:

- Hikrobot camera model.
- Lens and working distance.
- Lighting layout and expected lux/stability.
- Mounting position and fixture assumptions.
- Trigger/source mode.
- Resolution and FPS expectations.
- Network/USB topology.
- Whether any credentials are required.
- Calibration fixture and acceptance evidence.
- Rollback path to replay/shadow-only mode.

The next DoR-ready implementation issue should capture those items as evidence
before any live SDK import, live capture, calibration approval, geometry
authority, product-spec authority, or advanced model defect work begins.

## Restricted Until Approval

- Importing or vendoring a Hikrobot SDK.
- Loading camera SDK modules at runtime.
- Configuring camera credentials or secrets.
- Capturing live frames.
- Storing raw media or customer/factory images.
- Enabling production PASS/NG decisions from camera evidence.
- Deploying to staging or production with live camera ingestion.

## Rollback

Revert the FQV2-015 PR to remove the camera boundary, schema/tests, docs, and
gate evidence. Because this boundary is disabled-only, rollback does not require
data migration, secret rotation, raw media cleanup, or hardware state changes.
