# MIL AI Factory Rules

AI Factory 2.x-compatible top-level axioms. Area-specific rules live under
`.ai-factory/rules/` and are registered in `.ai-factory/config.yaml`.

Rule priority: `rules.<area> > rules/base.md > paths.rules_file`.

## Rules

- Start work from a GitHub issue or approved local task file.
- Keep one task per branch and keep implementation inside `allowed_files`.
- Codex is the only implementation worker; Augment, Mem0, and Auggie are context, memory, or advisory lanes only.
- Run implementation through the configured `codex_worker` runner or an explicitly approved local equivalent.
- Write tests or record why tests are not applicable.
- Record developer handoff, checks, risks, rollback note, and worker evidence in the PR or `.ai-factory/qa/`.
- Emit the final machine-readable `aif-gate-result` block after the human summary.
- Allowed MIL merge decisions are `APPROVE_MERGE`, `REQUEST_CHANGES`, `REJECT`, and `BLOCKED_NEEDS_HUMAN`.
- Never merge, deploy, bypass branch protection, or approve restricted work without human approval.
- Never store secrets, raw tokens, customer data, raw proprietary source, or raw transcripts in memory.
- Restricted changes include production deploy behavior, production secrets, billing, customer data retention/deletion, auth boundaries, destructive migrations, legal/compliance behavior, and safety-critical behavior.
