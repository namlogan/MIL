# Project Bootstrap Template

Use this template when applying the framework to a new repo.

Required output:
- Project docs copied from `docs/templates/project/`.
- Delivery OS docs copied from `.ai-factory/`.
- Contract skeleton copied from `contracts/`.
- Product CI profile chosen.
- Release manifest template copied.
- Memory namespace configured.
- Operator dashboard command documented.

Recommended command sequence:

```bash
python3 scripts/project-intake/validate_project_intake.py
python3 scripts/delivery/validate_delivery_os.py --self-test
python3 scripts/contracts/validate_contracts.py --self-test
```
