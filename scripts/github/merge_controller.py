#!/usr/bin/env python3
"""Policy-controlled PR approval and merge helper for the MIL agent factory."""

from __future__ import annotations

import argparse
import fnmatch
import json
import os
import subprocess
from pathlib import Path
from typing import Any, NamedTuple


REPO_ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = REPO_ROOT / ".ai-factory" / "merge-controller.json"


class PolicyResult(NamedTuple):
    decision: str
    blockers: list[str]
    warnings: list[str]
    required_contexts: list[str]
    labels: list[str]
    changed_paths: list[str]


def default_config(repo_root: Path | None = None) -> dict[str, Any]:
    root = repo_root or REPO_ROOT
    config_path = root / ".ai-factory" / "merge-controller.json"
    if config_path.exists():
        return json.loads(config_path.read_text(encoding="utf-8"))
    return {
        "enabled": True,
        "repo": "namlogan/MIL",
        "base_branch": "main",
        "merge_method": "merge",
        "auto_merge": False,
        "token_env": "MIL_MERGE_BOT_TOKEN",
        "bot_username_env": "MIL_MERGE_BOT_USERNAME",
        "identities": {
            "owner": "namlogan",
            "coding_bot": "mil-agent-bot",
            "merge_bot": "mil-merge-bot",
        },
        "required_contexts": ["control-plane", "ai-gate/final-review", "merge-controller-policy"],
        "allowed_head_prefixes": ["agent/", "fix/", "codex/"],
        "allow_labels": ["agent:auto-build", "automerge:candidate", "automerge:allowed", "owner:auto-approve"],
        "owner_approval_labels": ["owner:auto-approve"],
        "block_labels": ["hold", "owner-review", "do-not-merge", "blocked", "security-review"],
        "restricted_labels": [
            "restricted-change",
            "production-deploy",
            "secrets",
            "customer-data",
            "auth-boundary",
            "destructive-migration",
            "legal-compliance",
            "safety-critical",
        ],
        "restricted_paths": [".github/**", ".ai-factory/merge-controller.json", "scripts/github/**"],
        "low_risk_path_prefixes": ["docs/", "tests/", "contracts/"],
        "required_pr_body_markers": ["## Summary", "## Evidence", "## Restricted Change Check", "Rollback"],
        "limits": {
            "max_changed_files": 20,
            "max_additions": 500,
            "max_deletions": 500,
            "max_total_lines": 800,
        },
    }


def _node_list(value: Any) -> list[Any]:
    if isinstance(value, list):
        return value
    if isinstance(value, dict):
        if isinstance(value.get("nodes"), list):
            return value["nodes"]
        if isinstance(value.get("contexts"), dict):
            return _node_list(value["contexts"])
    return []


def _label_names(pr: dict[str, Any]) -> list[str]:
    labels = pr.get("labels")
    if isinstance(labels, list):
        names = []
        for label in labels:
            if isinstance(label, dict) and label.get("name"):
                names.append(str(label["name"]))
            elif isinstance(label, str):
                names.append(label)
        return sorted(names)
    names: list[str] = []
    for node in _node_list(labels):
        if isinstance(node, dict) and node.get("name"):
            names.append(str(node["name"]))
        elif isinstance(node, str):
            names.append(node)
    return sorted(names)


def _changed_paths(pr: dict[str, Any]) -> list[str]:
    paths: list[str] = []
    files = pr.get("files")
    if isinstance(files, list):
        for item in files:
            if isinstance(item, dict) and item.get("path"):
                paths.append(str(item["path"]))
            elif isinstance(item, str):
                paths.append(item)
    return sorted(paths)


def _status_contexts(pr: dict[str, Any]) -> dict[str, str]:
    contexts: dict[str, str] = {}
    for node in _node_list(pr.get("statusCheckRollup")):
        if not isinstance(node, dict):
            continue
        name = node.get("context") or node.get("name") or node.get("workflowName")
        state = node.get("state") or node.get("conclusion") or node.get("status")
        if name and state:
            contexts[str(name)] = str(state).upper()
    return contexts


def _body_has_required_markers(body: str, markers: list[str]) -> list[str]:
    return [marker for marker in markers if marker not in body]


def _matches_any(path: str, patterns: list[str]) -> bool:
    return any(fnmatch.fnmatch(path, pattern) for pattern in patterns)


