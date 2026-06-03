# QC Tablet Signal Viewport Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the FQV2-034 signal-first QC tablet viewport for `/hmi`, with measurement chips, green/red/amber operator states, image-panel suspect overlays, and correct/false-alarm feedback actions.

**Architecture:** Keep all behavior inside the existing static HMI surface. The new first viewport derives display state from existing `inspection.snapshot` payload fields and posts alarm feedback through the existing `/feedback` endpoint; detailed SOP, artifact, detector, and feedback panels remain below the first viewport. No backend authority, camera, model, or feedback contract change is introduced.

**Tech Stack:** HTML/CSS/vanilla JavaScript in `apps/flange_qc_v2/static/hmi.html`, Python stdlib `unittest` in `tests/flange_qc_v2/test_hmi_screen.py`, existing no-camera replay endpoints, existing Browser/Playwright evidence.

---

## File Structure

- Modify `tests/flange_qc_v2/test_hmi_screen.py`: add RED coverage for the tablet viewport, three-state mapping helpers, image overlay helpers, and alarm feedback bindings.
- Modify `apps/flange_qc_v2/static/hmi.html`: replace the current dense top QC-device phase section with a signal-first viewport, add CSS, add JS render/mapping/overlay/feedback helpers, and keep existing detail panels below.
- Modify `docs/project/flange_qc_v2/USER_FLOWS.md`: describe the new QC tablet first-viewport flow.
- Modify `docs/project/flange_qc_v2/DATA_MODEL.md`: document derived operator state, measurement chips, overlay source, and feedback evidence.
- Modify `docs/project/flange_qc_v2/TEST_STRATEGY.md`: add HMI tablet viewport and feedback/overlay browser evidence expectations.
- Add `.ai-factory/gates/flange_qc_v2_fqv2_034_dor.json`: DoR manifest for issue #125.
- Add `.ai-factory/qa/flange_qc_v2_fqv2_034_handoff_2026-06-03.md`: QA handoff with tests, browser evidence, risks, and rollback.
- Add `.ai-factory/qa/flange_qc_v2_fqv2_034_hmi_tablet.png`: tablet screenshot artifact.
- Add `.ai-factory/qa/flange_qc_v2_fqv2_034_hmi_snapshot.md`: concise browser snapshot artifact.

## Task 1: RED Test For Signal-First Tablet Viewport

**Files:**
- Modify: `tests/flange_qc_v2/test_hmi_screen.py`
- Do not modify production code in this task.

- [ ] **Step 1: Add failing viewport structure test**

Append this test method inside `HmiScreenTests`:

```python
    def test_hmi_html_renders_signal_first_qc_tablet_viewport(self) -> None:
        html = HMI_HTML.read_text(encoding="utf-8")

        self.assertIn('aria-label="QC tablet operating viewport"', html)
        self.assertIn('id="qc-tablet-viewport"', html)
        self.assertIn('id="measurement-strip"', html)
        self.assertIn('id="operator-state-banner"', html)
        self.assertIn('id="operator-state-label"', html)
        self.assertIn('id="operator-state-action"', html)
        self.assertIn('id="inspection-image-panel"', html)
        self.assertIn('id="suspect-overlay-layer"', html)
        self.assertIn('id="suspect-region-label"', html)
        self.assertIn('id="alarm-feedback-actions"', html)
        self.assertIn('id="alarm-correct"', html)
        self.assertIn('id="alarm-false"', html)
        self.assertIn("Alert correct", html)
        self.assertIn("False alarm", html)
        self.assertIn("Next product", html)
        self.assertIn("Details", html)
```

- [ ] **Step 2: Add failing behavior-hook test**

Append this test method inside `HmiScreenTests`:

```python
    def test_hmi_html_defines_qc_tablet_state_overlay_and_feedback_helpers(self) -> None:
        html = HMI_HTML.read_text(encoding="utf-8")

        self.assertIn("renderQcTabletViewport", html)
        self.assertIn("mapOperatorState", html)
        self.assertIn("renderMeasurementStrip", html)
        self.assertIn("renderInspectionImagePanel", html)
        self.assertIn("renderAlarmFeedbackActions", html)
        self.assertIn("submitAlarmFeedback", html)
        self.assertIn("applySuspectOverlay", html)
        self.assertIn("hasActionableObservation", html)
        self.assertIn("measurementChipState", html)
        self.assertIn('data-operator-state="pass"', html)
        self.assertIn('data-operator-state="check"', html)
        self.assertIn('data-operator-state="review"', html)
        self.assertIn("PASS", html)
        self.assertIn("CHECK", html)
        self.assertIn("REVIEW", html)
        self.assertIn("Continue", html)
        self.assertIn("Inspect suspected area", html)
        self.assertIn("Wait / review", html)
        self.assertIn("MARK_FALSE_POSITIVE", html)
        self.assertIn("CONFIRM_BLOCKED", html)
```

