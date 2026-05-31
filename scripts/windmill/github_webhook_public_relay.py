#!/usr/bin/env python3
"""Expose only the signed MIL GitHub webhook route to local Windmill.

This relay is intended to sit behind a public tunnel such as a hosted reverse
proxy, a reserved ngrok domain, or a Cloudflare Tunnel. It deliberately exposes
one route and forwards only signed GitHub webhook requests to the local Windmill
HTTP trigger.
"""

from __future__ import annotations

import argparse
import hashlib
import hmac
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, NamedTuple


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_LISTEN_HOST = "127.0.0.1"
DEFAULT_LISTEN_PORT = 18090
DEFAULT_PUBLIC_ROUTE = "/mil/github-webhook"
DEFAULT_WINDMILL_URL = "http://localhost:8090/api/r/admins/mil/github-webhook"
DEFAULT_MAX_BODY_BYTES = 2 * 1024 * 1024
DEFAULT_TIMEOUT_SECONDS = 20
DEFAULT_AUTO_DISPATCH_QUEUE = ".ai-factory/queue/webhooks"

FORWARDED_HEADERS = (
    "Content-Type",
    "X-GitHub-Delivery",
    "X-GitHub-Event",
    "X-Hub-Signature-256",
    "X-GitHub-Hook-ID",
    "X-GitHub-Hook-Installation-Target-ID",
    "X-GitHub-Hook-Installation-Target-Type",
)


class RelayDecision(NamedTuple):
    forward: bool
    status_code: int
    message: str


def _normalize_headers(headers: dict[str, Any]) -> dict[str, str]:
    return {str(key).lower(): str(value) for key, value in headers.items()}


def verify_github_signature(headers: dict[str, Any], body: bytes, secret: str) -> bool:
    normalized = _normalize_headers(headers)
    observed = normalized.get("x-hub-signature-256", "")
    if not observed.startswith("sha256="):
        return False
    expected = hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(observed.removeprefix("sha256="), expected)


def evaluate_request(
    method: str,
    path: str,
    headers: dict[str, Any],
    body: bytes,
    secret: str,
    public_route: str = DEFAULT_PUBLIC_ROUTE,
    max_body_bytes: int = DEFAULT_MAX_BODY_BYTES,
) -> RelayDecision:
    if path != public_route:
        return RelayDecision(False, 404, "not found")
    if method.upper() != "POST":
        return RelayDecision(False, 405, "method not allowed")
    if len(body) > max_body_bytes:
        return RelayDecision(False, 413, "request body too large")
    if not secret:
        return RelayDecision(False, 500, "webhook secret is not configured")
    if not verify_github_signature(headers, body, secret):
        return RelayDecision(False, 401, "invalid GitHub webhook signature")
    return RelayDecision(True, 200, "signature verified")


def build_forward_headers(headers: dict[str, Any], body_length: int) -> dict[str, str]:
    normalized = _normalize_headers(headers)
    forwarded: dict[str, str] = {}
    for name in FORWARDED_HEADERS:
        value = normalized.get(name.lower())
        if value:
            forwarded[name] = value
    forwarded["Content-Length"] = str(body_length)
    return forwarded


