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
