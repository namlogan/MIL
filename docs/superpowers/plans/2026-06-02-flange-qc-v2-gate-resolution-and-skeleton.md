# FLANGE QC V2 Gate Resolution And Skeleton Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Resolve the approved app-code blockers and implement the narrow FQV2-001 app skeleton with a health endpoint.

**Architecture:** Gate decisions remain in docs, ADRs, QA evidence, and a JSON task manifest. App runtime starts as a small Python package under `apps/flange_qc_v2/**`, with a dependency-free health core and ASGI health endpoint so the skeleton can boot before FastAPI, camera, GPU, model, product tolerance approval, audit DB, or factory data are available.

**Tech Stack:** Python stdlib `unittest`, `compileall`, JSON config, minimal ASGI callable. FastAPI remains the intended service framework for later tasks when dependency policy is approved.

---

### Task 1: Gate-Resolution Pack

**Files:**
- Create: `docs/adr/flange-qc-v2/ADR-0005-bootstrap-repo-app-root-and-branch-convention.md`
- Create: `docs/project/flange_qc_v2/APPROVAL_REQUEST_PRODUCT_SPECS.md`
- Create: `.ai-factory/gates/flange_qc_v2_fqv2_001_dor.json`
- Create: `.ai-factory/qa/flange_qc_v2_gate_resolution_2026-06-02.md`
- Modify: `docs/project/flange_qc_v2/PROJECT_IDENTITY.md`
- Modify: `docs/project/flange_qc_v2/OPEN_QUESTIONS.md`
- Modify: `docs/project/flange_qc_v2/BOOTSTRAP_READINESS.md`

- [ ] **Step 1: Update project identity**

Add the approved bootstrap values:

