# Escalation Policy

Automation must stop and request human approval when the framework cannot make
a safe decision from committed source-of-truth artifacts.

## Mandatory Escalation

- Security or compliance behavior changes.
- Public API, event, payload, or database contract changes.
- Destructive migration, data deletion, or data retention change.
- Production deployment, production secret, or credential change.
- Billing, entitlement, or customer-impacting behavior.
- Model promotion, dataset policy, or artifact retention change.
- Business acceptance criteria or release decision change.
- Source-of-truth documentation conflict.
- Memory conflict involving architecture, security, compliance, or product
  policy.

## Decision Format

Escalation evidence must include task ID, affected area, decision needed,
options considered, recommended option, risk of doing nothing, rollback impact,
and source references.

## Allowed Outcomes

- `APPROVED_WITH_SCOPE`
- `REQUEST_MORE_EVIDENCE`
- `REJECTED`
- `DEFERRED`

The approved scope must be copied into the issue or PR before agent work
continues.
