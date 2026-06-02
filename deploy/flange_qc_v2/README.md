# FLANGE QC v2 Deployment Scaffold

This directory is a validation scaffold only. It documents local replay,
Jetson shadow, and RTX shadow targets without enabling deployment authority.

Validate the plan:

```bash
python3 scripts/deploy/validate_flange_qc_v2_deploy_plan.py --plan deploy/flange_qc_v2/deploy_plan.json
```

The checked-in scaffold must remain:

- manual and disabled
- free of literal secrets or credential values
- free of production deploy commands
- free of live camera, raw media, model weights, and TensorRT artifacts
- blocked on target, hardware, production release, and QC/SOP approvals

Rollback is a normal PR revert because this scaffold does not change runtime
infrastructure, hardware state, raw media, migrations, or release state.