- [ ] **Step 3: Run RED test**

Run:

```bash
python3 -m unittest tests.flange_qc_v2.test_hmi_screen -v
```

Expected: fails because `qc-tablet-viewport`, `renderQcTabletViewport`, and related viewport helpers are not present yet.

- [ ] **Step 4: Commit RED test**

```bash
git add tests/flange_qc_v2/test_hmi_screen.py
git commit -m "test: add QC tablet viewport coverage"
```

## Task 2: Build The Tablet Viewport Markup And CSS

**Files:**
- Modify: `apps/flange_qc_v2/static/hmi.html`
- Test: `tests/flange_qc_v2/test_hmi_screen.py`

- [ ] **Step 1: Insert CSS variables and classes**

Inside the `<style>` block, add these classes near the existing QC-device CSS:

```css
      .qc-tablet-viewport {
        display: grid;
        grid-template-rows: auto auto minmax(240px, 1fr) auto;
        gap: 12px;
        min-height: min(720px, calc(100vh - 112px));
        border: 1px solid var(--line);
        border-radius: var(--radius);
        background: var(--surface);
        overflow: hidden;
      }

      .qc-tablet-viewport[data-operator-state="pass"] {
        border-color: #9bd8b9;
        background: #effaf4;
      }

      .qc-tablet-viewport[data-operator-state="check"] {
        border-color: #f4b3aa;
        background: #fff7f5;
      }

      .qc-tablet-viewport[data-operator-state="review"] {
        border-color: #f7c78b;
        background: #fff8ed;
      }

      .measurement-strip {
        display: grid;
        grid-template-columns: 1.1fr repeat(3, minmax(0, 0.8fr));
        gap: 1px;
        background: var(--line);
      }

      .measurement-chip {
        min-width: 0;
        padding: 12px 14px;
        background: #ffffff;
      }

      .measurement-chip span {
        display: block;
        color: var(--muted);
        font-size: 12px;
        font-weight: 800;
      }

      .measurement-chip strong {
        display: block;
        margin-top: 5px;
        font-size: clamp(20px, 3vw, 34px);
        line-height: 1;
        overflow-wrap: anywhere;
      }

      .measurement-chip[data-state="ok"] strong {
        color: var(--green);
      }

      .measurement-chip[data-state="check"] strong {
        color: var(--red);
      }

      .measurement-chip[data-state="review"] strong {
        color: var(--amber);
      }

      .operator-state-banner {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 16px;
        min-height: 112px;
        padding: 18px 22px;
        color: #ffffff;
        background: var(--amber);
      }

      .operator-state-banner[data-operator-state="pass"] {
        background: var(--green);
      }

      .operator-state-banner[data-operator-state="check"] {
        background: var(--red);
      }

      .operator-state-banner[data-operator-state="review"] {
        background: var(--amber);
      }

      .operator-state-banner strong {
        display: block;
        font-size: clamp(44px, 8vw, 88px);
        line-height: 0.95;
        letter-spacing: 0;
      }

      .operator-state-banner span {
        display: block;
        margin-top: 8px;
        font-size: clamp(16px, 2vw, 24px);
        font-weight: 850;
      }

      .operator-state-badge {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        min-width: 116px;
        min-height: 46px;
        border: 2px solid rgba(255, 255, 255, 0.82);
        border-radius: 999px;
        font-weight: 950;
      }

      .inspection-image-panel {
        position: relative;
        min-height: 260px;
        margin: 0 14px;
        border: 1px solid var(--line);
        border-radius: var(--radius);
        overflow: hidden;
        background:
          radial-gradient(circle at 38% 42%, rgba(255,255,255,0.55), rgba(255,255,255,0) 22%),
          linear-gradient(135deg, #dbe4ed 0 18%, #b6c4d2 18% 20%, #d8e1ea 20% 44%, #aab9c7 44% 46%, #e4eaf0 46% 100%);
      }

      .suspect-overlay-layer {
        position: absolute;
        inset: 0;
      }

      .suspect-overlay {
        position: absolute;
        border: 6px solid var(--red);
        border-radius: 999px;
        background: rgba(180, 35, 24, 0.12);
        box-shadow: 0 0 0 5px rgba(255,255,255,0.86);
      }

      .suspect-region-label {
        position: absolute;
        left: 14px;
        bottom: 14px;
        max-width: calc(100% - 28px);
        padding: 9px 11px;
        border-radius: 6px;
        background: rgba(17, 24, 39, 0.9);
        color: #ffffff;
        font-size: 13px;
        font-weight: 850;
        overflow-wrap: anywhere;
      }

      .alarm-feedback-actions {
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 10px;
        padding: 0 14px 14px;
      }

      .alarm-action {
        min-height: 54px;
        border: 1px solid var(--line);
        border-radius: 6px;
        background: #ffffff;
        color: var(--ink);
        font-weight: 900;
        cursor: pointer;
      }

      .alarm-action-primary {
        border-color: var(--ink);
        color: #ffffff;
        background: var(--ink);
      }
```

