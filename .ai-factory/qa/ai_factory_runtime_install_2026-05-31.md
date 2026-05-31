# AI Factory Runtime Install Evidence

Date: 2026-05-31
Issue: #16
Branch: `agent/16-ai-factory-runtime-config`

## Installed Runtime Contracts

- `.ai-factory/runtime/agents.json`
- `.ai-factory/runtime/workflows.json`
- `.ai-factory/runtime/evidence.json`
- `.ai-factory/runtime/environment.json`
- `scripts/ai-factory/bootstrap_runtime.py`

## Verification Commands

```bash
python3 scripts/ai-factory/bootstrap_runtime.py --check
python3 scripts/ai-factory/bootstrap_runtime.py --check --check-tools
python3 scripts/agent-gate/validate_ai_factory.py --self-test
python3 -m unittest discover -s tests -v
python3 scripts/windmill/validate_windmill_project.py --self-test
python3 -m compileall -q scripts tests f
git diff --check
wmill --workspace mil-local sync push --dry-run --includes 'f/mil/**'
```

## Result

All commands completed successfully in the local workspace. Windmill file-as-code stayed in sync with the local Windmill workspace with `0 changes to apply`.

## Residual Risks

- GitHub webhook routing into Windmill is still tracked separately in issue #4.
- Auggie non-interactive execution remains blocked by account policy and is still tracked in issue #3.
