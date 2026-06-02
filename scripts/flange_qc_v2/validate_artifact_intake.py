#!/usr/bin/env python3
"""Validate a Flange QC v2 dataset/model/camera artifact intake directory."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from apps.flange_qc_v2.artifact_intake import validate_artifact_intake


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--intake-dir",
        required=True,
        help="Directory containing dataset_manifest.json, evaluation_report.json, model_artifact_manifest.json, and camera_boundary.json.",
    )
    parser.add_argument("--repo-root", default=str(REPO_ROOT))
    args = parser.parse_args(argv)

    result = validate_artifact_intake(args.intake_dir, repo_root=args.repo_root)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
