# Auggie Supervised Lane Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a supervised Auggie lane that lets Codex operate Auggie through interactive TTY while Windmill queues and records the work.

**Architecture:** Windmill remains a queue and audit layer; it does not call `auggie --print` while account policy blocks non-interactive mode. Codex starts an interactive Auggie TTY with a repo wrapper, runs standardized `.augment/commands`, verifies the output, and posts evidence to GitHub.

**Tech Stack:** Bash wrappers, Auggie workspace commands, Markdown runbooks, Python unittest validation, GitHub Actions.

---

### Task 1: Add The Interactive Auggie Entrypoint

**Files:**
- Create: `scripts/agent-flow/auggie_interactive.sh`
- Modify: `.github/workflows/ci.yml`

- [ ] Create a Bash wrapper that sources `.env.local`, requires `AUGMENT_SESSION_AUTH`, and runs `auggie --workspace-root "$REPO_ROOT" --rules AGENTS.md --allow-indexing`.
- [ ] Allow additional user flags to pass through to Auggie.
- [ ] Add the wrapper to the CI shell syntax check.

### Task 2: Add The Auggie Command Pack

**Files:**
- Create: `.augment/commands/mil-morning-triage.md`
- Create: `.augment/commands/mil-plan-review.md`
- Create: `.augment/commands/mil-pr-review.md`
- Create: `.augment/commands/mil-ci-diagnose.md`
- Create: `.augment/commands/mil-handoff.md`

- [ ] Each command must declare Auggie as advisory, not final merge authority.
- [ ] Each command must require read-only behavior unless the issue explicitly routes implementation to Auggie.
- [ ] Each command must require one of `AUGMENT_REVIEW_PASS`, `AUGMENT_REVIEW_NOTES`, `AUGMENT_REVIEW_CHANGES_RECOMMENDED`, or `AUGMENT_REVIEW_BLOCKED`.

### Task 3: Document The Human-In-Loop Workflow

**Files:**
- Create: `docs/auggie-human-loop-runbook.md`
- Create: `.ai-factory/qa/auggie_advisory_template.md`
- Create: `.windmill/flows/auggie_supervised_advisory.md`
- Modify: `docs/augment-setup.md`
- Modify: `docs/agent-operating-model.md`
- Modify: `.windmill/README.md`
- Modify: `.windmill/worker-groups.md`
- Modify: `README.md`

- [ ] Explain why Windmill does not call Auggie unattended while `--print` is blocked.
- [ ] Define the Codex-operated Auggie loop.
- [ ] Provide morning triage commands and PR evidence template.
- [ ] Keep secret handling local-only and recommend Windmill encrypted secrets.

### Task 4: Add Regression Checks

**Files:**
- Create: `tests/test_auggie_supervised_lane.py`
- Modify: `.github/workflows/ci.yml`

- [ ] Validate that all command files exist.
- [ ] Validate that command files include allowed Auggie verdicts.
- [ ] Validate that command files and docs do not contain literal Augment token fields.
- [ ] Run `python3 -m unittest discover -s tests -v`.
