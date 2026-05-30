#!/usr/bin/env python3
"""Extract the final aif-gate-result JSON block from agent output."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


GATE_BLOCK_RE = re.compile(r"```aif-gate-result\s*([\s\S]*?)```", re.MULTILINE)


def extract_aif_gate_result(text: str) -> dict[str, Any] | None:
    matches = list(GATE_BLOCK_RE.finditer(text))
    if not matches:
        return None
    raw_json = matches[-1].group(1).strip()
    return json.loads(raw_json)


def read_input(path: str | None) -> str:
    if path:
        return Path(path).read_text(encoding="utf-8")
    return sys.stdin.read()


def run_self_test() -> None:
    sample = """
Earlier notes.

```aif-gate-result
{"decision": "REQUEST_CHANGES", "blocking": true, "reasons": ["old"]}
```

Final notes.

```aif-gate-result
{"decision": "APPROVE_MERGE", "blocking": false, "reasons": []}
```
"""
    result = extract_aif_gate_result(sample)
    assert result is not None
    assert result["decision"] == "APPROVE_MERGE"
    assert result["blocking"] is False


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", nargs="?", help="File to read. Defaults to stdin.")
    parser.add_argument("--self-test", action="store_true", help="Run built-in tests.")
    args = parser.parse_args()

    if args.self_test:
        run_self_test()
        print("extract_aif_gate_result self-test passed")
        return 0

    try:
        result = extract_aif_gate_result(read_input(args.path))
    except json.JSONDecodeError as exc:
        print(f"Malformed aif-gate-result JSON: {exc}", file=sys.stderr)
        return 3

    if result is None:
        print("No aif-gate-result block found", file=sys.stderr)
        return 2

    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

