# wm_ci_baseline_check

Purpose: prove the new repo skeleton can build and test before agent coding.

Baseline checks:
- Unit test skeleton.
- Contract validation.
- Config validation.
- Memory event validation and scrubber.
- Windmill job or flow validation.
- Secret and fake-token scan.

Gate: CI baseline must be green before `wm_agent_assignment` can dispatch work.
