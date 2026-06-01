# wm_test_gate

Purpose: verify required tests for a PR or release candidate.

Checks:
- Required unit, contract, integration, e2e, product CI, and smoke commands are
  selected by change type.
- Missing dependencies are reported as blockers, not silent passes.
- Test evidence is attached to PR or release evidence.

Gate: failed required tests block merge.
