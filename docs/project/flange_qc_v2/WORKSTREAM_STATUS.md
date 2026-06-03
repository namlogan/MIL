# Flange QC V2 Workstream Status

## Demo-only V2 Workstream: Frozen

The replay/no-camera/HMI demo-only lane is frozen as of 2026-06-03. It remains
available as a regression baseline and rollback path, but it is no longer the
active implementation direction.

Allowed demo-only work is limited to:

- regression fixes;
- evidence corrections;
- security or policy repair;
- owner-approved emergency unblock.

Blocked demo-only work includes new replay-only polish, synthetic-only UI
expansion, and model defect work that bypasses the real-runtime SOP gates.

## Active Workstream: `machine_vision` Real-Runtime SOP

The active workstream is `machine_vision` real-runtime SOP. Its job is to move
from replay-ready app behavior to real camera/calibration/geometry/product-spec
evidence that can feed the app runtime through:

```text
POST /inspection/intake
```

This workstream has no production authority. It must remain fail-closed until
the required human gates pass.

## Priority Order

1. camera hardware/readiness evidence;
2. calibration evidence;
3. runtime geometry measurement evidence;
4. product specs and tolerance approval package;
5. full SOP rule gate;
6. advanced model defect work.

The advanced model defect work remains blocked until camera hardware/readiness
evidence, calibration evidence, runtime geometry measurement evidence, product
specs and tolerance approval package, and full SOP rule gate evidence are
recorded.

## Required Human Gates

- Product specs approval.
- QC/SOP tolerance approval.
- Camera hardware validation.
- Model promotion approval.
- Production release approval.

## Source Of Truth

The machine-readable workstream record lives in:

```text
.ai-factory/workstreams/flange_qc_v2_machine_vision.json
```

Future agent-runnable issues must cite that manifest when they touch camera,
calibration, geometry, product specs, SOP authority, model defect work, or
production release readiness.
