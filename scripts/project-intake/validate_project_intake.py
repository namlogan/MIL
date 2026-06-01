#!/usr/bin/env python3
"""Validate the project intake package required before agent work starts."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


REQUIRED_TEMPLATE_PATHS = [
    "docs/templates/project/PRD.md",
    "docs/templates/project/MVP_SCOPE.md",
    "docs/templates/project/USER_FLOWS.md",
    "docs/templates/project/DATA_MODEL.md",
    "docs/templates/project/TEST_STRATEGY.md",
    "docs/templates/project/DEPLOYMENT.md",
    "docs/templates/project/RISK_REGISTER.md",
    "docs/templates/project/OPEN_QUESTIONS.md",
    "docs/templates/project/SOURCE_OF_TRUTH.md",
    "docs/templates/project/QUALITY_GATE_MATRIX.md",
    "docs/templates/release/RELEASE_CHECKLIST.md",
]

REQUIRED_ACTIVE_DOCS = [
    ".ai-factory/DESCRIPTION.md",
    ".ai-factory/ARCHITECTURE.md",
    ".ai-factory/RULES.md",
    "docs/project/PRD.md",
    "docs/project/MVP_SCOPE.md",
    "docs/project/USER_FLOWS.md",
    "docs/project/DATA_MODEL.md",
    "docs/project/TEST_STRATEGY.md",
    "docs/project/DEPLOYMENT.md",
    "docs/project/RISK_REGISTER.md",
    "docs/project/OPEN_QUESTIONS.md",
    "docs/project/SOURCE_OF_TRUTH.md",
    "docs/project/QUALITY_GATE_MATRIX.md",
]

MINIMUM_MARKER = "##"


def _missing(repo_root: Path, paths: list[str]) -> list[str]:
    return [path for path in paths if not (repo_root / path).is_file()]


def _thin_docs(repo_root: Path, paths: list[str]) -> list[str]:
    thin: list[str] = []
    for relative_path in paths:
        path = repo_root / relative_path
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8").strip()
        if MINIMUM_MARKER not in text or len(text) < 120:
            thin.append(relative_path)
    return thin


def validate_project_intake(repo_root: str | Path) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    missing_templates = _missing(root, REQUIRED_TEMPLATE_PATHS)
    missing_active_docs = _missing(root, REQUIRED_ACTIVE_DOCS)
    thin_active_docs = _thin_docs(root, REQUIRED_ACTIVE_DOCS)
    return {
        "ok": not missing_templates and not missing_active_docs and not thin_active_docs,
        "checked_templates": REQUIRED_TEMPLATE_PATHS,
        "checked_active_docs": REQUIRED_ACTIVE_DOCS,
        "missing_templates": missing_templates,
        "missing_active_docs": missing_active_docs,
        "thin_active_docs": thin_active_docs,
    }


def run_self_test() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    result = validate_project_intake(repo_root)
    assert result["ok"], result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", default=str(Path(__file__).resolve().parents[2]))
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args(argv)

    if args.self_test:
        run_self_test()
        print("validate_project_intake self-test passed")
        return 0

    result = validate_project_intake(args.repo)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
