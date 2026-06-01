# wm_security_gate

Purpose: stop secret, auth, compliance, and data-risk changes until reviewed.

Checks:
- No raw secrets or tokens are introduced.
- Restricted files or environment behavior are declared.
- Credential changes use secret references, not literal values.
- Customer data, billing, auth, and retention changes have human approval.
- Memory candidates are scrubbed before writeback.

Security gate failure blocks merge and release.
