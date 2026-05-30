# MIL Agent Factory Design

Date: 2026-05-30
Status: approved for Approach A scaffold

## Goal

Initialize MIL with a repo-local agent control plane before application code exists. The first version should define how GitHub, Windmill, AI Factory, Codex, and Auggie cooperate without granting agents direct merge authority.

## Selected Approach

Approach A: scaffold the repository control plane first.

This creates documentation, rules, flow definitions, CI skeleton, and local gate scripts. It does not install or start Windmill, does not configure GitHub branch protection remotely, and does not assume a product stack.

## Architecture

GitHub is the source of truth for issues, pull requests, CI, reviews, and merge history.

Windmill is the cockpit for orchestration: webhooks, UI approvals, logs, retries, worker routing, and secrets.

AI Factory is the SDLC protocol layer: rules, plans, QA artifacts, and machine-readable gate results.

Codex is the implementation and test worker.

Auggie is the codebase-aware advisory reviewer and diagnosis worker.

GitHub branch protection is the hard merge boundary. AI can recommend merge, but GitHub must enforce required checks and approvals.

## Components

- `AGENTS.md`: operating contract for all agents.
- `.ai-factory/`: rules, configuration, plans, QA outputs, and gate artifacts.
- `.windmill/`: flow descriptions and worker group policy.
- `.github/`: pull request template and initial CI.
- `scripts/agent-gate/`: local scripts for extracting and evaluating gate results.
- `docs/`: operating model and branch protection guidance.

## Data Flow

```text
Issue -> Windmill flow -> Codex/Auggie worker -> PR -> CI -> AI gate -> branch protection -> human or bot merge
```

Windmill may comment, label, request approval, and publish status checks. It must not bypass GitHub branch protection.

## Error Handling

Automation should stop and request human review when:

- required issue fields are missing
- CI fails after two automated fix attempts
- the gate result is missing or malformed
- restricted areas are touched
- the branch contains unrelated changes

## Testing

The initial CI only validates the control-plane scripts. Application-specific tests should be added after the product stack is chosen.

## Non-Goals

- No Windmill server installation in this scaffold.
- No GitHub remote or branch protection mutation from local scripts.
- No application framework selection.
- No production deployment setup.

