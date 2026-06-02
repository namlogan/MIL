from __future__ import annotations

import json
import os
from collections.abc import Awaitable, Callable
from pathlib import Path
from typing import Any

from apps.flange_qc_v2.artifact_intake import validate_artifact_intake
from apps.flange_qc_v2.audit import AuditStore
from apps.flange_qc_v2.detector import (
    build_shadow_detector_status_from_intake,
    build_shadow_detector_unconfigured_status,
)
from apps.flange_qc_v2.domain import ValidationError
from apps.flange_qc_v2.feedback import QcFeedback
from apps.flange_qc_v2.health import build_health_snapshot
from apps.flange_qc_v2.hmi_stream import build_replay_inspection_snapshot

Scope = dict[str, Any]
Receive = Callable[[], Awaitable[dict[str, Any]]]
Send = Callable[[dict[str, Any]], Awaitable[None]]
REPO_ROOT = Path(__file__).resolve().parents[2]
STATIC_DIR = Path(__file__).resolve().parent / "static"
HMI_SCREEN = STATIC_DIR / "hmi.html"
ARTIFACT_INTAKE_ENV = "FLANGE_QC_V2_ARTIFACT_INTAKE_DIR"


async def app(scope: Scope, receive: Receive, send: Send) -> None:
    scope_type = scope.get("type")
    if scope_type == "http":
        await _handle_http(scope, receive, send)
        return
    if scope_type == "websocket":
        await _handle_websocket(scope, receive, send)
        return
    raise RuntimeError("FLANGE QC V2 bootstrap app only supports HTTP and WebSocket ASGI scopes")


async def _handle_http(scope: Scope, receive: Receive, send: Send) -> None:
    path = scope.get("path", "")
    method = scope.get("method", "GET")
    if method == "GET" and path == "/health":
        await _send_json(send, 200, build_health_snapshot())
        return
    if method == "GET" and path == "/hmi":
        await _send_html(send, 200, HMI_SCREEN.read_text(encoding="utf-8"))
        return
    if method == "GET" and path == "/inspection/replay":
        snapshot = build_replay_inspection_snapshot()
        audit_store = _audit_store_from_env()
        if audit_store is not None:
            audit_store.initialize()
            audit_store.ensure_inspection(snapshot)
        await _send_json(send, 200, snapshot.to_payload())
        return
    if method == "GET" and path == "/artifact-intake/status":
        await _send_json(send, 200, _artifact_intake_status_from_env())
        return
    if method == "GET" and path == "/detector/shadow/status":
        await _send_json(send, 200, _shadow_detector_status_from_env())
        return
    if method == "POST" and path == "/feedback":
        try:
            payload = await _read_json_body(receive)
            feedback = QcFeedback.from_payload(payload)
            response_payload = feedback.to_payload()
            audit_store = _audit_store_from_env()
            if audit_store is not None:
                audit_store.initialize()
                snapshot = build_replay_inspection_snapshot()
                if feedback.inspection_id == snapshot.inspection_id:
                    audit_store.ensure_inspection(snapshot)
                audit_store.append_feedback(feedback)
                response_payload["audit"] = {
                    "persisted": True,
                    "feedback_count": len(audit_store.fetch_feedback(feedback.inspection_id)),
                }
        except (ValidationError, json.JSONDecodeError) as exc:
            await _send_json(send, 400, {"detail": str(exc)})
            return
        await _send_json(send, 200, response_payload)
        return

    await _send_json(send, 404, {"detail": "not found"})


async def _handle_websocket(scope: Scope, receive: Receive, send: Send) -> None:
    message = await receive()
    if message.get("type") != "websocket.connect":
        return
    if scope.get("path", "") != "/ws/inspection":
        await send({"type": "websocket.close", "code": 1008})
        return

    snapshot = build_replay_inspection_snapshot()
    await send({"type": "websocket.accept"})
    await send(
        {
            "type": "websocket.send",
            "text": json.dumps(snapshot.to_payload(), sort_keys=True),
        }
    )
    await send({"type": "websocket.close", "code": 1000})


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


async def _send_html(send: Send, status: int, html: str) -> None:
    body = html.encode("utf-8")
    await send(
        {
            "type": "http.response.start",
            "status": status,
            "headers": [
                (b"content-type", b"text/html; charset=utf-8"),
                (b"content-length", str(len(body)).encode("ascii")),
            ],
        }
    )
    await send({"type": "http.response.body", "body": body})


async def _read_json_body(receive: Receive) -> dict[str, Any]:
    chunks: list[bytes] = []
    while True:
        message = await receive()
        if message.get("type") == "http.disconnect":
            raise ValidationError("request disconnected")
        chunks.append(message.get("body", b""))
        if not message.get("more_body", False):
            break
    raw = b"".join(chunks)
    if not raw:
        return {}
    data = json.loads(raw.decode("utf-8"))
    if not isinstance(data, dict):
        raise ValidationError("feedback payload must be an object")
    return data


def _audit_store_from_env() -> AuditStore | None:
    raw_path = os.environ.get("FLANGE_QC_V2_AUDIT_DB_PATH", "").strip()
    if not raw_path:
        return None
    return AuditStore(raw_path)


def _artifact_intake_status_from_env() -> dict[str, Any]:
    intake_dir = os.environ.get(ARTIFACT_INTAKE_ENV, "").strip()
    if not intake_dir:
        return {
            "configured": False,
            "ok": False,
            "intake_dir": "",
            "repo_root": str(REPO_ROOT),
            "errors": [f"{ARTIFACT_INTAKE_ENV} is not configured"],
            "warnings": [],
            "artifacts": {},
            "ready": {
                "shadow_model_integration_issue": False,
                "live_camera_implementation_issue": False,
            },
            "next_issue": {
                "recommended_task": "configure_artifact_intake",
                "reason": "artifact intake directory env var is missing",
            },
            "production_authority": False,
            "authority_blockers": [
                "MODEL_APPROVAL_REQUIRED",
                "HARDWARE_APPROVAL_REQUIRED",
                "PRODUCTION_APPROVAL_REQUIRED",
            ],
        }

    result = validate_artifact_intake(intake_dir, repo_root=REPO_ROOT)
    result["configured"] = True
    result["production_authority"] = False
    result["authority_blockers"] = [
        "MODEL_APPROVAL_REQUIRED",
        "HARDWARE_APPROVAL_REQUIRED",
        "PRODUCTION_APPROVAL_REQUIRED",
    ]
    return result


def _shadow_detector_status_from_env() -> dict[str, Any]:
    intake_dir = os.environ.get(ARTIFACT_INTAKE_ENV, "").strip()
    if not intake_dir:
        return build_shadow_detector_unconfigured_status(f"{ARTIFACT_INTAKE_ENV} is not configured")
    return build_shadow_detector_status_from_intake(intake_dir, repo_root=REPO_ROOT)
