# FLANGE QC V2 Bootstrap Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Promote FLANGE QC App V2 from intake brief to a MIL-compliant, gate-first product repo bootstrap.

**Architecture:** Keep MIL as the SDLC control plane while FLANGE QC V2 becomes the product app. The app runtime path is replay/camera input, vision preprocessing, geometry measurement and detector observations, SOP rule engine, inspection decision, audit DB, and HMI/WebSocket feedback. Windmill, AI Factory, and Memory0 stay outside the realtime PASS/NG path.

**Tech Stack:** FastAPI, WebSocket, SQLite, Python pytest, ruff, mypy, JSON Schema, replay/no-camera fixtures, Jetson/RTX deployment scaffold after release gates.

---

### Task 1: Resolve Project Identity

**Files:**
- Modify: `docs/project/flange_qc_v2/PROJECT_IDENTITY.md`
- Modify: `docs/project/flange_qc_v2/OPEN_QUESTIONS.md`

- [ ] **Step 1: Confirm target repo**

Record the target GitHub repository in `PROJECT_IDENTITY.md`:

```markdown
| Repo ID | `github:<owner>/<repo>` |
```

- [ ] **Step 2: Resolve active location**

Set the answer to whether FLANGE QC V2 lives in MIL, a new repo, or an existing FLANGE repo in `OPEN_QUESTIONS.md`.

- [ ] **Step 3: Run validation**

Run:

```bash
python3 scripts/project-intake/validate_project_intake.py
git diff --check
```

Expected: validators exit 0 for MIL framework docs; FLANGE package still requires target-repo promotion before coding dispatch.

### Task 2: Verify SOP Sources And Product Specs

**Files:**
- Modify: `docs/project/flange_qc_v2/SOP_RULE_REGISTRY.md`
- Modify: `configs/flange_qc_v2/product_specs.bootstrap.json`
- Modify: `docs/project/flange_qc_v2/OPEN_QUESTIONS.md`

- [ ] **Step 1: Attach SOP source references**

Add source references for measurement, diagonal, mark, seam, corner, and defect rules to `SOP_RULE_REGISTRY.md`.

- [ ] **Step 2: Fill product groups**

Replace the empty `product_groups` array in `configs/flange_qc_v2/product_specs.bootstrap.json` with QC-approved groups only.

- [ ] **Step 3: Record approval state**

Change `status` from `draft_requires_qc_owner_approval` only after the QC/domain owner approval source is recorded.

- [ ] **Step 4: Validate JSON**

Run:

```bash
jq empty configs/flange_qc_v2/product_specs.bootstrap.json
git diff --check
```

Expected: JSON parses and no whitespace errors exist.

### Task 3: Promote Bootstrap Into Target Repo

**Files:**
- Copy from: `docs/project/flange_qc_v2/**`
- Copy from: `docs/adr/flange-qc-v2/**`
- Copy from: `contracts/flange_qc_v2/**`
- Copy from: `configs/flange_qc_v2/**`

- [ ] **Step 1: Copy active project docs**

In the target repo, place core intake files under its active `docs/project/**` paths according to the MIL startup runbook.

- [ ] **Step 2: Copy ADRs**

Copy ADRs into the target repo's `docs/adr/**` and mark them for owner review.

- [ ] **Step 3: Copy contracts and config**

Copy FLANGE contracts and bootstrap config into target repo paths.

- [ ] **Step 4: Run startup validators**

Run in the target repo:

```bash
python3 scripts/project-intake/validate_project_intake.py
python3 scripts/delivery/validate_delivery_os.py --self-test
python3 scripts/contracts/validate_contracts.py --self-test
python3 scripts/operator/daily_status.py
```

Expected: intake and framework validators pass before any implementation issue is dispatched.

### Task 4: Create First Doc-Only Smoke Issue

**Files:**
- Create in target repo through a GitHub issue and Codex worker branch only.

- [ ] **Step 1: Create issue**

Create a GitHub issue with task ID, goal, acceptance criteria, allowed files, required checks, restricted-change check, rollback note, and memory preflight scope.

- [ ] **Step 2: Keep allowed files harmless**

Allowed file for the first smoke should be a single docs-only evidence file.

- [ ] **Step 3: Require checks**

Use:

```bash
git diff --check
```

- [ ] **Step 4: Dispatch only after Definition of Ready**

Use `agent:auto-build` only after the issue passes Definition of Ready.

### Task 5: Start App Skeleton After Smoke

**Files:**
- Create: `apps/flange_qc_v2/src/**`
- Create: `apps/flange_qc_v2/tests/**`
- Modify: `.ai-factory/product-ci.json`

- [ ] **Step 1: Enable product CI for selected stack**

Set product CI checks for Python/FastAPI only after the app skeleton exists.

- [ ] **Step 2: Create app skeleton issue**

Use work package `V2-001` with allowed paths, acceptance criteria, checks, and rollback note.

- [ ] **Step 3: Verify no hardware dependency**

App health must start without camera, GPU, model, or factory data.

- [ ] **Step 4: Run checks**

Run:

```bash
python -m pytest tests/unit -q
ruff check .
mypy apps/flange_qc_v2/src
git diff --check
```

Expected: all required checks for the issue pass or blockers are recorded as evidence.
