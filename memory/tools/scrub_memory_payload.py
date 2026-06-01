#!/usr/bin/env python3
"""Check memory payloads for restricted data before they enter Memory0."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from f.mil.memory_contract import sanitize_value


RESTRICTED_MARKERS = (
    "ghp_",
    "gho_",
    "github_pat_",
    "sk-",
    "accessToken",
    "authtoken",
    "api_key",
    "password",
    "PRIVATE KEY",
    "chain-of-thought",
    "raw customer data",
    "database dump",
    "model weights",
)


def _payload_contains_marker(value: Any) -> bool:
    serialized = json.dumps(value, sort_keys=True)
    return any(marker in serialized for marker in RESTRICTED_MARKERS)


def check_payloads(paths: list[Path]) -> list[str]:
    errors: list[str] = []
    for path in paths:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            errors.append(f"{path}: {exc}")
            continue
        scrubbed = sanitize_value(data)
        if _payload_contains_marker(scrubbed):
            errors.append(f"{path}: restricted marker remains after scrub")
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("paths", nargs="+")
    args = parser.parse_args(argv)

    errors = check_payloads([Path(path) for path in args.paths])
    if errors:
        print(json.dumps({"ok": False, "errors": errors}, indent=2), file=sys.stderr)
        return 1
    print("memory payload scrub check passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