```markdown
| Repo ID | `MIL/flange-qc-v2-bootstrap` |
| Canonical app root | `apps/flange_qc_v2/**` |
| First implementation branch | `agent/fqv2-001-app-skeleton` |
```

- [ ] **Step 2: Resolve owner-approved bootstrap questions**

Mark `FQV2-Q-001`, `FQV2-Q-002`, `FQV2-Q-009`, `FQV2-Q-010`, and `FQV2-Q-011` as resolved by `docs/superpowers/specs/2026-06-02-flange-qc-v2-gate-resolution-design.md`. Leave QC/SOP approval questions open.

- [ ] **Step 3: Add ADR-0005**

Record that MVP-0 uses the MIL bootstrap repo, `apps/flange_qc_v2/**`, and MIL branch naming. State consequences: app skeleton may start, but product specs remain draft and production release is blocked.

- [ ] **Step 4: Add product-spec approval request**

Create a request artifact that asks QC/domain owner to approve or reject `configs/flange_qc_v2/product_specs.bootstrap.json`. Include required decision fields:

```markdown
- approver_name:
- approver_role:
- source_sop_revision:
- decision: pending
- decision_date:
- notes:
```

- [ ] **Step 5: Add FQV2-001 DoR manifest**

Create `.ai-factory/gates/flange_qc_v2_fqv2_001_dor.json` matching `contracts/flange_qc_v2/jobs/gstack_job.schema.json` with:

```json
{
  "task_id": "FQV2-001",
  "source_ref": "docs/superpowers/specs/2026-06-02-flange-qc-v2-gate-resolution-design.md",
  "owner_agent": "codex_developer",
  "qa_agent": "codex_qa",
  "preferred_lane": "codex",
  "branch": "agent/fqv2-001-app-skeleton",
  "allowed_paths": [
    "apps/flange_qc_v2/**",
    "tests/flange_qc_v2/**",
    ".ai-factory/product-ci.json",
    ".ai-factory/gates/flange_qc_v2_fqv2_001_dor.json",
    ".ai-factory/qa/flange_qc_v2_*",
    "docs/project/flange_qc_v2/**",
    "docs/adr/flange-qc-v2/ADR-0005-bootstrap-repo-app-root-and-branch-convention.md",
    "docs/superpowers/plans/2026-06-02-flange-qc-v2-gate-resolution-and-skeleton.md"
  ],
  "restricted_paths": [
    ".env",
    "machine_vision/**",
    "legacy runtime",
    "factory datasets",
    "model weights",
    "TensorRT engines",
    "production deploy",
    "secrets",
    "destructive migrations"
  ],
  "acceptance_criteria": [
    "App package imports without camera, GPU, model, factory data, or approved product specs.",
    "Health endpoint returns explicit subsystem states.",
    "Unknown production capabilities are reported as unavailable, not passing.",
    "No SOP PASS/NG production decision logic is implemented.",
    "Product CI is enabled with checks that pass in this repo."
  ],
  "test_commands": [
    "python3 -m unittest discover -s tests/flange_qc_v2 -v",
    "python3 -m compileall -q apps/flange_qc_v2 tests/flange_qc_v2",
    "python3 scripts/product-ci/run_product_checks.py",
    "python3 -m unittest discover -s tests -v"
  ],
  "handoff_required": true,
  "rollback_note": "Revert FQV2-001 branch changes to remove the app skeleton and restore disabled product CI."
}
```

- [ ] **Step 6: Add QA gate evidence**

Create `.ai-factory/qa/flange_qc_v2_gate_resolution_2026-06-02.md` with `aif-gate-result` status `pass` for app skeleton only and residual risk that QC approval is still pending.

- [ ] **Step 7: Validate gate docs**

Run:

```bash
jq empty .ai-factory/gates/flange_qc_v2_fqv2_001_dor.json
python3 scripts/project-intake/validate_project_intake.py
python3 scripts/delivery/validate_delivery_os.py --self-test
python3 scripts/contracts/validate_contracts.py --self-test
git diff --check
```

Expected: all commands exit `0`.

- [ ] **Step 8: Commit gate pack**

Run:

```bash
git add docs/superpowers/plans/2026-06-02-flange-qc-v2-gate-resolution-and-skeleton.md docs/adr/flange-qc-v2/ADR-0005-bootstrap-repo-app-root-and-branch-convention.md docs/project/flange_qc_v2/APPROVAL_REQUEST_PRODUCT_SPECS.md docs/project/flange_qc_v2/PROJECT_IDENTITY.md docs/project/flange_qc_v2/OPEN_QUESTIONS.md docs/project/flange_qc_v2/BOOTSTRAP_READINESS.md .ai-factory/gates/flange_qc_v2_fqv2_001_dor.json .ai-factory/qa/flange_qc_v2_gate_resolution_2026-06-02.md
git commit -m "docs: resolve flange app skeleton gate"
```

### Task 2: Health Core TDD

**Files:**
- Create: `tests/flange_qc_v2/test_health.py`
- Create: `apps/flange_qc_v2/__init__.py`
- Create: `apps/flange_qc_v2/health.py`

- [ ] **Step 1: Write failing health snapshot test**

Create `tests/flange_qc_v2/test_health.py`:

```python
import unittest

from apps.flange_qc_v2.health import build_health_snapshot


class HealthSnapshotTests(unittest.TestCase):
    def test_default_snapshot_reports_safe_bootstrap_states(self) -> None:
        snapshot = build_health_snapshot()

        self.assertEqual(snapshot["service"], "flange-qc-v2")
        self.assertEqual(snapshot["status"], "degraded")
        self.assertEqual(snapshot["mode"], "bootstrap")
        self.assertEqual(snapshot["version"], "0.1.0")
        self.assertEqual(snapshot["subsystems"]["camera"], "unavailable")
        self.assertEqual(snapshot["subsystems"]["gpu"], "unavailable")
        self.assertEqual(snapshot["subsystems"]["model"], "unavailable")
        self.assertEqual(snapshot["subsystems"]["product_specs"], "draft_requires_qc_owner_approval")
        self.assertEqual(snapshot["subsystems"]["sop_decision_engine"], "not_implemented")
        self.assertEqual(snapshot["decision_authority"], "none")
        self.assertIn("qc_product_spec_approval_missing", snapshot["blockers"])
```

- [ ] **Step 2: Verify test fails**

Run:

```bash
python3 -m unittest tests.flange_qc_v2.test_health -v
```

Expected: fail with `ModuleNotFoundError` for `apps.flange_qc_v2.health`.

- [ ] **Step 3: Implement minimal health core**

Create `apps/flange_qc_v2/__init__.py`:

```python
"""FLANGE QC V2 bootstrap application package."""

__all__ = ["__version__"]

__version__ = "0.1.0"
```

Create `apps/flange_qc_v2/health.py`:

```python
from __future__ import annotations

from copy import deepcopy
from typing import Any

from apps.flange_qc_v2 import __version__


_BOOTSTRAP_SUBSYSTEMS = {
    "camera": "unavailable",
    "gpu": "unavailable",
    "model": "unavailable",
    "product_specs": "draft_requires_qc_owner_approval",
    "sop_decision_engine": "not_implemented",
    "audit_db": "not_configured",
    "replay_source": "not_configured",
}


def build_health_snapshot() -> dict[str, Any]:
    return {
        "service": "flange-qc-v2",
        "version": __version__,
        "status": "degraded",
        "mode": "bootstrap",
        "decision_authority": "none",
        "subsystems": deepcopy(_BOOTSTRAP_SUBSYSTEMS),
        "blockers": [
            "qc_product_spec_approval_missing",
            "camera_hardware_validation_missing",
            "model_approval_missing",
            "audit_db_not_configured",
        ],
    }
```

- [ ] **Step 4: Verify test passes**

Run:

```bash
python3 -m unittest tests.flange_qc_v2.test_health -v
```

Expected: `OK`.

### Task 3: ASGI Health Endpoint TDD

**Files:**
- Modify: `tests/flange_qc_v2/test_health.py`
- Create: `apps/flange_qc_v2/asgi.py`

- [ ] **Step 1: Add failing ASGI health endpoint test**

Append to `tests/flange_qc_v2/test_health.py`:

```python
import asyncio
import json

from apps.flange_qc_v2.asgi import app


class AsgiHealthEndpointTests(unittest.TestCase):
    def test_health_endpoint_returns_json_snapshot(self) -> None:
        messages = []

        async def receive():
            return {"type": "http.request", "body": b"", "more_body": False}

        async def send(message):
            messages.append(message)

        scope = {"type": "http", "method": "GET", "path": "/health"}
        asyncio.run(app(scope, receive, send))

        start = messages[0]
        body = json.loads(messages[1]["body"].decode("utf-8"))
        headers = dict(start["headers"])

        self.assertEqual(start["status"], 200)
        self.assertEqual(headers[b"content-type"], b"application/json")
        self.assertEqual(body["service"], "flange-qc-v2")
        self.assertEqual(body["decision_authority"], "none")
```

- [ ] **Step 2: Verify ASGI test fails**

Run:

```bash
python3 -m unittest tests.flange_qc_v2.test_health -v
```

Expected: fail with `ModuleNotFoundError` for `apps.flange_qc_v2.asgi`.

- [ ] **Step 3: Implement minimal ASGI endpoint**

Create `apps/flange_qc_v2/asgi.py`:

```python
from __future__ import annotations

import json
from collections.abc import Awaitable, Callable
from typing import Any

from apps.flange_qc_v2.health import build_health_snapshot

Scope = dict[str, Any]
Receive = Callable[[], Awaitable[dict[str, Any]]]
Send = Callable[[dict[str, Any]], Awaitable[None]]


async def app(scope: Scope, receive: Receive, send: Send) -> None:
    if scope.get("type") != "http":
        raise RuntimeError("FLANGE QC V2 bootstrap app only supports HTTP ASGI scopes")

    path = scope.get("path", "")
    method = scope.get("method", "GET")
    if method == "GET" and path == "/health":
        await _send_json(send, 200, build_health_snapshot())
        return

    await _send_json(send, 404, {"detail": "not found"})


async def _send_json(send: Send, status: int, payload: dict[str, Any]) -> None:
    body = json.dumps(payload, sort_keys=True).encode("utf-8")
    await send(
        {
            "type": "http.response.start",
            "status": status,
            "headers": [
                (b"content-type", b"application/json"),
                (b"content-length", str(len(body)).encode("ascii")),
            ],
        }
    )
    await send({"type": "http.response.body", "body": body})
```

- [ ] **Step 4: Verify endpoint test passes**

Run:

```bash
python3 -m unittest tests.flange_qc_v2.test_health -v
```

Expected: `OK`.

### Task 4: CLI Smoke And Product CI

**Files:**
- Modify: `tests/flange_qc_v2/test_health.py`
- Create: `apps/flange_qc_v2/__main__.py`
- Modify: `.ai-factory/product-ci.json`

- [ ] **Step 1: Add failing CLI smoke test**

Append to `tests/flange_qc_v2/test_health.py`:

```python
import subprocess
import sys


class HealthCliTests(unittest.TestCase):
    def test_module_cli_prints_health_json(self) -> None:
        completed = subprocess.run(
            [sys.executable, "-m", "apps.flange_qc_v2"],
            check=True,
            text=True,
            capture_output=True,
        )

        body = json.loads(completed.stdout)
        self.assertEqual(body["service"], "flange-qc-v2")
        self.assertEqual(body["status"], "degraded")
```

- [ ] **Step 2: Verify CLI test fails**

Run:

```bash
python3 -m unittest tests.flange_qc_v2.test_health -v
```

Expected: fail because `apps.flange_qc_v2.__main__` is missing.

- [ ] **Step 3: Implement CLI**

Create `apps/flange_qc_v2/__main__.py`:

```python
from __future__ import annotations

import json

from apps.flange_qc_v2.health import build_health_snapshot


def main() -> int:
    print(json.dumps(build_health_snapshot(), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Verify CLI test passes**

Run:

```bash
python3 -m unittest tests.flange_qc_v2.test_health -v
```

Expected: `OK`.

- [ ] **Step 5: Enable product CI**

Update `.ai-factory/product-ci.json`:

```json
{
  "enabled": true,
  "checks": [
    {
      "name": "flange-qc-v2-compile",
      "command": ["python3", "-m", "compileall", "-q", "apps/flange_qc_v2", "tests/flange_qc_v2"],
      "required": true
    },
    {
      "name": "flange-qc-v2-unit",
      "command": ["python3", "-m", "unittest", "discover", "-s", "tests/flange_qc_v2", "-v"],
      "required": true
    },
    {
      "name": "flange-qc-v2-health-smoke",
      "command": ["python3", "-m", "apps.flange_qc_v2"],
      "required": true
    }
  ]
}
```

- [ ] **Step 6: Verify product CI**

Run:

```bash
python3 scripts/product-ci/run_product_checks.py
```

Expected: JSON result with `"ok": true`.

### Task 5: Final Verification And Commit

**Files:**
- All files changed in Tasks 1-4.

- [ ] **Step 1: Run full verification**

Run:

```bash
jq empty .ai-factory/product-ci.json .ai-factory/gates/flange_qc_v2_fqv2_001_dor.json configs/flange_qc_v2/product_specs.bootstrap.json
python3 -m unittest discover -s tests/flange_qc_v2 -v
python3 -m compileall -q apps/flange_qc_v2 tests/flange_qc_v2
python3 scripts/product-ci/run_product_checks.py
python3 scripts/project-intake/validate_project_intake.py
python3 scripts/delivery/validate_delivery_os.py --self-test
python3 scripts/contracts/validate_contracts.py --self-test
python3 -m unittest discover -s tests -v
python3 scripts/operator/daily_status.py
git diff --check
```

Expected: all commands exit `0`; `daily_status.py` may report workspace dirty before commit but all checks must be OK except cleanliness.

- [ ] **Step 2: Commit implementation**

Run:

```bash
git add apps/flange_qc_v2 tests/flange_qc_v2 .ai-factory/product-ci.json
git commit -m "feat: add flange qc v2 app skeleton"
```

- [ ] **Step 3: Confirm clean post-commit state**

Run:

```bash
git status --short --branch
python3 scripts/operator/daily_status.py
```

Expected: branch `agent/fqv2-001-app-skeleton`, clean workspace, daily status ready.

## Self-Review

- Spec coverage: covers repo_id, package root, branch convention, product-spec approval request, FQV2-001 DoR, app skeleton, health endpoint, product CI, and final verification.
- Placeholder scan: no unresolved placeholder or deferred implementation wording remains.
- Type consistency: health snapshot is a `dict[str, Any]`; ASGI app uses JSON bytes and stdlib tests; product CI commands match actual paths.
