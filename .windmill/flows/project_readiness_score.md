# wm_project_readiness_score

Purpose: provide an operator-readable readiness score for a new project.

Signals:
- Intake completeness
- Contract skeleton presence
- Product CI profile state
- Release path state
- Public webhook state
- Memory gateway state
- Augment context provider state
- Branch protection state

Output:
- JSON report with `ready`, `attention`, or `blocked`.
- Human-readable next action for the operator dashboard.
