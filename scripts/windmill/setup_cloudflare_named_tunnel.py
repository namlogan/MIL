#!/usr/bin/env python3
"""Create and validate the stable Cloudflare named tunnel for MIL webhooks."""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, NamedTuple


DEFAULT_TUNNEL_NAME = "mil-github-webhook"
DEFAULT_CONFIG_OUT = Path(".windmill/runtime/cloudflared/mil-github-webhook.yml")
DEFAULT_RELAY_URL = "http://127.0.0.1:18090"
DEFAULT_METRICS = "127.0.0.1:20241"
LOCAL_WINDMILL_PORTS = (":8090", ":8000")


class TunnelInfo(NamedTuple):
    tunnel_id: str
    name: str


def default_origin_cert() -> Path:
    return Path(os.environ.get("TUNNEL_ORIGIN_CERT", "~/.cloudflared/cert.pem")).expanduser()


def validate_hostname(hostname: str) -> list[str]:
    errors: list[str] = []
    if "://" in hostname or "/" in hostname:
        errors.append("hostname must not include scheme or path")
    if "." not in hostname:
        errors.append("hostname must be a DNS name controlled by Cloudflare")
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9.-]*[A-Za-z0-9]", hostname):
        errors.append("hostname contains invalid DNS characters")
    return errors


def validate_relay_url(relay_url: str) -> list[str]:
    errors: list[str] = []
    if relay_url.rstrip("/").endswith("/api/r/admins/mil/github-webhook"):
        errors.append("relay URL must point to the local signed relay, not Windmill directly")
    if any(port in relay_url for port in LOCAL_WINDMILL_PORTS):
        errors.append("relay URL must not expose the full local Windmill port")
    if not relay_url.startswith("http://127.0.0.1:"):
        errors.append("relay URL must bind to 127.0.0.1 for the local signed relay")
    return errors


def build_config(
    *,
    tunnel_id: str,
    credentials_file: Path,
    hostname: str,
    relay_url: str,
    metrics: str,
) -> str:
    return "\n".join(
        [
            f"tunnel: {tunnel_id}",
            f"credentials-file: {credentials_file.expanduser().resolve()}",
            f"metrics: {metrics}",
            "loglevel: info",
            "ingress:",
            f"  - hostname: {hostname}",
            f"    service: {relay_url}",
            "  - service: http_status:404",
            "",
        ]
    )


