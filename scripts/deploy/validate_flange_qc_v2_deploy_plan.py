#!/usr/bin/env python3
"""Validate the Flange QC v2 deployment scaffold.

The checked-in plan is intentionally a disabled scaffold. This validator fails
closed if the plan starts to look like a real production deploy.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


REQUIRED_ENVIRONMENTS = {"local_replay", "jetson_shadow", "rtx_shadow"}
ALLOWED_COMMANDS = {"validate", "smoke"}
BLOCKED_COMMANDS = {"deploy", "release", "promote", "push", "apply", "migrate"}
SECRET_VALUE_PATTERNS = [
    re.compile(r"gh[pousr]_[A-Za-z0-9_]{20,}"),
    re.compile(r"(?i)bearer\s+[A-Za-z0-9._=-]{16,}"),
    re.compile(r"(?i)(api[_-]?key|token|secret|password)\s*[:=]\s*[^,\s]{8,}"),
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
]


def load_plan(path: str | Path) -> dict[str, Any]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("deploy plan must be a JSON object")
    return data


def _flag_enabled_false(plan: dict[str, Any], field: str, errors: list[str]) -> None:
    if plan.get(field) is not False:
        errors.append(f"{field} must remain false")


def _secret_value_locations(value: Any, path: str = "plan") -> list[str]:
    locations: list[str] = []
    if isinstance(value, dict):
        for key, item in value.items():
            child_path = key if path == "plan" else f"{path}.{key}"
            locations.extend(_secret_value_locations(item, child_path))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            locations.extend(_secret_value_locations(item, f"{path}[{index}]"))
    elif isinstance(value, str):
        for pattern in SECRET_VALUE_PATTERNS:
            if pattern.search(value):
                locations.append(path)
                break
    return locations


def _validate_environments(environments: Any, errors: list[str]) -> None:
    if not isinstance(environments, list) or not environments:
        errors.append("environments must be a non-empty list")
        return

    names: set[str] = set()
    for environment in environments:
        if not isinstance(environment, dict):
            errors.append("each environment must be an object")
            continue
        name = str(environment.get("name", "")).strip()
        if not name:
            errors.append("each environment requires a name")
            continue
        names.add(name)
        for field in ["deploy_enabled", "production_deploy_enabled", "live_camera_enabled", "raw_media_enabled"]:
            if environment.get(field) is not False:
                errors.append(f"environment {name} {field} must remain false")

        commands = environment.get("commands", {})
        if not isinstance(commands, dict):
            errors.append(f"environment {name} commands must be an object")
            continue
        for command_name, command in commands.items():
            if command_name in BLOCKED_COMMANDS:
                errors.append(f"environment {name} command {command_name} is not allowed in scaffold")
            if command_name not in ALLOWED_COMMANDS:
                continue
            if not isinstance(command, list) or not command or not all(isinstance(part, str) for part in command):
                errors.append(f"environment {name} command {command_name} must be a command array")

    missing = REQUIRED_ENVIRONMENTS - names
    extra = names - REQUIRED_ENVIRONMENTS
    if missing:
        errors.append(f"missing environments: {', '.join(sorted(missing))}")
    if extra:
        errors.append(f"unexpected environments: {', '.join(sorted(extra))}")


def validate_plan(plan: dict[str, Any]) -> dict[str, Any]:
    errors: list[str] = []
    if plan.get("schema_version") != 1:
        errors.append("schema_version must be 1")
    if plan.get("app_id") != "flange_qc_v2":
        errors.append("app_id must be flange_qc_v2")
    if plan.get("status") != "scaffold_only":
        errors.append("status must be scaffold_only")
    if plan.get("deployment_authority") != "none":
        errors.append("deployment_authority must be none")
    if plan.get("deploy_provider_enabled") is not False:
        errors.append("deploy_provider_enabled must remain false")
    if plan.get("required_secret_names") != []:
        errors.append("required_secret_names must remain empty until provider approval")
    for field in ["production_deploy_enabled", "live_camera_enabled", "raw_media_enabled"]:
        _flag_enabled_false(plan, field, errors)
    _validate_environments(plan.get("environments"), errors)

    for location in _secret_value_locations(plan):
        errors.append(f"secret-like value found at {location}")

    return {
        "ok": not errors,
        "status": str(plan.get("status", "")),
        "app_id": str(plan.get("app_id", "")),
        "deployment_authority": str(plan.get("deployment_authority", "")),
        "production_deploy_enabled": bool(plan.get("production_deploy_enabled", False)),
        "required_secret_names": plan.get("required_secret_names", []),
        "errors": errors,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", default="deploy/flange_qc_v2/deploy_plan.json")
    args = parser.parse_args(argv)

    result = validate_plan(load_plan(args.plan))
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
