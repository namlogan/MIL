#!/usr/bin/env python3
"""Validate contract-first skeletons for the MIL delivery framework."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


REQUIRED_JSON_SCHEMAS = [
    "contracts/events/software_task_event.schema.json",
    "contracts/payloads/task_context_pack.schema.json",
    "contracts/memory/memory_event.schema.json",
    "contracts/jobs/gstack_job.schema.json",
]

REQUIRED_FILES = [
    "contracts/README.md",
    "contracts/api/openapi.yaml",
    "contracts/db/migration_contract.md",
    *REQUIRED_JSON_SCHEMAS,
]


def _load_json(path: Path, errors: list[str]) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        errors.append(f"invalid JSON schema {path}: {exc}")
        return {}
    if not isinstance(data, dict):
        errors.append(f"{path} must contain a JSON object")
        return {}
    return data


def _validate_json_schema(path: Path, errors: list[str]) -> None:
    data = _load_json(path, errors)
    if not data:
        return
    if data.get("type") != "object":
        errors.append(f"{path} must define type object")
    if not isinstance(data.get("properties"), dict):
        errors.append(f"{path} must define properties")
    if not isinstance(data.get("required", []), list):
        errors.append(f"{path} required must be a list")


def _validate_openapi(path: Path, errors: list[str]) -> None:
    text = path.read_text(encoding="utf-8")
    for marker in ["openapi:", "info:", "paths:", "/health:"]:
        if marker not in text:
            errors.append(f"contracts/api/openapi.yaml missing {marker}")


def validate_contracts(repo_root: str | Path) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    errors: list[str] = []

    for relative_path in REQUIRED_FILES:
        path = root / relative_path
        if not path.is_file():
            errors.append(f"missing contract file: {relative_path}")

    openapi = root / "contracts/api/openapi.yaml"
    if openapi.is_file():
        _validate_openapi(openapi, errors)

    for relative_path in REQUIRED_JSON_SCHEMAS:
        path = root / relative_path
        if path.is_file():
            _validate_json_schema(path, errors)

    canonical_memory = root / "memory/schemas/memory_event.schema.json"
    contract_memory = root / "contracts/memory/memory_event.schema.json"
    if canonical_memory.is_file() and contract_memory.is_file():
        canonical = json.loads(canonical_memory.read_text(encoding="utf-8"))
        contract = json.loads(contract_memory.read_text(encoding="utf-8"))
        if canonical != contract:
            errors.append(
                "contracts/memory/memory_event.schema.json must match "
                "memory/schemas/memory_event.schema.json"
            )

    migration = root / "contracts/db/migration_contract.md"
    if migration.is_file():
        migration_text = migration.read_text(encoding="utf-8")
        for marker in ["Rollback", "Data", "Human approval"]:
            if marker not in migration_text:
                errors.append(f"migration contract missing {marker}")

    return {
        "ok": not errors,
        "checked_files": REQUIRED_FILES,
        "errors": errors,
    }


def run_self_test() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    result = validate_contracts(repo_root)
    assert result["ok"], result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", default=str(Path(__file__).resolve().parents[2]))
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args(argv)

    if args.self_test:
        run_self_test()
        print("validate_contracts self-test passed")
        return 0

    result = validate_contracts(args.repo)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