def write_config(path: Path, config: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(config, encoding="utf-8")


def resolve_credentials_file(requested: Path, tunnel_id: str) -> Path:
    if requested.exists():
        return requested
    default_cloudflared = Path(f"~/.cloudflared/{tunnel_id}.json").expanduser()
    if default_cloudflared.exists():
        return default_cloudflared
    return requested


def run_command(command: list[str], *, dry_run: bool = False) -> subprocess.CompletedProcess[str]:
    if dry_run:
        return subprocess.CompletedProcess(command, 0, stdout="", stderr="")
    return subprocess.run(command, check=True, text=True, capture_output=True)


def load_tunnels(cloudflared: str, tunnel_name: str, *, dry_run: bool = False) -> list[TunnelInfo]:
    if dry_run:
        return []

    result = run_command(
        [cloudflared, "tunnel", "list", "--output", "json", "--name", tunnel_name]
    )
    raw = result.stdout.strip()
    data = json.loads(raw or "[]")
    if not isinstance(data, list):
        raise ValueError("cloudflared tunnel list did not return a JSON list")

    tunnels: list[TunnelInfo] = []
    for item in data:
        if not isinstance(item, dict):
            continue
        name = str(item.get("name") or "")
        tunnel_id = str(item.get("id") or item.get("uuid") or "")
        if name == tunnel_name and tunnel_id:
            tunnels.append(TunnelInfo(tunnel_id=tunnel_id, name=name))
    return tunnels


def parse_created_tunnel(stdout: str, tunnel_name: str) -> TunnelInfo | None:
    raw = stdout.strip()
    if not raw:
        return None
    try:
        data: Any = json.loads(raw)
    except json.JSONDecodeError:
        match = re.search(r"Created tunnel .* with id ([0-9a-fA-F-]{36})", raw)
        if match:
            return TunnelInfo(tunnel_id=match.group(1), name=tunnel_name)
        return None

    if isinstance(data, dict):
        tunnel_id = str(data.get("id") or data.get("uuid") or "")
        name = str(data.get("name") or tunnel_name)
        if tunnel_id:
            return TunnelInfo(tunnel_id=tunnel_id, name=name)
    return None


def create_tunnel(
    cloudflared: str,
    tunnel_name: str,
    credentials_file: Path,
    *,
    dry_run: bool = False,
) -> TunnelInfo:
    credentials_file.parent.mkdir(parents=True, exist_ok=True)
    result = run_command(
        [
            cloudflared,
            "tunnel",
            "create",
            "--credentials-file",
            str(credentials_file),
            "--output",
            "json",
            tunnel_name,
        ],
        dry_run=dry_run,
    )
    if dry_run:
        return TunnelInfo(tunnel_id="00000000-0000-0000-0000-000000000000", name=tunnel_name)
    parsed = parse_created_tunnel(result.stdout, tunnel_name)
    if parsed is None:
        tunnels = load_tunnels(cloudflared, tunnel_name)
        if not tunnels:
            raise RuntimeError("could not determine created tunnel id")
        return tunnels[0]
    return parsed


def ensure_tunnel(
    cloudflared: str,
    tunnel_name: str,
    credentials_file: Path,
    *,
    create: bool,
    dry_run: bool,
) -> TunnelInfo:
    tunnels = load_tunnels(cloudflared, tunnel_name, dry_run=dry_run)
    if tunnels:
        return tunnels[0]
    if not create:
        raise RuntimeError(f"Cloudflare tunnel {tunnel_name!r} does not exist")
    return create_tunnel(cloudflared, tunnel_name, credentials_file, dry_run=dry_run)


def route_dns(
    cloudflared: str,
    tunnel: TunnelInfo,
    hostname: str,
    *,
    overwrite_dns: bool,
    dry_run: bool,
) -> None:
    command = [cloudflared, "tunnel", "route", "dns"]
    if overwrite_dns:
        command.append("--overwrite-dns")
    command.extend([tunnel.tunnel_id, hostname])
    run_command(command, dry_run=dry_run)


def setup(args: argparse.Namespace) -> dict[str, Any]:
    errors = validate_hostname(args.hostname) + validate_relay_url(args.relay_url)
    if errors:
        return {"ok": False, "errors": errors}

    credentials_file = Path(args.credentials_file).expanduser()

    if args.write_config_only:
        if not args.tunnel_id:
            return {"ok": False, "errors": ["--tunnel-id is required with --write-config-only"]}
        config = build_config(
            tunnel_id=args.tunnel_id,
            credentials_file=credentials_file,
            hostname=args.hostname,
            relay_url=args.relay_url,
            metrics=args.metrics,
        )
        write_config(Path(args.config_out), config)
        return {
            "ok": True,
            "mode": "write_config_only",
            "config": str(Path(args.config_out)),
            "hostname": args.hostname,
        }

    cloudflared = shutil.which("cloudflared")
    if cloudflared is None:
        return {"ok": False, "errors": ["cloudflared is not installed"]}

    origin_cert = default_origin_cert()
    if not origin_cert.exists() and not args.dry_run:
        return {
            "ok": False,
            "needs_human": True,
            "errors": [
                "Cloudflare origin cert is missing",
                "Run: cloudflared tunnel login",
                "Log in with a Cloudflare account that owns the target DNS zone",
            ],
            "origin_cert": str(origin_cert),
        }

    tunnel = ensure_tunnel(
        cloudflared,
        args.tunnel_name,
        credentials_file,
        create=not args.no_create,
        dry_run=args.dry_run,
    )
    credentials_file = resolve_credentials_file(credentials_file, tunnel.tunnel_id)
    if not args.dry_run and not credentials_file.exists():
        return {
            "ok": False,
            "errors": [
                f"Tunnel credentials file is missing for {tunnel.name}",
                f"Expected {credentials_file}",
                "Re-run with --credentials-file pointing to the local tunnel JSON credentials, or create a new tunnel from this machine.",
            ],
        }

    if not args.skip_route_dns:
        route_dns(
            cloudflared,
            tunnel,
            args.hostname,
            overwrite_dns=args.overwrite_dns,
            dry_run=args.dry_run,
        )

    config = build_config(
        tunnel_id=tunnel.tunnel_id,
        credentials_file=credentials_file,
        hostname=args.hostname,
        relay_url=args.relay_url,
        metrics=args.metrics,
    )
    if not args.dry_run:
        write_config(Path(args.config_out), config)

    return {
        "ok": True,
        "tunnel_name": tunnel.name,
        "tunnel_id": tunnel.tunnel_id,
        "hostname": args.hostname,
        "config": str(Path(args.config_out)),
        "webhook_url": f"https://{args.hostname}/mil/github-webhook",
        "run_command": f"cloudflared tunnel --config {args.config_out} run {tunnel.name}",
        "relay_command": "scripts/windmill/run_github_webhook_relay_from_windmill_secret.sh",
        "dry_run": args.dry_run,
        "config_written": not args.dry_run,
        "dns_routed": not args.skip_route_dns and not args.dry_run,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--hostname", required=True)
    parser.add_argument("--tunnel-name", default=DEFAULT_TUNNEL_NAME)
    parser.add_argument("--tunnel-id")
    parser.add_argument("--config-out", default=str(DEFAULT_CONFIG_OUT))
    parser.add_argument(
        "--credentials-file",
        default=".windmill/runtime/cloudflared/mil-github-webhook.json",
    )
    parser.add_argument("--relay-url", default=DEFAULT_RELAY_URL)
    parser.add_argument("--metrics", default=DEFAULT_METRICS)
    parser.add_argument("--write-config-only", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--no-create", action="store_true")
    parser.add_argument("--skip-route-dns", action="store_true")
    parser.add_argument("--overwrite-dns", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        result = setup(args)
    except subprocess.CalledProcessError as exc:
        result = {
            "ok": False,
            "errors": [
                "cloudflared command failed",
                " ".join(exc.cmd) if isinstance(exc.cmd, list) else str(exc.cmd),
            ],
            "stderr": (exc.stderr or "").strip(),
        }
    except (OSError, ValueError, RuntimeError) as exc:
        result = {"ok": False, "errors": [str(exc)]}
    output = json.dumps(result, indent=2, sort_keys=True)
    if result.get("ok"):
        print(output)
        return 0
    print(output, file=sys.stderr)
    return 2 if result.get("needs_human") else 1


if __name__ == "__main__":
    raise SystemExit(main())
