# wm_project_intake_gate

Purpose: block agent work until the project intake package is complete.

Inputs:
- Project docs under `docs/project/`
- `.ai-factory/DESCRIPTION.md`
- `.ai-factory/ARCHITECTURE.md`
- `.ai-factory/RULES.md`

Checks:
- Required intake docs exist and are not thin.
- Business objective, users, MVP, out-of-scope, success metrics, risks,
  security concerns, deployment assumptions, and decision owner are present.
- `python3 scripts/project-intake/validate_project_intake.py` passes.

Outputs:
- `PROJECT_INTAKE_READY`
- `PROJECT_INTAKE_BLOCKED`
