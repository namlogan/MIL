#!/usr/bin/env python3
"""Validate sanitized Flange QC v2 QC feedback export JSONL."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from apps.flange_qc_v2.feedback import validate_feedback_export_record


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, help="Path to QC feedback export JSONL.")
    args = parser.parse_args(argv)

    input_path = Path(args.input)
    if not input_path.exists():
        result = {
            "ok": False,
            "record_count": 0,
            "errors": [{"message": f"input file does not exist: {input_path}"}],
        }
        print(json.dumps(result, indent=2, sort_keys=True))
        return 1

    records: list[Any] = []
    errors: list[dict[str, Any]] = []
    for line_number, line in enumerate(input_path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError as exc:
            errors.append(
                {
                    "line": line_number,
                    "field": "record",
                    "message": f"invalid JSON: {exc.msg}",
                }
            )
            continue
        records.append(record)
        errors.extend(validate_feedback_export_record(record, line=line_number))

    result = {
        "ok": not errors,
        "record_count": len(records),
        "errors": errors,
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
