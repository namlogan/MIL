# wm_memory_conflict_review

Purpose: review memory that conflicts with a higher-priority source of truth.

Priority:

1. Compliance/legal/security policy
2. Current PRD/spec/SOP/contract
3. Git code and tests
4. Approved ADR
5. Approved memory
6. Candidate memory
7. Conversation context

Outputs:

- mark memory `superseded`
- mark memory `needs_review`
- write `deprecated_decision` candidate
- open follow-up issue when source docs are ambiguous
