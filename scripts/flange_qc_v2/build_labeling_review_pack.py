#!/usr/bin/env python3
"""Build a sanitized Flange QC v2 MLOps labeling review pack."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from apps.flange_qc_v2.feedback import build_labeling_review_pack


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, help="Path to validated QC feedback export JSONL.")
    parser.add_argument("--output", help="Output labeling review pack JSON path. Omit to write to stdout.")
    args = parser.parse_args(argv)

    input_path = Path(args.input)
    if not input_path.exists():
        _write_result(
            {
                "ok": False,
                "errors": [{"message": f"input file does not exist: {input_path}"}],
            },
            args.output,
        )
        return 1

    try:
        records = _read_jsonl(input_path)
        pack = build_labeling_review_pack(records)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        _write_result({"ok": False, "errors": [{"message": str(exc)}]}, args.output)
        return 1

    _write_result(pack, args.output)
    return 0


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    records = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        record = json.loads(line)
        if not isinstance(record, dict):
            raise ValueError(f"line {line_number}: record must be an object")
        records.append(record)
    return records


def _write_result(payload: dict[str, Any], output: str | None) -> None:
    text = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    if output:
        output_path = Path(output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(text, encoding="utf-8")
        return
    sys.stdout.write(text)


if __name__ == "__main__":
    raise SystemExit(main())
