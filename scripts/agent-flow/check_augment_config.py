#!/usr/bin/env python3
"""Validate local Augment credentials without printing secrets."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Mapping


REQUIRED_ENV = (
    "AUGMENT_MCP_TOKEN",
    "AUGMENT_API_TOKEN",
    "AUGMENT_API_URL",
    "AUGMENT_SESSION_AUTH",
)


def load_env_file(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.exists():
        return values

    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        values[key.strip()] = value.strip().strip("'\"")
    return values


def _present(env: Mapping[str, str], name: str) -> bool:
    return bool(env.get(name))


def _session_check(raw_session: str | None) -> dict[str, Any]:
    if not raw_session:
        return {
            "present": False,
            "valid_json": False,
            "tenant_url": "",
            "has_access_token": False,
            "scopes": [],
        }

    try:
        data = json.loads(raw_session)
    except json.JSONDecodeError:
        return {
            "present": True,
            "valid_json": False,
            "tenant_url": "",
            "has_access_token": False,
            "scopes": [],
        }

    scopes = data.get("scopes") if isinstance(data, dict) else []
    if not isinstance(scopes, list):
        scopes = []

    return {
        "present": True,
        "valid_json": isinstance(data, dict),
        "tenant_url": data.get("tenantURL", "") if isinstance(data, dict) else "",
        "has_access_token": bool(data.get("accessToken")) if isinstance(data, dict) else False,
        "scopes": [str(scope) for scope in scopes],
    }


def check_config(
    env: Mapping[str, str] | None = None,
    env_file: str | Path | None = ".env.local",
    require_read_only: bool = False,
) -> dict[str, Any]:
    merged: dict[str, str] = {}
    if env is None:
        merged.update(os.environ)
    else:
        merged.update(env)

    if env_file is not None:
        merged.update(load_env_file(Path(env_file)))

    session = _session_check(merged.get("AUGMENT_SESSION_AUTH"))
    api_url = merged.get("AUGMENT_API_URL", "")
    token_values = [
        merged.get("AUGMENT_MCP_TOKEN", ""),
        merged.get("AUGMENT_API_TOKEN", ""),
    ]
    session_token_available = bool(session["has_access_token"])

    checks: dict[str, Any] = {
        "augment_mcp_token": {"present": _present(merged, "AUGMENT_MCP_TOKEN")},
        "augment_api_token": {"present": _present(merged, "AUGMENT_API_TOKEN")},
        "augment_api_url": {
            "present": bool(api_url),
            "https": api_url.startswith("https://"),
            "value": api_url if api_url.startswith("https://") else "",
        },
        "augment_session_auth": session,
        "token_consistency": {
            "env_tokens_present": all(bool(value) for value in token_values),
            "session_token_present": session_token_available,
            "env_tokens_match": len(set(token_values)) == 1 if all(token_values) else False,
        },
    }

    warnings: list[str] = []
    errors: list[str] = []
    scopes = set(session.get("scopes") or [])
    if "write" in scopes:
        warnings.append(
            "Augment credential includes write scope; keep Auggie review workers read-only at the tool/flow layer."
        )
        if require_read_only:
            errors.append("Augment credential has write scope but read-only mode is required.")

    ok = (
        checks["augment_mcp_token"]["present"]
        and checks["augment_api_token"]["present"]
        and checks["augment_api_url"]["present"]
        and checks["augment_api_url"]["https"]
        and checks["augment_session_auth"]["present"]
        and checks["augment_session_auth"]["valid_json"]
        and checks["augment_session_auth"]["has_access_token"]
        and "read" in scopes
        and not errors
    )

    return {
        "ok": bool(ok),
        "checks": checks,
        "errors": errors,
        "warnings": warnings,
    }


def run_self_test() -> None:
    session = {
        "accessToken": "secret-token",
        "tenantURL": "https://e6.api.augmentcode.com/",
        "scopes": ["read"],
    }
    result = check_config(
        env={
            "AUGMENT_MCP_TOKEN": "secret-token",
            "AUGMENT_API_TOKEN": "secret-token",
            "AUGMENT_API_URL": "https://e6.api.augmentcode.com/",
            "AUGMENT_SESSION_AUTH": json.dumps(session),
        },
        env_file=None,
    )
    assert result["ok"] is True
    assert "secret-token" not in json.dumps(result)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--env-file", default=".env.local", help="Optional env file to load.")
    parser.add_argument(
        "--require-read-only",
        action="store_true",
        help="Fail when the Augment session includes write scope.",
    )
    parser.add_argument("--self-test", action="store_true", help="Run built-in tests.")
    args = parser.parse_args(argv)

    if args.self_test:
        run_self_test()
        print("check_augment_config self-test passed")
        return 0

    result = check_config(env_file=args.env_file, require_read_only=args.require_read_only)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
