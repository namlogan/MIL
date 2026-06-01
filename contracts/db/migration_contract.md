# Migration Contract

Database changes must be designed before repositories, services, or API code
depend on them.

## Required Fields

- Migration ID and owner.
- Linked issue or PR.
- Forward migration plan.
- Rollback or forward-fix plan.
- Data backfill plan, if needed.
- Expected lock, downtime, or performance impact.
- Compatibility strategy for old and new application versions.
- Test command and fixture evidence.
- Human approval for destructive changes.

## Block Conditions

Block merge when a migration deletes data without approval, changes retention
behavior, lacks rollback or forward-fix strategy, or has no compatibility plan.
