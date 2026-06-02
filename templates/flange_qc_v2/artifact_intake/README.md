# Flange QC v2 Artifact Intake Template

Copy this directory to a working intake location, replace the metadata with the
real dataset/model/camera references, then validate it before opening the next
implementation issue.

Recommended local working copy:

```bash
mkdir -p .ai-factory/tmp/flange_qc_v2/intake-2026-06-02
cp templates/flange_qc_v2/artifact_intake/*.json .ai-factory/tmp/flange_qc_v2/intake-2026-06-02/
python3 scripts/flange_qc_v2/validate_artifact_intake.py \
  --intake-dir .ai-factory/tmp/flange_qc_v2/intake-2026-06-02
```

Do not put raw images, videos, datasets, notebooks, model weights, credentials,
or camera secrets in this bundle. The validator rejects common raw media/model
and secrets-like files.

Valid output with `ready.shadow_model_integration_issue=true` means a new
shadow model integration issue can be opened. Live camera implementation remains
blocked until the camera boundary is replaced by approved hardware readiness
evidence through the hardware gate.
