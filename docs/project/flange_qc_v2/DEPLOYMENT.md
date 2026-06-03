# FLANGE QC App V2 Deployment

## Environments

| Environment | Purpose | Owner | Runtime |
|---|---|---|---|
| local | Development and replay smoke | Engineering/operator | Developer workstation |
| CI | Unit, contract, integration, replay checks | GitHub Actions | No camera/GPU required |
| staging | Shadow-mode validation | Product owner + engineering | Jetson/RTX or server preview |
| production | Factory use after approval | Product owner | Jetson/RTX deployment |

## Scaffold Status

Current deployment support is scaffold-only. The versioned plan lives at:

```text
deploy/flange_qc_v2/deploy_plan.json
```

Validate it with:

```bash
python3 scripts/deploy/validate_flange_qc_v2_deploy_plan.py --plan deploy/flange_qc_v2/deploy_plan.json
```

The checked-in plan covers local replay, Jetson shadow, and RTX shadow targets,
but keeps deploy provider, production deployment, live camera, raw media, and
secret requirements disabled. The first real deployment target remains open in
`docs/project/flange_qc_v2/OPEN_QUESTIONS.md` as `FQV2-Q-005`.

## Required Secrets

List secret names only after the target repo and deployment provider are confirmed.
Do not store literal values in Git, Memory0, Windmill logs, or agent prompts.

Potential secret references:

- Deployment provider token.
- Camera credential if required by hardware integration.
- Database backup credential if production DB moves beyond SQLite.
- GitHub/Windmill status publishing tokens for the SDLC control plane.

## Deploy Steps

1. Validate contracts and product config.
2. Run unit, contract, integration, and replay checks.
3. Build app artifact.
4. Deploy to staging or shadow-mode environment.
5. Run health and replay smoke.
6. Run a sanitized `/inspection/intake` smoke payload from the target camera or
   replay pipeline contract, without request-supplied config/model/data paths.
7. Confirm audit DB writes and HMI/WebSocket output.
8. Attach release and rollback evidence.
9. Request human release approval.

The scaffold validator does not execute any deploy step. Staging or production
deployment requires a separate release issue, release evidence, smoke evidence,
rollback evidence, and human release approval.

## Rollback

Production rollout must support reverting to the prior app artifact, disabling
live camera ingestion, returning to replay/shadow-only mode, and preserving audit
evidence for review.

Rollback for the current scaffold is a normal PR revert because it does not alter
runtime infrastructure, secrets, hardware state, raw media, migrations, or
release state.

## Observability

Minimum signals:

- App health endpoint.
- Inspection decision counts by state and reason code.
- Audit DB write success/failure.
- Replay smoke result.
- Runtime inspection intake smoke result.
- Calibration state.
- Camera/model availability.
- Operator feedback volume and unresolved corrections.
