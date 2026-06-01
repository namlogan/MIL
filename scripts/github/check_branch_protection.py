#!/usr/bin/env python3
"""Evaluate GitHub branch protection for the MIL agent factory."""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any


REQUIRED_CONTEXTS = {"control-plane", "ai-gate/final-review"}


def evaluate_branch_protection(
    protection: dict[str, Any],
    *,
    allow_zero_reviews: bool = False,
) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []

    checks = protection.get("required_status_checks") or {}
    contexts = set(checks.get("contexts") or [])
    if not REQUIRED_CONTEXTS.issubset(contexts):
        errors.append("branch protection must require control-plane and ai-gate/final-review")
    if checks.get("strict") is not True:
        errors.append("branch protection must require branches to be up to date")

    reviews = protection.get("required_pull_request_reviews") or {}
    review_count = int(reviews.get("required_approving_review_count") or 0)
    if review_count < 1:
        if allow_zero_reviews:
            warnings.append("zero required reviews allowed only with explicit --allow-zero-reviews")
        else:
            errors.append("real project mode requires at least one approving review")
    if review_count >= 1 and reviews.get("require_code_owner_reviews") is not True:
        warnings.append("CODEOWNERS review is recommended for real project mode")
    if review_count >= 1 and reviews.get("dismiss_stale_reviews") is not True:
        warnings.append("stale review dismissal is recommended for real project mode")

    return {
        "ok": not errors,
        "errors": errors,
        "warnings": warnings,
        "required_contexts": sorted(REQUIRED_CONTEXTS),
        "review_count": review_count,
    }


def _load_from_github(repo: str, branch: str) -> dict[str, Any]:
    completed = subprocess.run(
        ["gh", "api", f"repos/{repo}/branches/{branch}/protection"],
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr.strip() or completed.stdout.strip())
    return json.loads(completed.stdout)


def run_self_test() -> None:
    result = evaluate_branch_protection(
        {
            "required_status_checks": {
                "strict": True,
                "contexts": ["control-plane", "ai-gate/final-review"],
            },
            "required_pull_request_reviews": {"required_approving_review_count": 1},
        },
        allow_zero_reviews=False,
    )
    assert result["ok"], result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", default="namlogan/MIL")
    parser.add_argument("--branch", default="main")
    parser.add_argument("--from-file", help="Evaluate a saved branch protection JSON file.")
    parser.add_argument(
        "--allow-zero-reviews",
        action="store_true",
        help="Explicitly allow zero approving reviews for temporary local/demo use.",
    )
    parser.add_argument(
        "--team-mode",
        action="store_true",
        help="Deprecated no-op; real project mode is the default.",
    )
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args(argv)

    if args.self_test:
        run_self_test()
        print("check_branch_protection self-test passed")
        return 0

    if args.from_file:
        protection = json.loads(Path(args.from_file).read_text(encoding="utf-8"))
    else:
        protection = _load_from_github(args.repo, args.branch)
    result = evaluate_branch_protection(
        protection,
        allow_zero_reviews=args.allow_zero_reviews,
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