def _is_low_risk_path(path: str, prefixes: list[str]) -> bool:
    return any(path.startswith(prefix) for prefix in prefixes)


def _latest_pusher(pr: dict[str, Any]) -> str | None:
    explicit = pr.get("latestPusher")
    if isinstance(explicit, str):
        return explicit
    commits = pr.get("commits")
    nodes = _node_list(commits)
    if not nodes:
        return None
    last = nodes[-1]
    if not isinstance(last, dict):
        return None
    commit = last.get("commit") if isinstance(last.get("commit"), dict) else last
    author = commit.get("pushedBy") or commit.get("author") if isinstance(commit, dict) else None
    if isinstance(author, dict) and author.get("login"):
        return str(author["login"])
    return None


def evaluate_pr(
    pr: dict[str, Any],
    config: dict[str, Any],
    *,
    check_required_contexts: bool = True,
    check_merge_state: bool = True,
) -> PolicyResult:
    blockers: list[str] = []
    warnings: list[str] = []
    labels = _label_names(pr)
    label_set = set(labels)
    paths = _changed_paths(pr)
    required_contexts = list(config.get("required_contexts") or [])
    owner_labels = set(config.get("owner_approval_labels") or [])
    allow_labels = set(config.get("allow_labels") or [])
    block_labels = set(config.get("block_labels") or [])
    restricted_labels = set(config.get("restricted_labels") or [])

    if config.get("enabled") is not True:
        return PolicyResult(
            "BLOCKED",
            ["merge controller is disabled"],
            warnings,
            required_contexts,
            labels,
            paths,
        )

    for label in sorted(label_set.intersection(block_labels)):
        blockers.append(f"blocked by label: {label}")
    has_owner_label = bool(label_set.intersection(owner_labels))
    for label in sorted(label_set.intersection(restricted_labels)):
        if has_owner_label:
            warnings.append(f"restricted label owner-approved: {label}")
        else:
            blockers.append(f"restricted label requires owner approval: {label}")

    identities = config.get("identities") or {}
    merge_bot = os.environ.get(str(config.get("bot_username_env") or "")) or identities.get("merge_bot")
    latest_pusher = _latest_pusher(pr)
    if merge_bot and latest_pusher and str(merge_bot) == str(latest_pusher):
        blockers.append("merge bot must be separate from latest pusher")
    if identities.get("coding_bot") and identities.get("merge_bot") == identities.get("coding_bot"):
        blockers.append("coding bot and merge bot identities must be separate")

    if blockers and any(blocker.startswith("blocked by label") or "must be separate" in blocker for blocker in blockers):
        return PolicyResult("BLOCKED", blockers, warnings, required_contexts, labels, paths)

    if pr.get("isDraft") is True:
        blockers.append("draft PR is not mergeable")
    base_branch = str(config.get("base_branch") or "main")
    if pr.get("baseRefName") != base_branch:
        blockers.append(f"base branch must be {base_branch}")
    head = str(pr.get("headRefName") or "")
    allowed_prefixes = list(config.get("allowed_head_prefixes") or [])
    if allowed_prefixes and not any(head.startswith(prefix) for prefix in allowed_prefixes):
        blockers.append(f"head branch must start with one of: {', '.join(allowed_prefixes)}")

    if str(pr.get("reviewDecision") or "").upper() == "CHANGES_REQUESTED":
        blockers.append("review changes requested")

    waiting: list[str] = []
    if check_required_contexts:
        checks = _status_contexts(pr)
        for context in required_contexts:
            state = checks.get(context)
            if state is None:
                waiting.append(f"{context} is missing")
            elif state not in {"SUCCESS", "COMPLETED"}:
                waiting.append(f"{context} is {state}")
    if check_merge_state:
        merge_state = str(pr.get("mergeStateStatus") or "").upper()
        review_decision = str(pr.get("reviewDecision") or "").upper()
        review_block_only = merge_state == "BLOCKED" and review_decision == "REVIEW_REQUIRED"
        if merge_state and merge_state != "CLEAN" and not review_block_only:
            waiting.append(f"merge state is {merge_state}")

    if blockers:
        return PolicyResult("NEEDS_OWNER_APPROVAL", blockers, warnings, required_contexts, labels, paths)
    if waiting:
        return PolicyResult("WAITING_FOR_CHECKS", waiting, warnings, required_contexts, labels, paths)

    missing_markers = _body_has_required_markers(
        str(pr.get("body") or ""),
        list(config.get("required_pr_body_markers") or []),
    )
    for marker in missing_markers:
        blockers.append(f"PR body missing marker: {marker}")

    limits = config.get("limits") or {}
    additions = int(pr.get("additions") or 0)
    deletions = int(pr.get("deletions") or 0)
    if len(paths) > int(limits.get("max_changed_files") or 999999):
        blockers.append("changed file count exceeds merge-controller limit")
    if additions > int(limits.get("max_additions") or 999999):
        blockers.append("additions exceed merge-controller limit")
    if deletions > int(limits.get("max_deletions") or 999999):
        blockers.append("deletions exceed merge-controller limit")
    if additions + deletions > int(limits.get("max_total_lines") or 999999):
        blockers.append("total changed lines exceed merge-controller limit")

    restricted_path_patterns = list(config.get("restricted_paths") or [])
    restricted_paths = [path for path in paths if _matches_any(path, restricted_path_patterns)]
    for path in restricted_paths:
        blockers.append(f"restricted path changed: {path}")

    low_risk_prefixes = list(config.get("low_risk_path_prefixes") or [])
    has_app_code = any(not _is_low_risk_path(path, low_risk_prefixes) for path in paths)
    has_allow_label = bool(label_set.intersection(allow_labels))
    if has_app_code and not has_allow_label:
        blockers.append("app-code PR requires an allow label")
    owner_approvable_prefixes = (
        "changed file count exceeds",
        "additions exceed",
        "deletions exceed",
        "total changed lines exceed",
        "restricted path changed:",
        "app-code PR requires",
    )
    if has_owner_label:
        owner_approved: list[str] = []
        remaining: list[str] = []
        for blocker in blockers:
            if blocker.startswith(owner_approvable_prefixes):
                owner_approved.append(blocker)
            else:
                remaining.append(blocker)
        warnings.extend(owner_approved)
        blockers = remaining
    elif restricted_paths or label_set.intersection(restricted_labels):
        return PolicyResult("NEEDS_OWNER_APPROVAL", blockers, warnings, required_contexts, labels, paths)
    if blockers:
        return PolicyResult("NEEDS_OWNER_APPROVAL", blockers, warnings, required_contexts, labels, paths)

    return PolicyResult("AUTO_APPROVE_AND_MERGE", [], warnings, required_contexts, labels, paths)


