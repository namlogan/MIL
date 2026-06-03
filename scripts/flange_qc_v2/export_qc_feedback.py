#!/usr/bin/env python3
"""Export sanitized Flange QC v2 QC feedback metadata as JSONL."""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from apps.flange_qc_v2.audit import AuditStore


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--audit-db", required=True, help="Path to the Flange QC v2 audit SQLite database.")
    parser.add_argument("--output", help="Output JSONL path. Omit to write to stdout.")
    args = parser.parse_args(argv)

    audit_path = Path(args.audit_db)
    if not audit_path.exists():
        print(f"audit DB does not exist: {audit_path}", file=sys.stderr)
        return 1

    try:
        records = AuditStore(audit_path).export_feedback_metadata_records()
    except (OSError, sqlite3.Error, json.JSONDecodeError) as exc:
        print(f"feedback export failed: {exc}", file=sys.stderr)
        return 1

    output = "".join(json.dumps(record, sort_keys=True) + "\n" for record in records)
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(output, encoding="utf-8")
    else:
        sys.stdout.write(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
