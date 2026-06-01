#!/usr/bin/env python3
"""Check whether MIL memory is using local JSONL, Mem0 OSS, or Mem0 Platform."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Mapping


DEFAULT_LOCAL_STORE = ".ai-factory/memory/local_memory.jsonl"


def check_provider(env: Mapping[str, str] | None = None) -> dict[str, object]:
    values = dict(os.environ if env is None else env)
    base_url = values.get("MEM0_BASE_URL", "").strip()
    api_key = values.get("MEM0_API_KEY", "").strip()
    errors: list[str] = []
    warnings: list[str] = []

    if base_url:
        if not (base_url.startswith("http://") or base_url.startswith("https://")):
            errors.append("MEM0_BASE_URL must start with http:// or https://")
        return {
            "ok": not errors,
            "mode": "mem0_self_hosted",
            "base_url": base_url if not errors else "",
            "errors": errors,
            "warnings": warnings,
        }

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


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args(argv)

    if args.self_test:
        run_self_test()
        print("check_mem0_provider self-test passed")
        return 0

    result = check_provider()
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
