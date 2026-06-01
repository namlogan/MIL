# wm_task_context_pack

Purpose: build the short agent context pack for a Codex worker.

Pack sections:

1. Task goal
2. Allowed files
3. Restricted files
4. Relevant approved memories
5. Required source docs
6. Required test commands
7. Handoff requirements

Rules:

- Keep memory `top_k` between 5 and 10.
- Do not include candidate memory.
- Do not include secrets, raw artifacts, raw transcripts, or chain-of-thought.
- Context helps the agent navigate source-of-truth documents; it does not
  replace those documents.
