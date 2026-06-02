from __future__ import annotations

import json
from collections.abc import Awaitable, Callable
from pathlib import Path
from typing import Any

from apps.flange_qc_v2.health import build_health_snapshot
from apps.flange_qc_v2.hmi_stream import build_replay_inspection_snapshot

Scope = dict[str, Any]
Receive = Callable[[], Awaitable[dict[str, Any]]]
Send = Callable[[dict[str, Any]], Awaitable[None]]
STATIC_DIR = Path(__file__).resolve().parent / "static"
HMI_SCREEN = STATIC_DIR / "hmi.html"


async def app(scope: Scope, receive: Receive, send: Send) -> None:
    scope_type = scope.get("type")
    if scope_type == "http":
        await _handle_http(scope, send)
        return
    if scope_type == "websocket":
        await _handle_websocket(scope, receive, send)
        return
    raise RuntimeError("FLANGE QC V2 bootstrap app only supports HTTP and WebSocket ASGI scopes")


async def _handle_http(scope: Scope, send: Send) -> None:
    path = scope.get("path", "")
    method = scope.get("method", "GET")
    if method == "GET" and path == "/health":
        await _send_json(send, 200, build_health_snapshot())
        return
    if method == "GET" and path == "/hmi":
        await _send_html(send, 200, HMI_SCREEN.read_text(encoding="utf-8"))
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
