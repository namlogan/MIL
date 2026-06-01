# wm_release_memory_writeback

Purpose: extract durable release lessons into Memory0 candidates.

Rules:
- Store distilled operational lessons only.
- Include release manifest, PR, or incident `source_ref`.
- Never store secrets, raw logs, raw customer data, raw code dumps, or raw
  transcripts.
- Write status must be `candidate`.
- Approval is separate and follows the memory review checklist.
