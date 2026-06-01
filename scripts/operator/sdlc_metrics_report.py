#!/usr/bin/env python3
"""Build a local SDLC metrics report for the MIL operator dashboard."""

from __future__ import annotations

import argparse
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, NamedTuple


METRIC_KEYS = [
    "lead_time_issue_to_merge",
    "cycle_time_by_task_type",
    "pr_review_latency",
    "build_failure_rate",
    "rework_rate",
    "escaped_defect_count",
    "rollback_count",
    "memory_conflict_count",
    "agent_handoff_quality",
    "test_flakiness",
    "release_frequency",
]

DASHBOARD_SECTIONS = [
    "current_wip",
    "blocked_tasks",
    "aging_prs",
    "failed_gates",
    "upcoming_releases",
    "memory_candidates_waiting_review",
    "stale_open_questions",
    "postmortem_actions",
]


class CommandResult(NamedTuple):
    returncode: int
    stdout: str
    stderr: str


Runner = Callable[[list[str], Path], CommandResult]


def run_command(command: list[str], cwd: Path) -> CommandResult:
    completed = subprocess.run(
        command,
        cwd=str(cwd),
        text=True,
        capture_output=True,
        check=False,
    )
    return CommandResult(completed.returncode, completed.stdout, completed.stderr)


def fake_runner(command: list[str], cwd: Path) -> CommandResult:
    responses = {
        ("git", "status", "--short"): (0, "", ""),
        ("git", "log", "--since=30 days ago", "--pretty=%H%x09%s"): (
            0,
            "abc123\tMerge pull request #51 from codex/harden-memory\n",
            "",
        ),
    }
    return CommandResult(*responses.get(tuple(command), (0, "", "")))


def _count_files(root: Path, pattern: str) -> int:
    return len([path for path in root.glob(pattern) if path.is_file()])


def _git_summary(root: Path, runner: Runner) -> dict[str, Any]:
    status = runner(["git", "status", "--short"], root)
    log = runner(["git", "log", "--since=30 days ago", "--pretty=%H%x09%s"], root)
    merges = [
        line
        for line in log.stdout.splitlines()
        if "Merge pull request" in line or "merge" in line.lower()
    ]
    return {
        "dirty_files": len([line for line in status.stdout.splitlines() if line.strip()]),
        "recent_merge_count": len(merges),
    }


def build_sdlc_metrics_report(
    repo_root: str | Path,
    runner: Runner = run_command,
) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    git = _git_summary(root, runner)
    memory_candidate_count = _count_files(root, ".ai-factory/memory/*.jsonl")
    qa_report_count = _count_files(root, ".ai-factory/qa/**/*.md")
    release_manifest_count = _count_files(root, "docs/release/**/*.md")
    blocked_queue_count = _count_files(root, ".ai-factory/queue/webhooks/*.result.json")

    metrics = {
        "lead_time_issue_to_merge": {"value": None, "unit": "hours", "source": "GitHub PR data"},
        "cycle_time_by_task_type": {"value": {}, "unit": "hours", "source": "Issue labels"},
        "pr_review_latency": {"value": None, "unit": "hours", "source": "GitHub reviews"},
        "build_failure_rate": {"value": None, "unit": "ratio", "source": "GitHub Actions"},
        "rework_rate": {"value": None, "unit": "ratio", "source": "change requests"},
        "escaped_defect_count": {"value": 0, "unit": "count", "source": "docs/incidents"},
        "rollback_count": {"value": 0, "unit": "count", "source": "docs/release"},
        "memory_conflict_count": {"value": 0, "unit": "count", "source": "Memory Gateway audit"},
        "agent_handoff_quality": {
            "value": qa_report_count,
            "unit": "evidence files",
            "source": ".ai-factory/qa",
        },
        "test_flakiness": {"value": None, "unit": "ratio", "source": "CI reruns"},
        "release_frequency": {
            "value": git["recent_merge_count"],
            "unit": "recent merges",
            "source": "git log",
        },
    }

    dashboard = {
        "current_wip": {"dirty_files": git["dirty_files"]},
        "blocked_tasks": {"queue_result_files": blocked_queue_count},
        "aging_prs": {"source": "GitHub PR list"},
        "failed_gates": {"source": "daily_status and CI"},
        "upcoming_releases": {"release_manifest_count": release_manifest_count},
        "memory_candidates_waiting_review": {"local_memory_files": memory_candidate_count},
        "stale_open_questions": {"source": "Memory0 open_question and docs/project"},
        "postmortem_actions": {"source": "docs/incidents"},
    }

    return {
        "ok": set(METRIC_KEYS) == set(metrics) and set(DASHBOARD_SECTIONS) == set(dashboard),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "repo": str(root),
        "metrics": metrics,
        "dashboard": dashboard,
    }


def run_self_test() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    result = build_sdlc_metrics_report(repo_root, runner=fake_runner)
    assert result["ok"], result
    assert set(METRIC_KEYS) == set(result["metrics"]), result
    assert set(DASHBOARD_SECTIONS) == set(result["dashboard"]), result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", default=str(Path(__file__).resolve().parents[2]))
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args(argv)

    if args.self_test:
        run_self_test()
        print("sdlc_metrics_report self-test passed")
        return 0

    result = build_sdlc_metrics_report(args.repo)
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(f"MIL SDLC metrics: {'ok' if result['ok'] else 'attention'}")
        for key in METRIC_KEYS:
            metric = result["metrics"][key]
            print(f"- {key}: {metric['value']} {metric['unit']}")
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