Also extend the existing mobile media query so `.measurement-strip` and `.alarm-feedback-actions` collapse cleanly:

```css
        .measurement-strip,
        .alarm-feedback-actions {
          grid-template-columns: 1fr;
        }
```

- [ ] **Step 2: Replace the current top dense sections**

Inside `<main>`, replace the current `status-strip` and `qc-device-layout` first-viewport area with this section. Keep `id="decision"`, `id="phase"`, `id="product"`, and `id="spec"` as hidden compatibility fields so existing tests and JS bindings remain stable.

```html
      <section id="qc-tablet-viewport" class="qc-tablet-viewport" data-operator-state="review" aria-label="QC tablet operating viewport">
        <div id="measurement-strip" class="measurement-strip">
          <div class="measurement-chip" data-chip="product" data-state="review">
            <span>Product</span>
            <strong id="product">611</strong>
          </div>
          <div class="measurement-chip" data-chip="length" data-state="review">
            <span>Length</span>
            <strong id="length-chip-status">REVIEW</strong>
          </div>
          <div class="measurement-chip" data-chip="width" data-state="review">
            <span>Width</span>
            <strong id="width-chip-status">REVIEW</strong>
          </div>
          <div class="measurement-chip" data-chip="diagonal-or-stitch" data-state="review">
            <span>Diagonal / Stitch</span>
            <strong id="diagonal-chip-status">REVIEW</strong>
          </div>
        </div>

        <div id="operator-state-banner" class="operator-state-banner" data-operator-state="review">
          <div>
            <strong id="operator-state-label">REVIEW</strong>
            <span id="operator-state-action">Wait / review</span>
          </div>
          <div id="operator-state-badge" class="operator-state-badge">AMBER</div>
        </div>

        <div id="inspection-image-panel" class="inspection-image-panel">
          <div id="suspect-overlay-layer" class="suspect-overlay-layer"></div>
          <div id="suspect-region-label" class="suspect-region-label">No approved live image; replay image well active</div>
        </div>

        <div id="alarm-feedback-actions" class="alarm-feedback-actions">
          <button id="alarm-correct" class="alarm-action alarm-action-primary" type="button">Alert correct</button>
          <button id="alarm-false" class="alarm-action" type="button">False alarm</button>
        </div>
      </section>

      <section class="status-strip" aria-label="Inspection status">
        <div class="metric">
          <h2>Decision</h2>
          <strong id="decision" class="decision-blocked">BLOCKED</strong>
        </div>
        <div class="metric">
          <h2>Phase</h2>
          <strong id="phase">PHASE_2</strong>
        </div>
        <div class="metric">
          <h2>Spec</h2>
          <strong id="spec">bootstrap_replay</strong>
        </div>
        <div class="metric">
          <h2>Detail</h2>
          <strong>Below</strong>
        </div>
      </section>
```

Remove the old `qc-device-layout` section from the first viewport. Leave later detail panels in place.

- [ ] **Step 3: Add new DOM field bindings**

In the `fields` object, add these entries and remove the old `phaseOneDevice*`, `phaseTwoDevice*`, and `phaseTwoStitch*` entries:

```javascript
        qcTabletViewport: document.getElementById("qc-tablet-viewport"),
        operatorStateBanner: document.getElementById("operator-state-banner"),
        operatorStateLabel: document.getElementById("operator-state-label"),
        operatorStateAction: document.getElementById("operator-state-action"),
        operatorStateBadge: document.getElementById("operator-state-badge"),
        lengthChipStatus: document.getElementById("length-chip-status"),
        widthChipStatus: document.getElementById("width-chip-status"),
        diagonalChipStatus: document.getElementById("diagonal-chip-status"),
        inspectionImagePanel: document.getElementById("inspection-image-panel"),
        suspectOverlayLayer: document.getElementById("suspect-overlay-layer"),
        suspectRegionLabel: document.getElementById("suspect-region-label"),
        alarmFeedbackActions: document.getElementById("alarm-feedback-actions"),
        alarmCorrect: document.getElementById("alarm-correct"),
        alarmFalse: document.getElementById("alarm-false"),
```

- [ ] **Step 4: Verify GREEN for structure**

Run:

```bash
python3 -m unittest tests.flange_qc_v2.test_hmi_screen -v
```

Expected: the structure test passes; helper test may still fail until Task 3.

- [ ] **Step 5: Commit markup and CSS**

