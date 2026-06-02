# AI Delivery Coordinator Mode Evidence

Date: 2026-06-02

## Scope

This change codifies AI Delivery Coordinator mode for routine MIL delivery. It
does not merge current branches, deploy credentials, approve restricted changes,
or bypass branch protection.

## Decision

Routine PRs are coordinated by `ai_delivery_coordinator` and do not return to
the owner for manual review when Definition of Ready, Codex handoff evidence,
Codex QA, required checks, rollback evidence, merge-controller policy, and
branch protection pass.

Human approval remains required for restricted changes, production release,
QC/SOP approval, policy exceptions, explicit holds, or repeated auto-fix
failures.

## Tests Run

- `python3 -m unittest tests.test_delivery_coordinator -v`
- `python3 -m unittest tests.test_ai_delivery_coordinator_policy -v`
- `python3 -m unittest tests.test_mil_flow.MilFlowTests.test_delivery_coordinator_routes_routine_work_without_owner_review -v`
- `python3 scripts/agent-flow/delivery_coordinator.py --self-test`
- `python3 scripts/agent-flow/mil_flow.py --self-test`
- `python3 scripts/agent-gate/validate_ai_factory.py --self-test`
- `python3 scripts/ai-factory/bootstrap_runtime.py --check`
- `git diff --check`

## Residual Risks

- Actual GitHub label application still depends on the existing Windmill/GitHub
  token setup.
- Production release and restricted owner approval remain intentionally outside
  coordinator authority.
- Existing local task branches still need to be pushed or handed to the
  coordinator entry point; this change defines the operating mode and tested
  coordinator contract.

```aif-gate-result
{
  "schema_version": "2.0",
  "gate": "ai_delivery_coordinator_mode",
  "status": "pass",
  "blocking": false,
  "decision": "APPROVE_MERGE",
  "scope": "framework coordinator contract and docs",
  "reasons": [
    "routine_issue_routes_to_agent_auto_build",
    "routine_pr_routes_to_automerge_candidate",
    "restricted_issue_escalates_to_owner",
    "restricted_pr_escalates_to_owner",
    "runtime_agent_declared_without_code_or_merge_power",
    "workflow_declares_owner_exception_boundary"
  ],
  "tests": [
    "python3 -m unittest tests.test_delivery_coordinator -v",
    "python3 -m unittest tests.test_ai_delivery_coordinator_policy -v",
    "python3 scripts/agent-flow/delivery_coordinator.py --self-test",
    "python3 scripts/agent-gate/validate_ai_factory.py --self-test"
  ],
  "residual_risks": [
    "github_label_application_depends_on_configured_tokens",
    "production_release_still_requires_human_approval"
  ]
}
```
