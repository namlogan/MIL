#!/usr/bin/env python3
"""Run project-specific CI checks configured by the product repository."""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any


DEFAULT_CONFIG = {
    "enabled": False,
    "checks": [],
}
DEFAULT_PROFILES = {
    "profiles": {},
}


def load_config(path: str | Path) -> dict[str, Any]:
    config_path = Path(path)
    if not config_path.exists():
        return dict(DEFAULT_CONFIG)
    data = json.loads(config_path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("product CI config must be a JSON object")
    return data


def load_profiles(path: str | Path) -> dict[str, Any]:
    profiles_path = Path(path)
    if not profiles_path.exists():
        return dict(DEFAULT_PROFILES)
    data = json.loads(profiles_path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("product CI profiles config must be a JSON object")
    profiles = data.get("profiles", {})
    if not isinstance(profiles, dict):
        raise ValueError("product CI profiles must be an object")
    return data


def load_effective_config(path: str | Path, profiles_path: str | Path) -> dict[str, Any]:
    config = load_config(path)
    profile_name = str(config.get("profile", "")).strip()
    checks = config.get("checks", [])
    if profile_name and not checks:
        profiles = load_profiles(profiles_path).get("profiles", {})
        profile = profiles.get(profile_name, {}) if isinstance(profiles, dict) else {}
        if not isinstance(profile, dict):
            raise ValueError(f"product CI profile {profile_name} must be an object")
        config = {**config, "checks": profile.get("checks", [])}
    return config


def validate_config(config: dict[str, Any]) -> dict[str, Any]:
    errors: list[str] = []
    enabled = bool(config.get("enabled", False))
    profile = config.get("profile")
    checks = config.get("checks", [])
    if profile is not None and not isinstance(profile, str):
        errors.append("profile must be a string when present")
    if not isinstance(checks, list):
        errors.append("checks must be a list")
        checks = []
    if enabled and not checks:
        errors.append("enabled product CI requires at least one check")
    for check in checks:
        if not isinstance(check, dict):
            errors.append("each check must be an object")
            continue
        name = str(check.get("name", "")).strip()
        command = check.get("command")
        if not name:
            errors.append("each check requires a name")
        if not isinstance(command, list) or not command or not all(isinstance(item, str) for item in command):
            errors.append(f"check {name or '<unnamed>'} command must be a non-empty list")
    return {
        "ok": not errors,
        "enabled": enabled,
        "errors": errors,
    }


def run_checks(config: dict[str, Any], repo_root: str | Path) -> dict[str, Any]:
    validation = validate_config(config)
    if not validation["ok"]:
        return {"ok": False, "status": "invalid_config", "checks": [], "errors": validation["errors"]}
    if not validation["enabled"]:
        return {"ok": True, "status": "skipped", "checks": [], "errors": []}

    results: list[dict[str, Any]] = []
    for check in config["checks"]:
        completed = subprocess.run(
            check["command"],
            cwd=str(repo_root),
            text=True,
            capture_output=True,
            check=False,
        )
        results.append(
            {
                "name": check["name"],
                "command": check["command"],
                "returncode": completed.returncode,
                "ok": completed.returncode == 0,
                "summary": (completed.stdout or completed.stderr).strip().splitlines()[:3],
            }
        )
    return {
        "ok": all(result["ok"] for result in results),
        "status": "completed",
        "checks": results,
        "errors": [],
    }


def run_self_test() -> None:
    assert validate_config({"enabled": False, "checks": []})["ok"] is True
    assert validate_config({"enabled": True, "checks": []})["ok"] is False
    assert validate_config(
        {"enabled": True, "checks": [{"name": "unit", "command": ["python3", "--version"]}]}
    )["ok"] is True
    assert load_effective_config(
        Path(__file__).resolve().parents[2] / ".ai-factory/product-ci.json",
        Path(__file__).resolve().parents[2] / ".ai-factory/product-ci.profiles.json",
    )["enabled"] is False


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", default=str(Path(__file__).resolve().parents[2]))
    parser.add_argument("--config", default=".ai-factory/product-ci.json")
    parser.add_argument("--profiles-config", default=".ai-factory/product-ci.profiles.json")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args(argv)

    if args.self_test:
        run_self_test()
        print("run_product_checks self-test passed")
        return 0

    repo = Path(args.repo).resolve()
    config = load_effective_config(repo / args.config, repo / args.profiles_config)
    result = run_checks(config, repo)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
