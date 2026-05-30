# MIL External Blockers

Status as of 2026-05-30.

The repo-local agent framework is in place on PR #2, and local tests cover all four specified flow contracts. The remaining items below require account, platform, or credential changes outside the repository.

## GitHub Branch Protection

Tracking issue: https://github.com/namlogan/MIL/issues/5

Current state:

- `main` exists and CI runs.
- `ai-gate/final-review` can be published through the commit status API.
- GitHub branch protection API returned HTTP 403 because this private repository requires GitHub Pro or public visibility for branch protection on the current account.

Required decision:

- Upgrade the GitHub plan, move the repo under an org/plan with branch protection, or explicitly approve making the repo public.

## Auggie Automated Worker

Tracking issue: https://github.com/namlogan/MIL/issues/3

Current state:

- Auggie CLI is installed.
- `auggie --version` works.
- Non-interactive `auggie --print` execution is blocked by account policy.
- Local Augment credential config can be validated with `scripts/agent-flow/check_augment_config.py`.
- Augment MCP can be started with credentials, but Codex may still require MCP tool-call approval depending on the client/session.

Required decision:

- Enable Auggie non-interactive mode, provide an approved SDK/API path, or keep Auggie as a manual advisory lane until access changes.

## Windmill Cockpit

Tracking issue: https://github.com/namlogan/MIL/issues/4

Current state:

- Repo flow contracts exist under `.windmill/flows/`.
- Local dry-run harness exists under `scripts/agent-flow/`.
- Required secret names are documented.
- No Windmill workspace URL, route, webhook, or secret has been configured yet.

Required decision:

- Provision Windmill, add least-privilege secrets, and connect GitHub webhooks to the documented flows.
