#!/usr/bin/env python3
"""Check whether MIL memory is using local JSONL, Mem0 OSS, or Mem0 Platform."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import urllib.error
import urllib.request
from typing import Callable, Mapping


DEFAULT_LOCAL_STORE = ".ai-factory/memory/local_memory.jsonl"
DEFAULT_TIMEOUT_SECONDS = 5.0

HttpGet = Callable[[str, dict[str, str], float], tuple[int, bytes]]


def _default_http_get(url: str, headers: dict[str, str], timeout: float) -> tuple[int, bytes]:
    request = urllib.request.Request(url, headers=headers, method="GET")
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return int(response.status), response.read(512)
    except urllib.error.HTTPError as exc:
        return int(exc.code), exc.read(512)


def _live_check(
    *,
    base_url: str,
    api_key: str,
    timeout_seconds: float,
    http_get: HttpGet,
) -> dict[str, object]:
    health_url = f"{base_url.rstrip('/')}/health"
    headers: dict[str, str] = {}
    if api_key:
        headers["X-API-Key"] = api_key
    try:
        status_code, _body = http_get(health_url, headers, timeout_seconds)
    except OSError as exc:
        return {
            "ok": False,
            "url": health_url,
            "status_code": 0,
            "error": str(exc),
        }
    return {
        "ok": 200 <= status_code < 400,
        "url": health_url,
        "status_code": status_code,
    }


def check_provider(
    env: Mapping[str, str] | None = None,
    *,
    live_check: bool = False,
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
    http_get: HttpGet = _default_http_get,
) -> dict[str, object]:
    values = dict(os.environ if env is None else env)
    base_url = values.get("MEM0_BASE_URL", "").strip()
    api_key = values.get("MEM0_API_KEY", "").strip()
    errors: list[str] = []
    warnings: list[str] = []

    if base_url:
        if not (base_url.startswith("http://") or base_url.startswith("https://")):
            errors.append("MEM0_BASE_URL must start with http:// or https://")
        result: dict[str, object] = {
            "ok": not errors,
            "mode": "mem0_self_hosted",
            "base_url": base_url.rstrip("/") if not errors else "",
            "errors": errors,
            "warnings": warnings,
        }
        if live_check and not errors:
            probe = _live_check(
                base_url=base_url,
                api_key=api_key,
                timeout_seconds=timeout_seconds,
                http_get=http_get,
            )
            result["live_check"] = probe
            if not probe["ok"]:
                errors.append(
                    f"Mem0 live health check failed for {probe['url']} "
                    f"(status {probe['status_code']})"
                )
                result["ok"] = False
        return result

    if api_key:
        return {
            "ok": True,
            "mode": "mem0_platform",
            "base_url": "https://api.mem0.ai",
            "errors": errors,
            "warnings": warnings,
        }

    warnings.append("Mem0 external provider is not configured; using local JSONL adapter.")
    return {
        "ok": True,
        "mode": "local_jsonl",
        "store": DEFAULT_LOCAL_STORE,
        "errors": errors,
        "warnings": warnings,
    }


def run_self_test() -> None:
    assert check_provider({})["mode"] == "local_jsonl"
    assert check_provider({"MEM0_BASE_URL": "http://localhost:8888"})["ok"] is True
    assert check_provider({"MEM0_BASE_URL": "localhost:8888"})["ok"] is False
    live = check_provider(
        {"MEM0_BASE_URL": "http://localhost:8888", "MEM0_API_KEY": "secret"},
        live_check=True,
        http_get=lambda url, headers, timeout: (200, b'{"ok":true}'),
    )
    assert live["ok"] is True
    assert "secret" not in json.dumps(live)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live-check", action="store_true", help="Probe MEM0_BASE_URL /health.")
    parser.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT_SECONDS)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args(argv)

    if args.self_test:
        run_self_test()
        print("check_mem0_provider self-test passed")
        return 0

    result = check_provider(live_check=args.live_check, timeout_seconds=args.timeout)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