def _run(command: list[str], *, env: dict[str, str] | None = None) -> str:
    completed = subprocess.run(command, text=True, capture_output=True, check=False, env=env)
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr.strip() or completed.stdout.strip())
    return completed.stdout


def _fetch_pr(repo: str, number: int) -> dict[str, Any]:
    fields = [
        "additions",
        "baseRefName",
        "body",
        "commits",
        "deletions",
        "files",
        "headRefName",
        "isDraft",
        "labels",
        "mergeStateStatus",
        "number",
        "reviewDecision",
        "statusCheckRollup",
        "title",
        "url",
    ]
    output = _run(["gh", "pr", "view", str(number), "--repo", repo, "--json", ",".join(fields)])
    return json.loads(output)


def _open_pr_numbers(repo: str) -> list[int]:
    output = _run(["gh", "pr", "list", "--repo", repo, "--state", "open", "--json", "number"])
    return [int(item["number"]) for item in json.loads(output)]


def _bot_env(config: dict[str, Any]) -> dict[str, str]:
    token_env = str(config.get("token_env") or "MIL_MERGE_BOT_TOKEN")
    token = os.environ.get(token_env)
    if not token:
        raise RuntimeError(f"{token_env} is required for --execute")
    env = os.environ.copy()
    env["GH_TOKEN"] = token
    return env


def _approve_pr(repo: str, number: int, config: dict[str, Any]) -> None:
    body = (
        "MIL merge-controller approval: required checks and policy gates passed. "
        "Restricted owner controls remain enforced by labels and branch protection."
    )
    _run(
        [
            "gh",
            "api",
            "-X",
            "POST",
            f"repos/{repo}/pulls/{number}/reviews",
            "-f",
            "event=APPROVE",
            "-f",
            f"body={body}",
        ],
        env=_bot_env(config),
    )


