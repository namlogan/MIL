# wm_postmortem_to_memory

Purpose: convert reviewed incident and postmortem lessons into safe memory
candidates.

Rules:
- Store distilled operational lessons only.
- Include `source_ref` to incident, PR, release, or commit.
- Do not store raw logs, customer data, secrets, credentials, raw source, or
  transcripts.
- Architecture, product, security, and compliance lessons require approval
  before retrieval.

Output: memory candidates for Memory Gateway review.
