#!/usr/bin/env python3
"""Validate and print commands for a stable ngrok endpoint for MIL webhooks."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


DEFAULT_RELAY_PORT = 18090
DEFAULT_RELAY_URL = f"http://127.0.0.1:{DEFAULT_RELAY_PORT}"
LOCAL_WINDMILL_PORTS = (":8090", ":8000")


def normalize_domain(value: str) -> str:
    candidate = value.strip()
    if candidate.startswith("http://") or candidate.startswith("https://"):
        parsed = urlparse(candidate)
        candidate = parsed.netloc
    return candidate.rstrip("/")


def validate_domain(domain: str) -> list[str]:
    errors: list[str] = []
    if not domain:
        errors.append("ngrok domain is required")
        return errors
    if "/" in domain or "://" in domain:
        errors.append("ngrok domain must be a hostname, not a URL with scheme/path")
    if "." not in domain:
        errors.append("ngrok domain must be a DNS hostname")
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9.-]*[A-Za-z0-9]", domain):
        errors.append("ngrok domain contains invalid DNS characters")
    if not (
        domain.endswith(".ngrok-free.app")
        or domain.endswith(".ngrok.app")
        or domain.endswith(".ngrok.dev")
        or domain.endswith(".ngrok.io")
    ):
        errors.append(
            "expected an ngrok-managed static/dev domain such as <name>.ngrok-free.app"
        )
    return errors


def validate_relay_url(relay_url: str) -> list[str]:
    errors: list[str] = []
    if relay_url.rstrip("/").endswith("/api/r/admins/mil/github-webhook"):
        errors.append("relay URL must point to the signed local relay, not Windmill directly")
    if any(port in relay_url for port in LOCAL_WINDMILL_PORTS):
        errors.append("relay URL must not expose the full local Windmill port")
    if not relay_url.startswith("http://127.0.0.1:"):
        errors.append("relay URL must bind to 127.0.0.1 for the local signed relay")
    return errors


def ngrok_configured(ngrok: str) -> tuple[bool, str]:
    result = subprocess.run(
        [ngrok, "config", "check"],
        check=False,
        text=True,
        capture_output=True,
    )
    output = "\n".join(part for part in [result.stdout.strip(), result.stderr.strip()] if part)
    return result.returncode == 0, output


def setup(args: argparse.Namespace) -> dict[str, Any]:
    domain = normalize_domain(args.domain)
    errors = validate_domain(domain) + validate_relay_url(args.relay_url)
    if errors:
        return {"ok": False, "errors": errors}

    ngrok = shutil.which("ngrok")
    if ngrok is None:
        return {"ok": False, "errors": ["ngrok is not installed"]}

    configured, config_output = ngrok_configured(ngrok)
    if not configured and not args.skip_config_check:
        return {
            "ok": False,
            "needs_human": True,
            "errors": [
                "ngrok is installed but no valid local config/authtoken is present",
                "Run: ngrok config add-authtoken <NGROK_AUTHTOKEN>",
                "Reserve or copy your account dev/static domain from the ngrok dashboard",
            ],
            "ngrok_config_check": config_output,
        }

    relay_port = urlparse(args.relay_url).port or DEFAULT_RELAY_PORT
    ngrok_command = [
        "ngrok",
        "http",
        "--url",
        f"https://{domain}",
        str(relay_port),
    ]

    return {
        "ok": True,
        "domain": domain,
        "webhook_url": f"https://{domain}/mil/github-webhook",
        "relay_url": args.relay_url,
        "relay_command": "scripts/windmill/run_github_webhook_relay_from_windmill_secret.sh",
        "ngrok_command": " ".join(ngrok_command),
        "github_events": ["issues", "issue_comment", "pull_request", "workflow_run"],
        "config_checked": configured,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--domain", required=True)
    parser.add_argument("--relay-url", default=DEFAULT_RELAY_URL)
    parser.add_argument(
        "--skip-config-check",
        action="store_true",
        help="Only validate and print commands without requiring a local ngrok authtoken.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        result = setup(args)
    except OSError as exc:
        result = {"ok": False, "errors": [str(exc)]}

    output = json.dumps(result, indent=2, sort_keys=True)
    if result.get("ok"):
        print(output)
        return 0
    print(output, file=sys.stderr)
    return 2 if result.get("needs_human") else 1


if __name__ == "__main__":
    raise SystemExit(main())
