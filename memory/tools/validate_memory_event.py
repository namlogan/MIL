#!/usr/bin/env python3
"""Validate MIL memory event samples against the gateway contract."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from f.mil.memory_contract import ALLOWED_MEMORY_TYPES, validate_memory_event


def _load_schema(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("schema must be a JSON object")
    return data


def _iter_samples(path: Path) -> list[Path]:
    if path.is_file():
        return [path]
    return sorted(sample for sample in path.glob("*.json") if sample.is_file())


def validate_samples(schema_path: Path, samples_path: Path) -> list[str]:
    errors: list[str] = []
    schema = _load_schema(schema_path)
    schema_types = set(
        schema.get("properties", {})
        .get("memory_type", {})
        .get("enum", [])
    )
    if schema_types != ALLOWED_MEMORY_TYPES:
        errors.append("schema memory_type enum does not match gateway taxonomy")

    samples = _iter_samples(samples_path)
    if not samples:
        errors.append(f"no memory samples found under {samples_path}")
        return errors

    for sample in samples:
        try:
            data = json.loads(sample.read_text(encoding="utf-8"))
            validate_memory_event(data)
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            errors.append(f"{sample}: {exc}")
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--schema", required=True)
    parser.add_argument("--samples", required=True)
    args = parser.parse_args(argv)

    errors = validate_samples(Path(args.schema), Path(args.samples))
    if errors:
        print(json.dumps({"ok": False, "errors": errors}, indent=2), file=sys.stderr)
        return 1
    print("memory event validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