def _merge_pr(repo: str, number: int, config: dict[str, Any]) -> None:
    method = str(config.get("merge_method") or "merge")
    command = ["gh", "pr", "merge", str(number), "--repo", repo, "--delete-branch"]
    if config.get("auto_merge") is True:
        command.append("--auto")
    if method == "squash":
        command.append("--squash")
    elif method == "rebase":
        command.append("--rebase")
    else:
        command.append("--merge")
    _run(command, env=_bot_env(config))


def _result_payload(number: int, result: PolicyResult) -> dict[str, Any]:
    return {
        "number": number,
        "decision": result.decision,
        "blockers": result.blockers,
        "warnings": result.warnings,
        "required_contexts": result.required_contexts,
        "labels": result.labels,
        "changed_paths": result.changed_paths,
    }


def run_self_test() -> None:
    result = evaluate_pr(
        {
            "number": 1,
            "isDraft": False,
            "baseRefName": "main",
            "headRefName": "codex/self-test",
            "mergeStateStatus": "CLEAN",
            "additions": 1,
            "deletions": 0,
            "labels": {"nodes": [{"name": "agent:auto-build"}]},
            "statusCheckRollup": {
                "contexts": {
                    "nodes": [
                        {"context": "control-plane", "state": "SUCCESS"},
                        {"context": "ai-gate/final-review", "state": "SUCCESS"},
                        {"context": "merge-controller-policy", "state": "SUCCESS"},
                    ]
                }
            },
            "files": [{"path": "docs/branch-protection.md"}],
            "body": "## Summary\nx\n## Evidence\nx\n## Restricted Change Check\nx\nRollback: revert.",
        },
        default_config(),
    )
    assert result.decision == "AUTO_APPROVE_AND_MERGE", result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo")
    parser.add_argument("--config", default=str(CONFIG_PATH))
    parser.add_argument("--pr", type=int)
    parser.add_argument("--pr-json", help="Evaluate a saved PR JSON payload.")
    parser.add_argument("--scan-open", action="store_true")
    parser.add_argument(
        "--policy-only",
        action="store_true",
        help="Evaluate PR policy only. Let branch protection enforce other required checks.",
    )
    parser.add_argument("--execute", action="store_true", help="Approve and merge when policy allows it.")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args(argv)

    if args.self_test:
        run_self_test()
        print("merge_controller self-test passed")
        return 0

    config_path = Path(args.config)
    config = json.loads(config_path.read_text(encoding="utf-8")) if config_path.exists() else default_config()
    repo = args.repo or str(config.get("repo") or "namlogan/MIL")

    if args.pr_json:
        pr_payload = json.loads(Path(args.pr_json).read_text(encoding="utf-8"))
        result = evaluate_pr(
            pr_payload,
            config,
            check_required_contexts=not args.policy_only,
            check_merge_state=not args.policy_only,
        )
        print(json.dumps(_result_payload(int(pr_payload.get("number") or 0), result), indent=2, sort_keys=True))
        return 0 if result.decision in {"AUTO_APPROVE_AND_MERGE", "WAITING_FOR_CHECKS"} else 1

    numbers = _open_pr_numbers(repo) if args.scan_open else ([args.pr] if args.pr is not None else [])
    if args.scan_open and not numbers:
        print(json.dumps({"repo": repo, "open_prs": [], "decision": "NO_OPEN_PRS"}, indent=2, sort_keys=True))
        return 0
    if not numbers:
        raise SystemExit("--pr, --pr-json, --scan-open, or --self-test is required")

    exit_code = 0
    for number in numbers:
        pr_payload = _fetch_pr(repo, int(number))
        result = evaluate_pr(
            pr_payload,
            config,
            check_required_contexts=not args.policy_only,
            check_merge_state=not args.policy_only,
        )
        print(json.dumps(_result_payload(int(number), result), indent=2, sort_keys=True))
        if args.execute and result.decision == "AUTO_APPROVE_AND_MERGE":
            _approve_pr(repo, int(number), config)
            _merge_pr(repo, int(number), config)
        elif result.decision in {"BLOCKED", "NEEDS_OWNER_APPROVAL"}:
            exit_code = 1
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