```bash
git add apps/flange_qc_v2/static/hmi.html
git commit -m "feat: add QC tablet viewport shell"
```

## Task 3: Implement State Mapping, Measurement Chips, And Overlay Rendering

**Files:**
- Modify: `apps/flange_qc_v2/static/hmi.html`
- Test: `tests/flange_qc_v2/test_hmi_screen.py`

- [ ] **Step 1: Replace the old QC-device renderer call**

Inside `renderSnapshot(payload)`, replace:

```javascript
        renderQcDevicePhaseLayout(payload.phase_results);
```

with:

```javascript
        renderQcTabletViewport(payload);
```

- [ ] **Step 2: Add the tablet viewport render helpers**

Replace the old helper block from `function renderQcDevicePhaseLayout` through `function summarizeDevicePhase` with:

```javascript
      function renderQcTabletViewport(payload) {
        const operatorState = mapOperatorState(payload);
        fields.qcTabletViewport.dataset.operatorState = operatorState.state;
        fields.operatorStateBanner.dataset.operatorState = operatorState.state;
        fields.operatorStateLabel.textContent = operatorState.label;
        fields.operatorStateAction.textContent = operatorState.action;
        fields.operatorStateBadge.textContent = operatorState.badge;
        renderMeasurementStrip(payload, operatorState);
        renderInspectionImagePanel(payload, operatorState);
        renderAlarmFeedbackActions(operatorState);
      }

      function mapOperatorState(payload) {
        const observations = Array.isArray(payload.observations) ? payload.observations : [];
        const hasObservation = observations.some(hasActionableObservation);
        const phaseResults = Array.isArray(payload.phase_results) ? payload.phase_results : [];
        const hasNgPhase = phaseResults.some((phaseResult) => phaseResult && phaseResult.decision === "NG");
        if (payload.decision === "PASS" && !hasObservation && !hasNgPhase) {
          return {
            state: "pass",
            label: "PASS",
            action: "Continue",
            badge: "GREEN"
          };
        }
        if (payload.decision === "NG" || hasNgPhase || hasObservation) {
          return {
            state: "check",
            label: "CHECK",
            action: "Inspect suspected area",
            badge: "RED"
          };
        }
        return {
          state: "review",
          label: "REVIEW",
          action: "Wait / review",
          badge: "AMBER"
        };
      }

      function renderMeasurementStrip(payload, operatorState) {
        const phaseResults = Array.isArray(payload.phase_results) ? payload.phase_results : [];
        const phaseOne = findPhaseResult(phaseResults, "PHASE_1");
        const phaseTwo = findPhaseResult(phaseResults, "PHASE_2");
        setMeasurementChip("length", measurementChipState(phaseOne), measurementChipLabel(phaseOne));
        setMeasurementChip("width", measurementChipState(phaseOne), measurementChipLabel(phaseOne));
        setMeasurementChip(
          "diagonal-or-stitch",
          operatorState.state === "check" ? "check" : measurementChipState(phaseTwo),
          operatorState.state === "check" ? "CHECK" : measurementChipLabel(phaseTwo)
        );
      }

      function setMeasurementChip(chipName, state, label) {
        const chip = document.querySelector(`[data-chip="${chipName}"]`);
        if (!chip) {
          return;
        }
        chip.dataset.state = state;
        const value = chip.querySelector("strong");
        if (value) {
          value.textContent = label;
        }
      }

      function measurementChipState(phaseResult) {
        if (!phaseResult || phaseResult.decision === "BLOCKED" || phaseResult.decision === "ASSIST" || phaseResult.decision === "NOT_EVALUATED") {
          return "review";
        }
        if (phaseResult.decision === "NG") {
          return "check";
        }
        return "ok";
      }

      function measurementChipLabel(phaseResult) {
        if (!phaseResult) {
          return "REVIEW";
        }
        if (phaseResult.decision === "PASS") {
          return "OK";
        }
        if (phaseResult.decision === "NG") {
          return "CHECK";
        }
        return "REVIEW";
      }

      function renderInspectionImagePanel(payload, operatorState) {
        const observations = Array.isArray(payload.observations) ? payload.observations : [];
        const actionable = observations.find(hasActionableObservation) || null;
        fields.suspectOverlayLayer.innerHTML = "";
        if (actionable) {
          applySuspectOverlay(actionable);
          fields.suspectRegionLabel.textContent = `${actionable.label || "suspected defect"} / ${formatConfidence(actionable.confidence)}`;
          return;
        }
        if (operatorState.state === "pass") {
          fields.suspectRegionLabel.textContent = "All required measurements in tolerance";
          return;
        }
        if (operatorState.state === "check") {
          fields.suspectRegionLabel.textContent = "Measurement check required; QC self-measure";
          return;
        }
        fields.suspectRegionLabel.textContent = "Review setup, calibration, approval, or model evidence";
      }

      function hasActionableObservation(observation) {
        return Boolean(observation && Array.isArray(observation.bbox) && observation.bbox.length === 4);
      }

      function applySuspectOverlay(observation) {
        const [x, y, width, height] = observation.bbox.map(Number);
        if (![x, y, width, height].every(Number.isFinite)) {
          return;
        }
        const overlay = document.createElement("div");
        overlay.className = "suspect-overlay";
        overlay.style.left = `${Math.max(0, Math.min(1, x)) * 100}%`;
        overlay.style.top = `${Math.max(0, Math.min(1, y)) * 100}%`;
        overlay.style.width = `${Math.max(0.02, Math.min(1, width)) * 100}%`;
        overlay.style.height = `${Math.max(0.02, Math.min(1, height)) * 100}%`;
        fields.suspectOverlayLayer.appendChild(overlay);
      }

      function renderAlarmFeedbackActions(operatorState) {
        const isAlarm = operatorState.state === "check";
        fields.alarmCorrect.textContent = isAlarm ? "Alert correct" : "Next product";
        fields.alarmFalse.textContent = isAlarm ? "False alarm" : "Details";
        fields.alarmCorrect.dataset.feedbackType = isAlarm ? "CONFIRM_BLOCKED" : "";
        fields.alarmFalse.dataset.feedbackType = isAlarm ? "MARK_FALSE_POSITIVE" : "";
      }

      function findPhaseResult(results, phaseName) {
        return results.find((result) => result && result.phase === phaseName) || null;
      }
```

