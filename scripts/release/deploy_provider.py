#!/usr/bin/env python3
"""Validate and describe the MIL release/deploy provider."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


DEFAULT_CONFIG = {
    "schema_version": 1,
    "enabled": False,
    "provider": "manual",
    "required_secret_names": [],
    "environments": {},
}
SUPPORTED_PROVIDERS = {"manual", "command", "vercel", "railway", "render", "fly"}
COMMAND_FIELDS = ("deploy", "smoke", "rollback")


def load_config(path: str | Path) -> dict[str, Any]:
    config_path = Path(path)
    if not config_path.exists():
        return dict(DEFAULT_CONFIG)
    data = json.loads(config_path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("deploy provider config must be a JSON object")
    return {**DEFAULT_CONFIG, **data}


def _is_command_array(value: Any) -> bool:
    return isinstance(value, list) and bool(value) and all(isinstance(item, str) for item in value)


def validate_config(config: dict[str, Any]) -> dict[str, Any]:
    errors: list[str] = []
    provider = str(config.get("provider", "")).strip()
    enabled = bool(config.get("enabled", False))
    required_secret_names = config.get("required_secret_names", [])
    environments = config.get("environments", {})

    if provider not in SUPPORTED_PROVIDERS:
        errors.append(f"provider must be one of {', '.join(sorted(SUPPORTED_PROVIDERS))}")
    if not isinstance(required_secret_names, list) or not all(
        isinstance(name, str) and name and "=" not in name for name in required_secret_names
    ):
        errors.append("required_secret_names must be a list of environment variable names, not values")
    if not isinstance(environments, dict):
        errors.append("environments must be an object")
        environments = {}
    if enabled and provider != "manual" and not environments:
        errors.append("enabled non-manual deploy provider requires at least one environment")

    for environment, environment_config in environments.items():
        if not isinstance(environment_config, dict):
            errors.append(f"environment {environment} must be an object")
            continue
        for field in COMMAND_FIELDS:
            if field not in environment_config:
                continue
            if not _is_command_array(environment_config[field]):
                errors.append(f"environment {environment} {field} must be a command array")
        if enabled and provider == "command" and not _is_command_array(environment_config.get("deploy")):
            errors.append(f"environment {environment} deploy command is required for command provider")

    return {
        "ok": not errors,
        "enabled": enabled,
        "provider": provider,
        "errors": errors,
    }


def build_deploy_plan(config: dict[str, Any], *, environment: str) -> dict[str, Any]:
    validation = validate_config(config)
    if not validation["ok"]:
        return {**validation, "environment": environment, "commands": {}}
    if not validation["enabled"]:
        return {
            "ok": True,
            "enabled": False,
            "provider": validation["provider"],
            "environment": environment,
            "status": "disabled",
            "required_secret_names": config.get("required_secret_names", []),
            "commands": {},
        }

    environments = config.get("environments", {})
    environment_config = environments.get(environment, {}) if isinstance(environments, dict) else {}
    if not isinstance(environment_config, dict) or not environment_config:
        return {
            "ok": False,
            "enabled": True,
            "provider": validation["provider"],
            "environment": environment,
            "status": "missing_environment",
            "required_secret_names": config.get("required_secret_names", []),
            "commands": {},
            "errors": [f"environment {environment} is not configured"],
        }

    commands = {
        field: environment_config[field]
        for field in COMMAND_FIELDS
        if _is_command_array(environment_config.get(field))
    }
    return {
        "ok": True,
        "enabled": True,
        "provider": validation["provider"],
        "environment": environment,
        "status": "ready",
        "required_secret_names": config.get("required_secret_names", []),
        "commands": commands,
    }


def run_self_test() -> None:
    assert validate_config(DEFAULT_CONFIG)["ok"] is True
    assert not validate_config(
        {
            "enabled": True,
            "provider": "command",
            "environments": {"staging": {"deploy": "pnpm deploy"}},
        }
    )["ok"]
    assert build_deploy_plan(DEFAULT_CONFIG, environment="staging")["ok"] is True


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default=".ai-factory/deploy-provider.json")
    parser.add_argument("--environment", default="staging")
    parser.add_argument("--plan", action="store_true", help="Print deploy plan for an environment.")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args(argv)

    if args.self_test:
        run_self_test()
        print("deploy_provider self-test passed")
        return 0

    config = load_config(args.config)
    result = build_deploy_plan(config, environment=args.environment) if args.plan else validate_config(config)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
