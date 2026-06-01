# Windmill Flow Template

Baseline for a Windmill flow definition.

Include:
- Purpose and owner.
- Inputs and required secrets by reference.
- Side effects.
- Retry behavior.
- Output schema.
- Failure states.
- Evidence path.
- Human approval requirements.

Flows may orchestrate checks and comments. They must not bypass GitHub branch
protection or human approval gates.
