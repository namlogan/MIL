# AI Delivery Coordinator Mode Design

Date: 2026-06-02

## Purpose

Make the MIL framework operate as an AI-coordinated delivery system instead of
asking the owner to manually approve each routine PR. The owner should approve
policy, restricted exceptions, QC/SOP authority, and production release, while
routine ready tasks flow through Codex workers, Codex QA, merge-controller
policy, and GitHub auto-merge.

## Approved Direction

The owner approved AI Delivery Coordinator mode in chat on 2026-06-02.

The approved operating model is:

- AI Delivery Coordinator owns routine task routing and PR progression.
- Codex remains the only implementation worker.
- Augment remains read-only context.
- Mem0 remains sanitized memory context and candidate writeback.
- Merge authority remains GitHub branch protection plus
  `merge-controller-policy`.
- Routine PRs do not require owner review when required checks, AI gate, policy
  gate, evidence, rollback, labels, and size limits pass.
- Owner review is required only for restricted changes, production release,
  QC/SOP approval, policy exceptions, repeated fix failures, or explicit hold.

## Coordinator Responsibilities

For issues:

- Check Definition of Ready evidence.
- Apply or recommend `agent:auto-build` for ready routine issues.
- Refuse dispatch when required scope, checks, rollback, or memory preflight is
  missing.
- Escalate restricted work instead of dispatching it.

For PRs:

- Check required evidence markers and restricted labels/paths.
- Apply or recommend `automerge:candidate` for routine PRs.
- Wait for required checks instead of asking the owner to review.
- Escalate when owner-only approval is required.
- Stop after two auto-fix iterations and request owner review.

## Human Approval Boundary

The coordinator must not approve:

- production deploy or release
- secrets or credential changes
- billing, auth boundary, customer data, legal, or compliance behavior
- destructive migrations
- safety-critical behavior
- QC/domain approval for product tolerances or SOP interpretation
- model promotion
- PRs over configured size or policy limits unless owner approval evidence exists

## Current FQV2 Implication

For `FQV2-001`, the correct next operating action is not to ask the owner to
merge manually. The coordinator should create or prepare the PR with routine
auto labels and let `control-plane`, `ai-gate/final-review`,
`merge-controller-policy`, and GitHub auto-merge handle the merge when checks
pass.

## Implementation Scope

This task adds a coordinator contract and docs. It does not deploy credentials,
merge existing branches, or bypass GitHub protections.

Expected deliverables:

- a local coordinator script with deterministic issue/PR policy decisions
- unit tests for routine vs restricted routing
- runtime agent/workflow docs that name the coordinator role
- operating docs that say routine PRs should not prompt the owner for manual
  approval

## Verification

Required checks:

- coordinator self-test
- unit tests
- framework validators
- full `unittest` suite
- `git diff --check`