- [ ] **Step 3: Remove old helper names from production code**

Remove these old functions if they remain:

```javascript
renderQcDevicePhaseLayout
renderDevicePhase
renderPhaseTwoStitchZone
trafficStateForDecision
trafficLabelForDecision
summarizeDevicePhase
```

The existing `findPhaseResult` helper remains in the new block.

- [ ] **Step 4: Run HMI tests**

Run:

```bash
python3 -m unittest tests.flange_qc_v2.test_hmi_screen -v
```

Expected: all HMI screen tests pass.

- [ ] **Step 5: Commit renderer implementation**

```bash
git add apps/flange_qc_v2/static/hmi.html
git commit -m "feat: render QC tablet operator state"
```

## Task 4: Wire Alarm Feedback Buttons Through Existing Feedback Endpoint

**Files:**
- Modify: `apps/flange_qc_v2/static/hmi.html`
- Test: `tests/flange_qc_v2/test_hmi_screen.py`

- [ ] **Step 1: Add alarm button event listeners**

Near the existing `refreshReplay.addEventListener` and `feedbackForm.addEventListener` calls, add:

```javascript
      fields.alarmCorrect.addEventListener("click", () => submitAlarmFeedback("CONFIRM_BLOCKED"));
      fields.alarmFalse.addEventListener("click", () => submitAlarmFeedback("MARK_FALSE_POSITIVE"));
```

- [ ] **Step 2: Add `submitAlarmFeedback` helper**

Place this function immediately before the existing `submitFeedback()` function:

```javascript
      async function submitAlarmFeedback(feedbackType) {
        if (!currentSnapshot) {
          setFeedbackStatus("No inspection loaded", "error");
          return;
        }
        const isFalseAlarm = feedbackType === "MARK_FALSE_POSITIVE";
        const note = isFalseAlarm
          ? "QC tablet alarm feedback: false alarm."
          : "QC tablet alarm feedback: alert correct.";
        const reviewer = feedbackForm.querySelector('[name="reviewer_id"]');
        const feedbackTypeField = feedbackForm.querySelector('[name="feedback_type"]');
        const noteField = feedbackForm.querySelector('[name="note"]');
        if (reviewer && !String(reviewer.value || "").trim()) {
          reviewer.value = "qc-operator-1";
        }
        if (feedbackTypeField) {
          feedbackTypeField.value = feedbackType;
        }
        if (noteField) {
          noteField.value = note;
        }
        await submitFeedback();
      }
```

This keeps feedback inside the existing contract. `Alert correct` maps to `CONFIRM_BLOCKED` for the current implementation, and the QA handoff must record this limitation.

- [ ] **Step 3: Run HMI tests**

Run:

```bash
python3 -m unittest tests.flange_qc_v2.test_hmi_screen -v
```

Expected: all HMI screen tests pass.

- [ ] **Step 4: Commit feedback wiring**

```bash
git add apps/flange_qc_v2/static/hmi.html
git commit -m "feat: wire QC alarm feedback actions"
```

## Task 5: Documentation, DoR, And QA Evidence

