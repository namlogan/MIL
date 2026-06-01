# wm_pr_review_gate

Purpose: review PR evidence before merge decision.

Checks:
- One task, one branch, one PR, one handoff, one review.
- Acceptance criteria are satisfied.
- Diff is inside allowed scope.
- Required tests and gate artifacts are attached.
- Restricted areas are declared.
- Rollback note exists when runtime, deploy, database, or workflow behavior
  changes.

Output: approve, request changes, reject, or blocked-needs-human.
