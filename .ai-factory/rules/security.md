# Security Rules

> Area rules for credentials, restricted changes, and sensitive operations.

## Rules

- Agents must not print, copy, commit, request, or store production secrets.
- All secrets must stay in GitHub or Windmill secret stores and be referenced by variable path or environment name only.
- Hardcoded API keys, tokens, passwords, private keys, and session cookies are blocking security violations.
- Use least-privilege worker credentials: read-only workers inspect, write workers push agent branches, merge workers merge only after protections pass, and release workers require human approval.
- Authentication, authorization, billing, customer data handling, destructive migrations, production deployment behavior, and legal/compliance changes require human approval before merge.
- Security gate findings with concrete secret exposure or auth boundary impact must block the PR.