**Files:**
- Modify: `docs/project/flange_qc_v2/USER_FLOWS.md`
- Modify: `docs/project/flange_qc_v2/DATA_MODEL.md`
- Modify: `docs/project/flange_qc_v2/TEST_STRATEGY.md`
- Add: `.ai-factory/gates/flange_qc_v2_fqv2_034_dor.json`
- Add: `.ai-factory/qa/flange_qc_v2_fqv2_034_handoff_2026-06-03.md`

- [ ] **Step 1: Update user flow docs**

In `docs/project/flange_qc_v2/USER_FLOWS.md`, update the No-Camera HMI Feedback Loop steps so step 3 reads:

```markdown
3. Operator first scans the QC tablet operating viewport. The viewport shows a
   top measurement strip, a large three-state signal, and a product image panel.
   Green `PASS` means continue, red `CHECK` means inspect the marked suspected
   region or self-measure, and amber `REVIEW` means setup/authority/model
   evidence still needs review.
4. If the app raises a red alarm, QC can submit `Alert correct` or `False alarm`
   feedback from the viewport. This feedback is model-training evidence only
   and does not approve production authority.
```

Renumber later steps.

- [ ] **Step 2: Update data model docs**

In `docs/project/flange_qc_v2/DATA_MODEL.md`, update the HMI screen section with:

```markdown
The first viewport is now a QC tablet operating surface. It derives an operator
state from the existing snapshot: green `PASS`, red `CHECK`, or amber `REVIEW`.
Measurement chips show product, length, width, and diagonal/stitch status in
minimal `OK`/`CHECK`/`REVIEW` labels. The image panel uses replay image-well
evidence in no-camera mode and can draw normalized detector `bbox` overlays when
review-only observations are present. Alarm feedback buttons post through the
existing `/feedback` endpoint as shadow evidence only.
```

- [ ] **Step 3: Update test strategy docs**

In `docs/project/flange_qc_v2/TEST_STRATEGY.md`, add:

```markdown
- HMI screen tests and browser evidence validate the signal-first QC tablet
  viewport, three-state green/red/amber operator mapping, measurement chips,
  suspect overlay rendering hooks, and alarm correctness feedback actions.
```

- [ ] **Step 4: Add DoR JSON**

Create `.ai-factory/gates/flange_qc_v2_fqv2_034_dor.json`:

```json
{
  "task_id": "FQV2-034",
  "github_issue": 125,
  "source_ref": "https://github.com/namlogan/MIL/issues/125",
  "owner_agent": "codex_developer",
  "qa_agent": "codex_qa",
  "preferred_lane": "codex",
  "branch": "agent/125-qc-tablet-viewport",
  "allowed_paths": [
    ".ai-factory/gates/flange_qc_v2_fqv2_034_dor.json",
    ".ai-factory/qa/flange_qc_v2_fqv2_034_handoff_2026-06-03.md",
    ".ai-factory/qa/flange_qc_v2_fqv2_034_hmi_tablet.png",
    ".ai-factory/qa/flange_qc_v2_fqv2_034_hmi_snapshot.md",
    "apps/flange_qc_v2/static/hmi.html",
    "tests/flange_qc_v2/test_hmi_screen.py",
    "docs/project/flange_qc_v2/USER_FLOWS.md",
    "docs/project/flange_qc_v2/DATA_MODEL.md",
    "docs/project/flange_qc_v2/TEST_STRATEGY.md",
    "docs/superpowers/specs/2026-06-03-qc-tablet-viewport-design.md",
    "docs/superpowers/plans/2026-06-03-qc-tablet-viewport.md"
  ],
  "restricted_summary": "No live camera, raw media/data, model runtime/training, production deploy/release, product spec approval, QC/SOP tolerance approval, model promotion, production PASS/NG authority, or production auto-reject change.",
  "acceptance_criteria": [
    "HMI first viewport is signal-first and tablet-oriented.",
    "Three-state green PASS, red CHECK, and amber REVIEW display is implemented.",
    "Top measurement chips show product and key measurement status.",
    "Image panel can render suspect overlays from normalized detector bbox observations.",
    "Alarm correct and false alarm actions submit existing shadow feedback evidence.",
    "Detailed panels remain available below the first viewport.",
    "Tests and browser/tablet evidence cover the new viewport."
  ],
  "test_commands": [
    "python3 -m unittest tests.flange_qc_v2.test_hmi_screen -v",
    "Browser/Playwright verification on http://127.0.0.1:8765/hmi at tablet landscape viewport",
    "python3 -m unittest discover -s tests/flange_qc_v2 -v",
    "python3 -m compileall -q apps/flange_qc_v2 tests/flange_qc_v2",
    "python3 scripts/product-ci/run_product_checks.py",
    "python3 -m unittest discover -s tests -v",
    "git diff --check",
    "python3 -m json.tool .ai-factory/gates/flange_qc_v2_fqv2_034_dor.json"
  ],
  "handoff_required": true,
  "browser_verification_required": true,
  "rollback_note": "Revert FQV2-034 to restore the previous HMI layout. Existing backend replay, decision engine, detector bridge, artifact intake, and feedback contracts remain valid."
}
```

