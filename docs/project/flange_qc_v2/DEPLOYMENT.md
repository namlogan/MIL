# FLANGE QC App V2 Deployment

## Environments

| Environment | Purpose | Owner | Runtime |
|---|---|---|---|
| local | Development and replay smoke | Engineering/operator | Developer workstation |
| CI | Unit, contract, integration, replay checks | GitHub Actions | No camera/GPU required |
| staging | Shadow-mode validation | Product owner + engineering | Jetson/RTX or server preview |
| production | Factory use after approval | Product owner | Jetson/RTX deployment |

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
6. Confirm audit DB writes and HMI/WebSocket output.
7. Attach release and rollback evidence.
8. Request human release approval.

## Rollback

Production rollout must support reverting to the prior app artifact, disabling
live camera ingestion, returning to replay/shadow-only mode, and preserving audit
evidence for review.

## Observability

Minimum signals:

- App health endpoint.
- Inspection decision counts by state and reason code.
- Audit DB write success/failure.
- Replay smoke result.
- Calibration state.
- Camera/model availability.
- Operator feedback volume and unresolved corrections.
