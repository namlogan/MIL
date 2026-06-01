# Context Pack

## Task

`<task goal>`

## Approved Decisions

- `[memory_id] <decision>`  
  Source: `<source_ref>`

## Constraints

- `<constraint from approved memory or source docs>`

## Known Lessons

- `[memory_id] <lesson>`  
  Source: `<source_ref>`

## Required Tests

- `<test command>`

## Source References

- `<PRD/spec/issue/ADR/test reference>`

Rules:

- Include only `status=approved` memory.
- Keep `top_k` between 5 and 10.
- Every memory item must include `source_ref`.
- Do not include secrets, raw artifacts, raw transcripts, or chain-of-thought.