- [ ] **Step 5: Add QA handoff skeleton**

Create `.ai-factory/qa/flange_qc_v2_fqv2_034_handoff_2026-06-03.md` with sections:

```markdown
# FQV2-034 QA Handoff: QC Tablet Signal Viewport

## Source

- GitHub issue: https://github.com/namlogan/MIL/issues/125
- Branch: `agent/125-qc-tablet-viewport`
- Task: FQV2-034

## Files Changed

- `apps/flange_qc_v2/static/hmi.html`
- `tests/flange_qc_v2/test_hmi_screen.py`
- `docs/project/flange_qc_v2/USER_FLOWS.md`
- `docs/project/flange_qc_v2/DATA_MODEL.md`
- `docs/project/flange_qc_v2/TEST_STRATEGY.md`
- `.ai-factory/gates/flange_qc_v2_fqv2_034_dor.json`
- `.ai-factory/qa/flange_qc_v2_fqv2_034_handoff_2026-06-03.md`
- `.ai-factory/qa/flange_qc_v2_fqv2_034_hmi_tablet.png`
- `.ai-factory/qa/flange_qc_v2_fqv2_034_hmi_snapshot.md`

## Rules Applied

- One task per branch.
- GitHub issue is the source of truth.
- TDD RED/GREEN used for HMI viewport coverage.
- HMI derives display state from existing replay/snapshot evidence only.
- Alarm feedback remains shadow-only evidence through `/feedback`.

## Tests Run

- RED: `python3 -m unittest tests.flange_qc_v2.test_hmi_screen -v` fails before implementation because the QC tablet viewport is missing.
- Final verification commands are recorded in this section after Task 6 runs them.

## Browser Evidence

- Tablet screenshot: `.ai-factory/qa/flange_qc_v2_fqv2_034_hmi_tablet.png`.
- Tablet snapshot: `.ai-factory/qa/flange_qc_v2_fqv2_034_hmi_snapshot.md`.

## Residual Risks

- No live camera image is approved; image panel uses replay image-well evidence.
- `Alert correct` maps to existing `CONFIRM_BLOCKED` feedback until a richer true-positive feedback type is approved.
- Product specs, QC/SOP tolerances, model promotion, live camera readiness, production PASS/NG authority, and release remain gated.

## Rollback

Revert FQV2-034 to restore the previous HMI layout. No migration, model, camera, dataset, or deploy rollback is required.
```

- [ ] **Step 6: Commit docs and gate skeleton**

```bash
git add docs/project/flange_qc_v2/USER_FLOWS.md docs/project/flange_qc_v2/DATA_MODEL.md docs/project/flange_qc_v2/TEST_STRATEGY.md .ai-factory/gates/flange_qc_v2_fqv2_034_dor.json .ai-factory/qa/flange_qc_v2_fqv2_034_handoff_2026-06-03.md
git commit -m "docs: add QC tablet viewport gate evidence"
```

## Task 6: Browser Verification, Final Checks, PR, And Merge Gate

**Files:**
- Add: `.ai-factory/qa/flange_qc_v2_fqv2_034_hmi_tablet.png`
- Add: `.ai-factory/qa/flange_qc_v2_fqv2_034_hmi_snapshot.md`
- Modify: `.ai-factory/qa/flange_qc_v2_fqv2_034_handoff_2026-06-03.md`

- [ ] **Step 1: Start a temporary local HMI server**

Run the existing no-camera temp-server pattern from previous HMI tasks with:

```bash
FLANGE_QC_V2_ARTIFACT_INTAKE_DIR=/Users/mac/Documents/MIL/templates/flange_qc_v2/artifact_intake python3 - <<'PY'
from __future__ import annotations
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

from apps.flange_qc_v2.asgi import HMI_SCREEN, _artifact_intake_status_from_env, _shadow_detector_status_from_env
from apps.flange_qc_v2.hmi_stream import build_replay_inspection_snapshot

class Handler(BaseHTTPRequestHandler):
    def _send(self, status: int, body: bytes, content_type: str) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        if path == "/hmi":
            self._send(200, HMI_SCREEN.read_bytes(), "text/html; charset=utf-8")
            return
        if path == "/inspection/replay":
            body = json.dumps(build_replay_inspection_snapshot().to_payload(), sort_keys=True).encode("utf-8")
            self._send(200, body, "application/json")
            return
        if path == "/artifact-intake/status":
            body = json.dumps(_artifact_intake_status_from_env(), sort_keys=True).encode("utf-8")
            self._send(200, body, "application/json")
            return
        if path == "/detector/shadow/status":
            body = json.dumps(_shadow_detector_status_from_env(), sort_keys=True).encode("utf-8")
            self._send(200, body, "application/json")
            return
        self._send(404, b'{"detail":"not found"}', "application/json")

    def log_message(self, format: str, *args) -> None:
        return

server = ThreadingHTTPServer(("127.0.0.1", 8765), Handler)
print("serving http://127.0.0.1:8765/hmi", flush=True)
server.serve_forever()
PY
```