def forward_to_windmill(
    body: bytes,
    headers: dict[str, Any],
    windmill_url: str,
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
) -> tuple[int, bytes]:
    request = urllib.request.Request(
        windmill_url,
        data=body,
        headers=build_forward_headers(headers, len(body)),
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
            return int(response.status), response.read()
    except urllib.error.HTTPError as exc:
        return int(exc.code), exc.read()


def _truthy(value: str | None) -> bool:
    return str(value or "").strip().lower() in {"1", "true", "yes", "on"}


def _safe_delivery_id(value: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9_.-]+", "-", value.strip())
    return cleaned[:120] or "delivery"


def build_auto_dispatch_request(headers: dict[str, Any], body: bytes) -> dict[str, Any]:
    normalized = _normalize_headers(headers)
    payload = json.loads(body.decode("utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("GitHub webhook payload must be a JSON object")
    return {
        "github_event": normalized.get("x-github-event", ""),
        "delivery": normalized.get("x-github-delivery", ""),
        "payload": payload,
    }


def _launch_background_command(
    *,
    command: list[str],
    cwd: str | Path,
    log_path: str | Path,
) -> dict[str, Any]:
    log_file_path = Path(log_path)
    log_file_path.parent.mkdir(parents=True, exist_ok=True)
    with log_file_path.open("ab") as log_file:
        process = subprocess.Popen(
            command,
            cwd=str(cwd),
            stdout=log_file,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )
    return {"pid": process.pid}


def maybe_launch_auto_dispatch(
    *,
    headers: dict[str, Any],
    body: bytes,
    enabled: bool,
    repo_root: str | Path,
    queue_root: str | Path,
    launcher: Any = _launch_background_command,
) -> dict[str, Any]:
    if not enabled:
        return {"launched": False, "reason": "auto dispatch disabled"}

    request = build_auto_dispatch_request(headers, body)
    if request["github_event"] not in {"issues", "issue_comment"}:
        return {"launched": False, "reason": f"unsupported auto dispatch event {request['github_event']}"}

    root = Path(repo_root).resolve()
    queue = Path(queue_root)
    if not queue.is_absolute():
        queue = root / queue
    queue.mkdir(parents=True, exist_ok=True)

    delivery = _safe_delivery_id(str(request.get("delivery") or "delivery"))
    request_path = queue / f"{delivery}.json"
    result_path = queue / f"{delivery}.result.json"
    log_path = queue / f"{delivery}.log"
    request_path.write_text(json.dumps(request, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    command = [
        sys.executable,
        str(root / "scripts" / "agent-flow" / "auto_dispatcher.py"),
        "--request",
        str(request_path),
        "--repo",
        str(root),
        "--execute-agent",
        "--push",
        "--open-pr",
        "--out",
        str(result_path),
    ]
    launch_result = launcher(command=command, cwd=root, log_path=str(log_path))
    return {
        "launched": True,
        "request_path": str(request_path),
        "result_path": str(result_path),
        "log_path": str(log_path),
        **(launch_result or {}),
    }


class RelayHandler(BaseHTTPRequestHandler):
    server: "RelayServer"

    def do_GET(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler API
        self._reject_without_body("GET")

    def do_PUT(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler API
        self._reject_without_body("PUT")

    def do_DELETE(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler API
        self._reject_without_body("DELETE")

    def do_POST(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler API
        try:
            body_length = int(self.headers.get("Content-Length") or 0)
        except ValueError:
            self._send_json(400, {"ok": False, "error": "invalid content length"})
            return
        if body_length > self.server.max_body_bytes:
            self._send_json(413, {"ok": False, "error": "request body too large"})
            return
        body = self.rfile.read(body_length)
        decision = evaluate_request(
            method="POST",
            path=self.path,
            headers=dict(self.headers),
            body=body,
            secret=self.server.webhook_secret,
            public_route=self.server.public_route,
            max_body_bytes=self.server.max_body_bytes,
        )
        if not decision.forward:
            self._send_json(decision.status_code, {"ok": False, "error": decision.message})
            return

        status, response_body = forward_to_windmill(
            body=body,
            headers=dict(self.headers),
            windmill_url=self.server.windmill_url,
            timeout_seconds=self.server.timeout_seconds,
        )
        if status < 400:
            try:
                maybe_launch_auto_dispatch(
                    headers=dict(self.headers),
                    body=body,
                    enabled=self.server.auto_dispatch_enabled,
                    repo_root=self.server.auto_dispatch_repo,
                    queue_root=self.server.auto_dispatch_queue,
                )
            except (OSError, ValueError, json.JSONDecodeError) as exc:
                sys.stderr.write(f"github-webhook-relay: auto dispatch skipped: {exc}\n")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(response_body or b'{"ok":true}')

    def _reject_without_body(self, method: str) -> None:
        decision = evaluate_request(
            method=method,
            path=self.path,
            headers=dict(self.headers),
            body=b"",
            secret=self.server.webhook_secret,
            public_route=self.server.public_route,
            max_body_bytes=self.server.max_body_bytes,
        )
        self._send_json(decision.status_code, {"ok": False, "error": decision.message})

    def _send_json(self, status_code: int, payload: dict[str, Any]) -> None:
        encoded = json.dumps(payload, sort_keys=True).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def log_message(self, format: str, *args: Any) -> None:  # noqa: A002 - stdlib API
        sys.stderr.write(f"github-webhook-relay: {format % args}\n")


class RelayServer(ThreadingHTTPServer):
    def __init__(
        self,
        server_address: tuple[str, int],
        handler_class: type[BaseHTTPRequestHandler],
        webhook_secret: str,
        windmill_url: str,
        public_route: str,
        max_body_bytes: int,
        timeout_seconds: int,
        auto_dispatch_enabled: bool,
        auto_dispatch_repo: str,
        auto_dispatch_queue: str,
    ) -> None:
        super().__init__(server_address, handler_class)
        self.webhook_secret = webhook_secret
        self.windmill_url = windmill_url
        self.public_route = public_route
        self.max_body_bytes = max_body_bytes
        self.timeout_seconds = timeout_seconds
        self.auto_dispatch_enabled = auto_dispatch_enabled
        self.auto_dispatch_repo = auto_dispatch_repo
        self.auto_dispatch_queue = auto_dispatch_queue


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default=os.environ.get("MIL_WEBHOOK_RELAY_HOST", DEFAULT_LISTEN_HOST))
    parser.add_argument(
        "--port",
        type=int,
        default=int(os.environ.get("MIL_WEBHOOK_RELAY_PORT", str(DEFAULT_LISTEN_PORT))),
    )
    parser.add_argument(
        "--public-route",
        default=os.environ.get("MIL_WEBHOOK_PUBLIC_ROUTE", DEFAULT_PUBLIC_ROUTE),
    )
    parser.add_argument(
        "--windmill-url",
        default=os.environ.get("MIL_WINDMILL_WEBHOOK_URL", DEFAULT_WINDMILL_URL),
    )
    parser.add_argument(
        "--secret-env",
        default=os.environ.get("MIL_WEBHOOK_SECRET_ENV", "MIL_GITHUB_WEBHOOK_SECRET"),
    )
    parser.add_argument(
        "--auto-dispatch",
        action="store_true",
        default=_truthy(os.environ.get("MIL_AUTO_DISPATCH_ENABLED")),
        help="Launch local Codex worker dispatcher for explicit auto-build webhook requests.",
    )
    parser.add_argument(
        "--auto-dispatch-repo",
        default=os.environ.get("MIL_AUTO_DISPATCH_REPO", str(REPO_ROOT)),
    )
    parser.add_argument(
        "--auto-dispatch-queue",
        default=os.environ.get("MIL_AUTO_DISPATCH_QUEUE", DEFAULT_AUTO_DISPATCH_QUEUE),
    )
    parser.add_argument("--describe", action="store_true", help="Print effective non-secret config.")
    args = parser.parse_args(argv)

    secret = os.environ.get(args.secret_env, "")
    if args.describe:
        print(
            json.dumps(
                {
                    "host": args.host,
                    "port": args.port,
                    "public_route": args.public_route,
                    "windmill_url": args.windmill_url,
                    "secret_env": args.secret_env,
                    "secret_present": bool(secret),
                    "auto_dispatch_enabled": bool(args.auto_dispatch),
                    "auto_dispatch_repo": args.auto_dispatch_repo,
                    "auto_dispatch_queue": args.auto_dispatch_queue,
                },
                indent=2,
                sort_keys=True,
            )
        )
        return 0 if secret else 1

    if not secret:
        print(f"{args.secret_env} must be configured", file=sys.stderr)
        return 2

    server = RelayServer(
        (args.host, args.port),
        RelayHandler,
        webhook_secret=secret,
        windmill_url=args.windmill_url,
        public_route=args.public_route,
        max_body_bytes=DEFAULT_MAX_BODY_BYTES,
        timeout_seconds=DEFAULT_TIMEOUT_SECONDS,
        auto_dispatch_enabled=bool(args.auto_dispatch),
        auto_dispatch_repo=args.auto_dispatch_repo,
        auto_dispatch_queue=args.auto_dispatch_queue,
    )
    print(
        f"Listening on http://{args.host}:{args.port}{args.public_route} "
        f"-> {args.windmill_url}; auto_dispatch={bool(args.auto_dispatch)}",
        file=sys.stderr,
    )
    server.serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
