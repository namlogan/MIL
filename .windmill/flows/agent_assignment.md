# wm_agent_assignment

Purpose: assign exactly one coding worker to one ready task.

Inputs:
- Definition of Ready result.
- Task context pack.
- Allowed files and restricted areas.
- Required tests and gate routing.

Rules:
- Codex is the implementation worker.
- Augment provides codebase context only.
- Memory0 provides approved memory context only.
- No assignment is allowed for blocked or unclear tasks.