- [ ] **Step 2: Capture tablet browser evidence**

Use Browser/Playwright:

```text
resize viewport to 1024x768
navigate to http://127.0.0.1:8765/hmi
capture viewport screenshot as fqv2-034-hmi-tablet.png
capture accessibility snapshot as fqv2-034-hmi-snapshot-raw.md
```

Move screenshot to:

```bash
mv fqv2-034-hmi-tablet.png .ai-factory/qa/flange_qc_v2_fqv2_034_hmi_tablet.png
```

Create concise `.ai-factory/qa/flange_qc_v2_fqv2_034_hmi_snapshot.md` with:

```markdown
# FQV2-034 HMI Tablet Browser Snapshot

Local target:

```text
http://127.0.0.1:8765/hmi
```

Verified viewport:

```json
{
  "viewport": "1024x768",
  "operatorViewport": "QC tablet operating viewport",
  "operatorState": "CHECK when review-only detector observations are present, otherwise REVIEW for current blocked replay evidence",
  "measurementStrip": ["Product", "Length", "Width", "Diagonal / Stitch"],
  "imagePanel": "rendered",
  "alarmActions": ["Alert correct", "False alarm"],
  "detailsBelow": ["Inspection status", "SOP phase results", "Artifact intake readiness", "Detector shadow status"]
}
```

Residual note:

The temporary HTTP server does not implement WebSocket upgrade, so one
`/ws/inspection` console error is expected. The real ASGI WebSocket remains
covered by `tests.flange_qc_v2.test_hmi_stream`.
```

- [ ] **Step 3: Run final verification**

Run:

```bash
python3 -m json.tool .ai-factory/gates/flange_qc_v2_fqv2_034_dor.json >/dev/null
python3 -m unittest tests.flange_qc_v2.test_hmi_screen -v
python3 -m unittest discover -s tests/flange_qc_v2 -v
python3 -m compileall -q apps/flange_qc_v2 tests/flange_qc_v2
python3 scripts/product-ci/run_product_checks.py
python3 -m unittest discover -s tests -v
git diff --check
```

Expected: all commands pass. Record exact counts in the handoff.

- [ ] **Step 4: Update QA handoff and commit browser evidence**

```bash
git add .ai-factory/qa/flange_qc_v2_fqv2_034_handoff_2026-06-03.md .ai-factory/qa/flange_qc_v2_fqv2_034_hmi_tablet.png .ai-factory/qa/flange_qc_v2_fqv2_034_hmi_snapshot.md
git commit -m "docs: record QC tablet viewport QA evidence"
```

- [ ] **Step 5: Push and open PR**

```bash
git push -u origin agent/125-qc-tablet-viewport
gh pr create --base main --head agent/125-qc-tablet-viewport --title "FQV2-034: Signal-first QC tablet viewport" --label "agent:auto-build" --label "automerge:candidate" --body-file /tmp/fqv2-034-pr-body.md
```

PR body must include issue #125, tests run, restricted change check, residual risks, rollback, and `Closes #125`.

- [ ] **Step 6: Run merge controller and post-merge checks**

```bash
PR_NUMBER="$(gh pr view --json number -q .number)"
python3 scripts/github/merge_controller.py --pr "$PR_NUMBER" --policy-only
gh pr checks "$PR_NUMBER" --watch --interval 10
git checkout main
git pull --ff-only
gh workflow run ci --ref main
python3 scripts/operator/daily_status.py
```

Expected: PR checks pass, auto-merge completes or is ready under merge-controller policy, main CI passes, daily status is ready, and issue #125 is closed.

## Self-Review

- Spec coverage: Tasks cover state model, measurement strip, signal banner, image/overlay panel, alarm feedback, docs/evidence, browser/tablet verification, restricted boundaries, and merge flow.
- Placeholder scan: The implementation steps contain concrete selectors, function names, command lines, expected outcomes, and file paths. The handoff skeleton has fill points that are intentionally completed after final verification in Task 6.
- Type consistency: Function names and DOM ids are consistent across tests, markup, and render helpers: `renderQcTabletViewport`, `mapOperatorState`, `renderMeasurementStrip`, `renderInspectionImagePanel`, `renderAlarmFeedbackActions`, `submitAlarmFeedback`, `applySuspectOverlay`, and `measurementChipState`.
