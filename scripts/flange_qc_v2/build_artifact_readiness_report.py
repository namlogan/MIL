#!/usr/bin/env python3
"""Build a metadata-only Flange QC v2 artifact readiness report."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from apps.flange_qc_v2.artifact_intake import validate_artifact_intake
from apps.flange_qc_v2.artifact_readiness import build_artifact_readiness_report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--intake-dir",
        required=True,
        help="Artifact intake directory containing dataset/model/camera metadata manifests.",
    )
    parser.add_argument("--labeling-review-pack", help="Optional QC labeling review pack JSON path.")
    parser.add_argument("--repo-root", default=str(REPO_ROOT))
    parser.add_argument("--generated-at", help="Optional ISO timestamp for deterministic evidence output.")
    parser.add_argument("--source-ref", default="", help="Source issue, PR, or handoff reference.")
    parser.add_argument("--output", help="Output readiness report JSON path. Omit to write to stdout.")
    args = parser.parse_args(argv)

    try:
        labeling_pack = _read_optional_json(args.labeling_review_pack)
        intake_result = validate_artifact_intake(args.intake_dir, repo_root=args.repo_root)
        report = build_artifact_readiness_report(
            intake_result,
            labeling_review_pack=labeling_pack,
            generated_at=args.generated_at,
            source_ref=args.source_ref,
        )
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        _write_result({"ok": False, "errors": [str(exc)]}, args.output)
        return 1

    _write_result(report, args.output)
    return 0


def _read_optional_json(path: str | None) -> dict[str, Any] | None:
    if not path:
        return None
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("labeling review pack must be an object")
    return payload


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
