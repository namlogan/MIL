# wm_task_generation

Purpose: split MVP scope into agent-runnable vertical slices.

Each generated task must include goal, business reason, source references,
allowed areas, restricted areas, acceptance criteria, expected tests, rollback
impact, dependencies, memory preflight, and handoff format.

Gate: block tasks that are too large, lack `source_ref`, or route multiple
agents into the same core file without a split plan.
