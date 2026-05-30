# MIL External Blockers

Status as of 2026-05-30.

The repo-local agent framework is in place on PR #2, and local tests cover all four specified flow contracts. The remaining items below require account, platform, or credential changes outside the repository.

## GitHub Branch Protection

Tracking issue: https://github.com/namlogan/MIL/issues/5

Current state:

- Repository visibility is public by Product Owner approval.
- `main` exists and CI runs.
- Branch protection is enabled for `main`.
- `control-plane` is required and branches must be up to date.
- Pull requests are required with zero required approvals for the solo-owner pilot.
- Force pushes and branch deletion are disabled.
- Conversation resolution is required.
- `ai-gate/final-review` can be published through the commit status API, but is not required yet because Windmill is not provisioned.

Required decision:

- After Windmill is provisioned, add `ai-gate/final-review` as a required status check.

## Auggie Automated Worker

Tracking issue: https://github.com/namlogan/MIL/issues/3

Current state:

- Auggie CLI is installed.
- `auggie --version` works.
- Non-interactive `auggie --print` execution is blocked by account policy.
- Local Augment credential config can be validated with `scripts/agent-flow/check_augment_config.py`.
- Augment MCP can be started with credentials, but Codex may still require MCP tool-call approval depending on the client/session.
- Supervised Auggie interactive review works through `scripts/agent-flow/auggie_interactive.sh`; Windmill should queue and record this lane rather than call `auggie --print`.

Required decision:

- Enable Auggie non-interactive mode, provide an approved SDK/API path, or keep Auggie as a manual advisory lane until access changes.

## Windmill Cockpit

Tracking issue: https://github.com/namlogan/MIL/issues/4

Current state:

- Windmill CLI is installed locally as `wmill` and reports version `1.712.0`.
- Repo flow contracts exist under `.windmill/flows/`.
- Deployable Windmill CLI project files exist in `wmill.yaml`, `wmill-lock.yaml`, and `f/mil/**`.
- `scripts/windmill/validate_windmill_project.py --self-test` validates the Windmill project files without credentials.
- Local dry-run harness exists under `scripts/agent-flow/`.
- Required secret names are documented.
- No active Windmill workspace profile, route, webhook, or secret has been configured yet.

Required decision:

- Provision Windmill, add least-privilege secrets, and connect GitHub webhooks to the documented flows.
