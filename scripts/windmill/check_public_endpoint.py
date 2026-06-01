#!/usr/bin/env python3
"""Check the public GitHub webhook endpoint exposed through the MIL relay."""

from __future__ import annotations

import argparse
import json
import os
import urllib.error
import urllib.request
from typing import Callable
from urllib.parse import urlparse, urlunparse


DEFAULT_PUBLIC_ROUTE = "/mil/github-webhook"
DEFAULT_HEALTH_ROUTE = "/healthz"
DEFAULT_RELAY_URL = "http://127.0.0.1:18090"
WINDMILL_PORTS = {8000, 8090}

HttpGet = Callable[[str, float], tuple[int, bytes]]


def _default_http_get(url: str, timeout: float) -> tuple[int, bytes]:
    request = urllib.request.Request(url, method="GET")
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return int(response.status), response.read(512)
    except urllib.error.HTTPError as exc:
        return int(exc.code), exc.read(512)


def _health_url(url: str) -> str:
    parsed = urlparse(url)
    return urlunparse((parsed.scheme, parsed.netloc, DEFAULT_HEALTH_ROUTE, "", "", ""))


def evaluate_endpoint_config(
    *,
    public_url: str,
    relay_url: str = DEFAULT_RELAY_URL,
) -> dict[str, object]:
    errors: list[str] = []
    public = urlparse(public_url.strip())
    relay = urlparse(relay_url.strip())

    if public.scheme != "https":
        errors.append("public URL must use https")
    if not public.netloc:
        errors.append("public URL must include a hostname")
    if public.path.rstrip("/") != DEFAULT_PUBLIC_ROUTE:
        errors.append("public URL path must be /mil/github-webhook")
    if "/api/r/" in public.path:
        errors.append("public URL must point to the signed relay route, not Windmill directly")

    if relay.scheme != "http" or relay.hostname != "127.0.0.1":
        errors.append("relay URL must be http://127.0.0.1:<port>")
    if relay.port in WINDMILL_PORTS:
        errors.append("relay URL must not point at the Windmill port")
    if "/api/r/" in relay.path:
        errors.append("relay URL must not point at Windmill routes")

    return {
        "ok": not errors,
        "public_url": public_url.strip(),
        "relay_url": relay_url.strip(),
        "health_url": _health_url(public_url.strip()) if public.netloc else "",
        "local_health_url": _health_url(relay_url.strip()) if relay.netloc else "",
        "errors": errors,
    }


def _probe(url: str, timeout: float, http_get: HttpGet) -> dict[str, object]:
    try:
        status_code, body = http_get(url, timeout)
    except OSError as exc:
        return {"ok": False, "url": url, "status_code": 0, "error": str(exc)}
    ok = 200 <= status_code < 400
    parsed = {}
    if body:
        try:
            parsed = json.loads(body.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            parsed = {}
    return {
        "ok": ok and (not parsed or bool(parsed.get("ok", True))),
        "url": url,
        "status_code": status_code,
        "service": parsed.get("service", "") if isinstance(parsed, dict) else "",
    }


def run_health_checks(
    *,
    public_url: str,
    relay_url: str = DEFAULT_RELAY_URL,
    timeout: float = 5.0,
    http_get: HttpGet = _default_http_get,
) -> dict[str, object]:
    config = evaluate_endpoint_config(public_url=public_url, relay_url=relay_url)
    if not config["ok"]:
        return {**config, "checks": []}
    checks = [
        _probe(str(config["local_health_url"]), timeout, http_get),
        _probe(str(config["health_url"]), timeout, http_get),
    ]
    return {
        **config,
        "ok": all(check["ok"] for check in checks),
        "checks": checks,
        "errors": [str(check.get("error")) for check in checks if not check["ok"] and check.get("error")],
    }


def run_self_test() -> None:
    result = evaluate_endpoint_config(
        public_url="https://sublease-malformed-tribune.ngrok-free.dev/mil/github-webhook",
        relay_url="http://127.0.0.1:18090",
    )
    assert result["ok"], result
    bad = evaluate_endpoint_config(
        public_url="https://sublease-malformed-tribune.ngrok-free.dev/api/r/admins/mil/github-webhook",
        relay_url="http://127.0.0.1:8090",
    )
    assert not bad["ok"], bad


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--public-url",
        default=os.environ.get("MIL_PUBLIC_WEBHOOK_URL", ""),
        help="Public webhook URL, for example https://...ngrok-free.dev/mil/github-webhook.",
    )
    parser.add_argument("--relay-url", default=os.environ.get("MIL_RELAY_URL", DEFAULT_RELAY_URL))
    parser.add_argument("--timeout", type=float, default=5.0)
    parser.add_argument("--skip-health", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args(argv)

    if args.self_test:
        run_self_test()
        print("check_public_endpoint self-test passed")
        return 0

    if not args.public_url:
        parser.error("--public-url or MIL_PUBLIC_WEBHOOK_URL is required")
    if args.skip_health:
        result = evaluate_endpoint_config(public_url=args.public_url, relay_url=args.relay_url)
    else:
        result = run_health_checks(
            public_url=args.public_url,
            relay_url=args.relay_url,
            timeout=args.timeout,
        )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
