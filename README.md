# MIL

MIL is initialized with an agent-first software delivery control plane.

Current scaffold:

- GitHub is the source of truth for issues, PRs, CI, and merge history.
- Windmill is the cockpit for webhook handling, approvals, logs, retries, and worker routing.
- AI Factory artifacts define rules, plans, QA evidence, and final gate results.
- Codex is the only implementation and test worker.
- Augment provides codebase index/context to Codex sessions.
- Mem0 is the optional long-term memory layer for sanitized project/task context.
- Auggie is optional supervised advisory support only; it does not write code.

Start here:

- [Agent workflow](AGENTS.md)
- [Delivery Operating Model](.ai-factory/DELIVERY_OPERATING_MODEL.md)
- [Definition of Ready](.ai-factory/DEFINITION_OF_READY.md)
- [Definition of Done](.ai-factory/DEFINITION_OF_DONE.md)
- [Quality Gates](.ai-factory/QUALITY_GATES.md)
- [Release Policy](.ai-factory/RELEASE_POLICY.md)
- [Source of Truth Matrix](.ai-factory/SOURCE_OF_TRUTH_MATRIX.md)
- [New project startup pipeline](docs/runbooks/new_project_startup_pipeline.md)
- [Operating model](docs/agent-operating-model.md)
- [Workflow and starter kit](docs/agent-factory-workflow-and-starter.md)
- [Solo agent SDLC runbook](docs/solo-agent-sdlc-runbook.md)
- [Project intake template set](docs/templates/project/PRD.md)
- [Contract-first skeleton](contracts/README.md)
- [Golden path templates](templates/project_bootstrap/README.md)
- [Branch protection guide](docs/branch-protection.md)
- [External blockers](docs/external-blockers.md)
- [Augment setup](docs/augment-setup.md)
- [Mem0 memory layer](docs/mem0-memory-layer.md)
- [Deployment](docs/project/DEPLOYMENT.md)
- [Codex worker runner](docs/codex-worker-runner.md)
- [Auggie supervised loop](docs/auggie-human-loop-runbook.md)
- [Windmill coding dispatch](.windmill/flows/coding_agent_dispatch.md)
- [AI Factory rules](.ai-factory/RULES.md)
- [Windmill cockpit notes](.windmill/README.md)
- [Portable backup and migration runbook](docs/portable-agent-factory-runbook.md)

Daily operator command:

```bash
python3 scripts/operator/daily_status.py
```

Temporary ngrok endpoint check:

```bash
python3 scripts/windmill/check_public_endpoint.py \
  --public-url https://<assigned-name>.ngrok-free.dev/mil/github-webhook
```

New project intake check:

```bash
python3 scripts/project-intake/validate_project_intake.py
```

Delivery framework checks:

```bash
python3 scripts/delivery/validate_delivery_os.py --self-test
python3 scripts/contracts/validate_contracts.py --self-test
python3 scripts/operator/sdlc_metrics_report.py --json
```
