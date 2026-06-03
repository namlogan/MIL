#!/usr/bin/env python3
"""Validate a metadata-only Flange QC v2 shadow detector observation request."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from apps.flange_qc_v2.detector import validate_shadow_detector_observation_request


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, help="Path to shadow detector observation request JSON.")
    args = parser.parse_args(argv)

    input_path = Path(args.input)
    if not input_path.exists():
        result = {
            "ok": False,
            "observation_count": 0,
            "errors": [{"field": "input", "message": f"input file does not exist: {input_path}"}],
        }
        print(json.dumps(result, indent=2, sort_keys=True))
        return 1

    try:
        payload: Any = json.loads(input_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        result = {
            "ok": False,
            "observation_count": 0,
            "errors": [{"field": "input", "message": f"invalid JSON: {exc.msg}"}],
        }
        print(json.dumps(result, indent=2, sort_keys=True))
        return 1

    observations = payload.get("observations", []) if isinstance(payload, dict) else []
    observation_count = len(observations) if isinstance(observations, list) else 0
    errors = validate_shadow_detector_observation_request(payload)
    result = {
        "ok": not errors,
        "observation_count": observation_count,
        "errors": errors,
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
