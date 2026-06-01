# wm_definition_of_ready_check

Purpose: block unclear work before it reaches a coding worker.

Required inputs:
- Task ID and source reference
- Goal and business reason
- Acceptance criteria
- Allowed files and restricted areas
- Expected checks
- Dependencies
- Rollback impact
- Memory preflight scope
- Handoff format

Outputs:
- `READY_FOR_AGENT`
- `BLOCKED_NEEDS_HUMAN`

No branch or worker may be created when this flow returns blocked.
