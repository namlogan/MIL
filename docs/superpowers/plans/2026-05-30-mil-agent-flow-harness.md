# MIL Agent Flow Harness Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a local, tested harness that proves the MIL agent control-plane flows route work to the right agent roles and produce gate evidence before Windmill is installed.

**Architecture:** Add a small Python package under `scripts/agent-flow/` that loads JSON fixtures, validates task inputs, routes each flow stage to a dry-run agent adapter, and emits machine-readable artifacts. Keep Windmill as the future cockpit while using this harness as the local executable contract for flow behavior.

**Tech Stack:** Python standard library, `unittest`, GitHub Actions, existing `scripts/agent-gate/*` helpers.

---

### Task 1: Flow Harness Core

**Files:**
- Create: `scripts/agent-flow/mil_flow.py`
- Create: `tests/test_mil_flow.py`
- Create: `tests/fixtures/agent_task.json`
- Modify: `.github/workflows/ci.yml`

- [ ] **Step 1: Write failing tests for flow routing**

Create tests that load a fixture issue and assert:

- `issue_to_plan` calls `codex.plan` and `auggie.validate_plan`
- `plan_to_pr` calls `codex.implement`, `codex.test`, and `auggie.review`
- `pr_quality_gate` calls `codex.qa` and emits `APPROVE_MERGE` for non-restricted passing fixtures
- `fix_ci_or_review` calls `auggie.diagnose` before `codex.fix`

Run: `python3 -m unittest discover -s tests -v`
Expected: FAIL because `scripts/agent-flow/mil_flow.py` does not exist.

- [ ] **Step 2: Implement minimal flow harness**

Implement `AgentCall`, `FlowResult`, `DryRunAgentAdapter`, `load_task`, and `run_flow`.

- [ ] **Step 3: Run unit tests**

Run: `python3 -m unittest discover -s tests -v`
Expected: PASS.

- [ ] **Step 4: Add CI coverage**

Add flow harness self-test to `.github/workflows/ci.yml`.

### Task 2: CLI And Artifact Outputs

**Files:**
- Modify: `scripts/agent-flow/mil_flow.py`
- Create: `.ai-factory/gates/sample_issue_to_plan.json`
- Create: `.ai-factory/gates/sample_pr_quality_gate.json`
- Modify: `docs/windmill-setup.md`

- [ ] **Step 1: Write failing tests for CLI output**

Add tests asserting the CLI writes JSON artifacts with `flow`, `decision`, `agent_calls`, and `artifacts`.

- [ ] **Step 2: Implement CLI**

Add arguments: `--flow`, `--task`, `--out`, `--self-test`.

- [ ] **Step 3: Generate sample artifacts**

Run:

```bash
python3 scripts/agent-flow/mil_flow.py --flow issue_to_plan --task tests/fixtures/agent_task.json --out .ai-factory/gates/sample_issue_to_plan.json
python3 scripts/agent-flow/mil_flow.py --flow pr_quality_gate --task tests/fixtures/agent_task.json --out .ai-factory/gates/sample_pr_quality_gate.json
```

- [ ] **Step 4: Run verification**

Run all existing local verification commands.

### Task 3: Publish Updated PR Evidence

**Files:**
- Modify: PR #2
- Modify: issue #1 comment trail

- [ ] **Step 1: Commit changes**

Run:

```bash
git add .github .ai-factory docs scripts tests
git commit -m "Add local MIL agent flow harness"
```

- [ ] **Step 2: Push branch**

Run:

```bash
git push
```

- [ ] **Step 3: Watch PR checks**

Run:

```bash
gh pr checks 2 --watch
```

- [ ] **Step 4: Comment handoff**

Comment on issue #1 with the flow harness evidence and remaining external blocker: real Windmill workspace/tokens and GitHub branch protection availability.

