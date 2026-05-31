"""MIL Codex worker contract for Windmill and local runner execution."""

from __future__ import annotations

import fnmatch
import re
from pathlib import Path
from typing import Any


DEFAULT_WORKTREE_ROOT = ".ai-factory/tmp/worktrees"
DEFAULT_EVIDENCE_ROOT = ".ai-factory/qa/codex_worker"
DEFAULT_SANDBOX = "workspace-write"
DEFAULT_APPROVAL = "never"
DEFAULT_BRANCH_PREFIX = "agent/"
MAX_PROMPT_TEXT = 8000
MAX_RULE_TEXT = 2500
REQUIRED_RULE_SOURCE_PATHS = (
    ".ai-factory/RULES.md",
    ".ai-factory/rules/base.md",
    ".ai-factory/rules/implementation.md",
    ".ai-factory/rules/quality-gates.md",
    ".ai-factory/rules/security.md",
    ".ai-factory/rules/memory.md",
    ".ai-factory/rules/windmill.md",
)

SECRET_PATTERNS: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"github_pat_[A-Za-z0-9_]{20,}"), "[REDACTED_GITHUB_TOKEN]"),
    (re.compile(r"gh[pousr]_[A-Za-z0-9_]{20,}"), "[REDACTED_GITHUB_TOKEN]"),
    (re.compile(r"sk-[A-Za-z0-9_-]{20,}"), "[REDACTED_OPENAI_KEY]"),
    (
        re.compile(r"(?i)(accessToken\s*[:=]\s*)[A-Za-z0-9._-]{20,}"),
        r"\1[REDACTED_TOKEN]",
    ),
    (
        re.compile(r"(?i)(api[_-]?key\s*[:=]\s*)[A-Za-z0-9._-]{20,}"),
        r"\1[REDACTED_TOKEN]",
    ),
)


class ContractError(ValueError):
    """Raised when a task violates the worker contract."""


def redact_secrets(value: Any) -> str:
    text = str(value)
    for pattern, replacement in SECRET_PATTERNS:
        text = pattern.sub(replacement, text)
    return text


def slugify(value: str, fallback: str = "task") -> str:
    normalized = re.sub(r"[^a-zA-Z0-9]+", "-", value.strip().lower()).strip("-")
    normalized = re.sub(r"-+", "-", normalized)
    return normalized[:80] or fallback


def _as_string_list(value: Any, field: str, required: bool = False) -> list[str]:
    if value is None:
        if required:
            raise ContractError(f"{field} is required")
        return []
    if not isinstance(value, list):
        raise ContractError(f"{field} must be a list")
    result = [redact_secrets(item).strip() for item in value if str(item).strip()]
    if required and not result:
        raise ContractError(f"{field} is required")
    return result


def _required_text(task: dict[str, Any], field: str) -> str:
    value = redact_secrets(task.get(field, "")).strip()
    if not value:
        raise ContractError(f"{field} is required")
    return value


def _optional_text(task: dict[str, Any], field: str, default: str = "") -> str:
    value = redact_secrets(task.get(field, default)).strip()
    return value or default


def normalize_task(task: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(task, dict):
        raise ContractError("task must be an object")

    task_id = _required_text(task, "task_id")
    title = _optional_text(task, "title", task_id)
    issue_id = _optional_text(task, "issue_id", str(task.get("issue") or ""))
    goal = _required_text(task, "goal")
    allowed_files = _as_string_list(task.get("allowed_files"), "allowed_files", required=True)
    checks = _as_string_list(
        task.get("checks") or task.get("required_checks"),
        "checks",
        required=True,
    )
    acceptance = _as_string_list(
        task.get("acceptance_criteria"),
        "acceptance_criteria",
        required=False,
    )
    restricted_changes = _as_string_list(
        task.get("restricted_changes"),
        "restricted_changes",
    )
    out_of_scope_files = _as_string_list(
        task.get("out_of_scope_files"),
        "out_of_scope_files",
    )
    developer_agent = _optional_text(task, "developer_agent", "codex")
    if developer_agent != "codex":
        raise ContractError(f"Codex is the only supported coding agent; got {developer_agent}")

    base_branch = _optional_text(task, "base_branch", "main")
    branch = _optional_text(task, "branch")
    if not branch:
        branch = f"{DEFAULT_BRANCH_PREFIX}{slugify(task_id)}-{slugify(title, 'work')}"

    return {
        "task_id": task_id,
        "issue_id": issue_id,
        "title": title,
        "goal": goal,
        "acceptance_criteria": acceptance,
        "allowed_files": allowed_files,
        "out_of_scope_files": out_of_scope_files,
        "checks": checks,
        "restricted_changes": restricted_changes,
        "developer_agent": developer_agent,
        "base_branch": base_branch,
        "branch": branch,
        "rollback_note": _optional_text(task, "rollback_note", "Revert the PR branch."),
        "memory_context": task.get("memory_context") or [],
        "augment_context": task.get("augment_context") or [],
        "raw": task,
    }


def _repo_path(repo_root: str | Path, relative_path: str) -> str:
    root = Path(repo_root).resolve()
    return str(root / relative_path)


def _worktree_slug(branch: str) -> str:
    branch_slug = branch.split("/", 1)[-1] if "/" in branch else branch
    return slugify(branch_slug)


def _section_entries(config_text: str, section: str) -> dict[str, str]:
    entries: dict[str, str] = {}
    in_section = False
    for raw_line in config_text.splitlines():
        if not raw_line.strip() or raw_line.lstrip().startswith("#"):
            continue
        if raw_line == raw_line.lstrip():
            in_section = raw_line.strip() == f"{section}:"
            continue
        if not in_section or not raw_line.startswith("  ") or raw_line.startswith("    "):
            continue
        stripped = raw_line.split("#", 1)[0].strip()
        if ":" not in stripped:
            continue
        key, value = stripped.split(":", 1)
        value = value.strip().strip("'\"")
        if value:
            entries[key.strip()] = value
    return entries


def _normalize_relative_path(path: str) -> str:
    return path.strip().strip("'\"").rstrip("/")


def _dedupe(paths: list[tuple[str, str]]) -> list[tuple[str, str]]:
    seen: set[str] = set()
    result: list[tuple[str, str]] = []
    for name, path in paths:
        normalized = _normalize_relative_path(path)
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        result.append((name, normalized))
    return result


def resolve_rule_sources(repo_root: str | Path = ".") -> list[dict[str, str]]:
    root = Path(repo_root).resolve()
    config_path = root / ".ai-factory" / "config.yaml"
    paths: dict[str, str] = {}
    rule_entries: dict[str, str] = {}
    if config_path.exists():
        config_text = config_path.read_text(encoding="utf-8")
        paths = _section_entries(config_text, "paths")
        rule_entries = _section_entries(config_text, "rules")

    rules_file = paths.get("rules_file") or ".ai-factory/RULES.md"
    rules_dir = paths.get("rules") or ".ai-factory/rules"
    if rules_dir.endswith(".md"):
        rules_dir = paths.get("rules_dir") or ".ai-factory/rules"

    candidates: list[tuple[str, str]] = [
        ("paths.rules_file", rules_file),
        ("rules.base", rule_entries.get("base") or f"{rules_dir}/base.md"),
    ]
    for name in sorted(key for key in rule_entries if key != "base"):
        candidates.append((f"rules.{name}", rule_entries[name]))

    sources: list[dict[str, str]] = []
    for source_name, relative_path in _dedupe(candidates):
        path = root / relative_path
        if not path.exists() or not path.is_file():
            continue
        content = redact_secrets(path.read_text(encoding="utf-8"))[:MAX_RULE_TEXT]
        sources.append(
            {
                "name": source_name,
                "path": relative_path,
                "content": content,
            }
        )
    return sources


def _normalize_provided_rule_sources(value: Any) -> list[dict[str, str]]:
    if value is None or value == "":
        return []
    if not isinstance(value, list):
        raise ContractError("rule_sources must be a list")

    sources: list[dict[str, str]] = []
    seen_paths: set[str] = set()
    for index, item in enumerate(value, start=1):
        if not isinstance(item, dict):
            raise ContractError("rule_sources entries must be objects")

        name = redact_secrets(item.get("name") or f"provided.{index}").strip()
        path = _normalize_relative_path(redact_secrets(item.get("path") or name))
        content = redact_secrets(item.get("content") or "").strip()
        if not path:
            raise ContractError("rule_sources entries require path")
        if not content:
            raise ContractError(f"rule_sources entry {path} requires content")
        if path in seen_paths:
            continue

        seen_paths.add(path)
        sources.append(
            {
                "name": name or f"provided.{index}",
                "path": path,
                "content": content[:MAX_RULE_TEXT],
            }
        )
    return sources


def _missing_required_rule_sources(rule_sources: list[dict[str, str]]) -> list[str]:
    observed = {source["path"] for source in rule_sources}
    return [path for path in REQUIRED_RULE_SOURCE_PATHS if path not in observed]


def build_paths(
    task: dict[str, Any],
    repo_root: str | Path,
    worktree_root: str = DEFAULT_WORKTREE_ROOT,
    evidence_root: str = DEFAULT_EVIDENCE_ROOT,
) -> dict[str, str]:
    branch_slug = _worktree_slug(str(task["branch"]))
    evidence_dir = _repo_path(repo_root, f"{evidence_root}/{task['task_id']}")
    return {
        "worktree_path": _repo_path(repo_root, f"{worktree_root}/{branch_slug}"),
        "evidence_dir": evidence_dir,
        "prompt_path": f"{evidence_dir}/prompt.md",
        "result_path": f"{evidence_dir}/result.json",
        "codex_last_message_path": f"{evidence_dir}/codex-last-message.md",
    }


def _format_lines(items: list[str], empty: str = "None") -> str:
    if not items:
        return f"- {empty}"
    return "\n".join(f"- {item}" for item in items)


def _compact_context(items: Any, label: str) -> str:
    if not isinstance(items, list) or not items:
        return f"## {label}\n- None"
    lines = [f"## {label}"]
    for index, item in enumerate(items[:12], start=1):
        if isinstance(item, dict):
            memory_id = redact_secrets(
                item.get("memory_id")
                or item.get("id")
                or item.get("source_uri")
                or f"context_{index}"
            )
            text = redact_secrets(
                item.get("memory")
                or item.get("summary")
                or item.get("content")
                or item
            )
            source = redact_secrets(item.get("source_uri", "")).strip()
            suffix = f" ({source})" if source else ""
            lines.append(f"- [{memory_id}]{suffix} {text[:MAX_PROMPT_TEXT]}")
        else:
            lines.append(f"- {redact_secrets(item)[:MAX_PROMPT_TEXT]}")
    return "\n".join(lines)


def _format_rule_sources(rule_sources: list[dict[str, str]]) -> str:
    if not rule_sources:
        return "\n".join(
            [
                "## AI Factory v2 Rule Hierarchy",
                "- No rule sources resolved; stop and request configuration review.",
            ]
        )

    lines = [
        "## AI Factory v2 Rule Hierarchy",
        "- Priority: rules.<area> > rules/base.md > paths.rules_file",
        "- Treat all resolved rules as mandatory unless the task has explicit human-approved exception evidence.",
        "",
        "## Resolved Rule Sources",
    ]
    for source in rule_sources:
        lines.extend(
            [
                f"### {source['name']}: {source['path']}",
                source["content"].strip() or "- Empty rule file.",
                "",
            ]
        )
    return "\n".join(lines).strip()


def build_codex_prompt(
    task: dict[str, Any],
    rule_sources: list[dict[str, str]] | None = None,
) -> str:
    normalized = normalize_task(task)
    resolved_rules = rule_sources or []
    sections = [
        "# MIL Codex Worker Task",
        "You are the Codex implementation worker for the MIL AI Factory.",
        "Source of truth is the GitHub issue or explicit task payload.",
        "Do not edit files outside allowed_files.",
        "Do not read production secrets or write secret values to files, logs, commits, memory, or PR text.",
        "Do not merge, deploy, bypass branch protection, or reinterpret gate policy.",
        "",
        "## Task",
        f"- task_id: {normalized['task_id']}",
        f"- issue_id: {normalized['issue_id'] or 'N/A'}",
        f"- title: {normalized['title']}",
        f"- goal: {normalized['goal']}",
        "",
        "## Acceptance Criteria",
        _format_lines(normalized["acceptance_criteria"]),
        "",
        "## Allowed Files",
        _format_lines(normalized["allowed_files"]),
        "",
        "## Out Of Scope Files",
        _format_lines(normalized["out_of_scope_files"]),
        "",
        "## Required Checks",
        _format_lines(normalized["checks"]),
        "",
        "## Rollback Note",
        f"- {normalized['rollback_note']}",
        "",
        _format_rule_sources(resolved_rules),
        "",
        _compact_context(normalized["memory_context"], "Scoped Operational Memory"),
        "",
        _compact_context(normalized["augment_context"], "Augment Codebase Context"),
        "",
        "## Required Handoff",
        "- Summarize files changed, tests run, residual risks, and rollback note.",
        "- Keep the PR small and scoped to the issue.",
    ]
    return redact_secrets("\n".join(sections).strip() + "\n")


def build_codex_exec_command(
    worktree_path: str,
    output_last_message_path: str,
    *,
    model: str | None = None,
    sandbox: str = DEFAULT_SANDBOX,
    approval: str = DEFAULT_APPROVAL,
) -> list[str]:
    command = [
        "codex",
        "exec",
        "--cd",
        str(worktree_path),
        "--sandbox",
        sandbox,
        "--ask-for-approval",
        approval,
        "--json",
        "--output-last-message",
        str(output_last_message_path),
    ]
    if model:
        command.extend(["--model", model])
    return command


def _matches_any(path: str, patterns: list[str]) -> bool:
    normalized = path[2:] if path.startswith("./") else path
    return any(fnmatch.fnmatch(normalized, pattern) for pattern in patterns)


def validate_allowed_changes(
    changed_files: list[str],
    *,
    allowed_files: list[str],
    out_of_scope_files: list[str],
) -> None:
    for changed_file in changed_files:
        normalized = changed_file.strip()
        normalized = normalized[2:] if normalized.startswith("./") else normalized
        if not normalized:
            continue
        if _matches_any(normalized, out_of_scope_files):
            raise ValueError(f"{normalized} matches out_of_scope_files")
        if not _matches_any(normalized, allowed_files):
            raise ValueError(f"{normalized} is outside allowed_files")


def build_worker_plan(
    task: dict[str, Any],
    *,
    repo_root: str | Path = ".",
    worktree_root: str = DEFAULT_WORKTREE_ROOT,
    evidence_root: str = DEFAULT_EVIDENCE_ROOT,
    execute_agent: bool = False,
    push: bool = False,
    open_pr: bool = False,
    model: str | None = None,
    sandbox: str = DEFAULT_SANDBOX,
    approval: str = DEFAULT_APPROVAL,
    rule_sources: Any | None = None,
) -> dict[str, Any]:
    normalized = normalize_task(task)
    if normalized["restricted_changes"]:
        return {
            "decision": "CODEX_WORKER_BLOCKED",
            "blocking": True,
            "source_of_truth": "github_issue_or_explicit_task",
            "task_id": normalized["task_id"],
            "branch": normalized["branch"],
            "base_branch": normalized["base_branch"],
            "reasons": [
                "restricted_changes require human approval before Codex worker dispatch"
            ],
            "restricted_changes": normalized["restricted_changes"],
            "codex_command": [],
            "codex_stdin_prompt": False,
        }

    paths = build_paths(normalized, repo_root, worktree_root, evidence_root)
    resolved_rule_sources = (
        _normalize_provided_rule_sources(rule_sources)
        or _normalize_provided_rule_sources(normalized["raw"].get("rule_sources"))
        or _normalize_provided_rule_sources(normalized["raw"].get("ai_factory_rule_sources"))
        or resolve_rule_sources(repo_root)
    )
    missing_rule_sources = _missing_required_rule_sources(resolved_rule_sources)
    if not resolved_rule_sources or missing_rule_sources:
        reason = (
            "AI Factory rule sources are required before Codex worker dispatch; "
            "mount repo_root or pass options.rule_sources"
        )
        if missing_rule_sources:
            reason = f"AI Factory rule sources are incomplete: {', '.join(missing_rule_sources)}"
        return {
            "decision": "CODEX_WORKER_BLOCKED",
            "blocking": True,
            "source_of_truth": "github_issue_or_explicit_task",
            "task_id": normalized["task_id"],
            "issue_id": normalized["issue_id"],
            "title": normalized["title"],
            "branch": normalized["branch"],
            "base_branch": normalized["base_branch"],
            "worktree_path": paths["worktree_path"],
            "evidence_dir": paths["evidence_dir"],
            "rule_sources": [
                {"name": source["name"], "path": source["path"]}
                for source in resolved_rule_sources
            ],
            "execution": {
                "execute_agent": bool(execute_agent),
                "push": bool(push),
                "open_pr": bool(open_pr),
                "sandbox": sandbox,
                "approval": approval,
                "model": model or "",
            },
            "reasons": [reason],
            "codex_command": [],
            "codex_stdin_prompt": False,
        }

    prompt = build_codex_prompt(normalized, resolved_rule_sources)
    command = build_codex_exec_command(
        paths["worktree_path"],
        paths["codex_last_message_path"],
        model=model,
        sandbox=sandbox,
        approval=approval,
    )
    return {
        "decision": "CODEX_WORKER_READY",
        "blocking": False,
        "source_of_truth": "github_issue_or_explicit_task",
        "task_id": normalized["task_id"],
        "issue_id": normalized["issue_id"],
        "title": normalized["title"],
        "branch": normalized["branch"],
        "base_branch": normalized["base_branch"],
        "worktree_path": paths["worktree_path"],
        "evidence_dir": paths["evidence_dir"],
        "prompt_path": paths["prompt_path"],
        "result_path": paths["result_path"],
        "codex_last_message_path": paths["codex_last_message_path"],
        "allowed_files": normalized["allowed_files"],
        "out_of_scope_files": normalized["out_of_scope_files"],
        "checks": normalized["checks"],
        "rollback_note": normalized["rollback_note"],
        "rule_sources": [
            {"name": source["name"], "path": source["path"]}
            for source in resolved_rule_sources
        ],
        "execution": {
            "execute_agent": bool(execute_agent),
            "push": bool(push),
            "open_pr": bool(open_pr),
            "sandbox": sandbox,
            "approval": approval,
            "model": model or "",
        },
        "codex_command": command,
        "codex_stdin_prompt": True,
        "prompt": prompt,
        "reasons": [],
    }


def main(request: dict[str, Any] | None = None) -> dict[str, Any]:
    request = request or {}
    task = request.get("task") or request
    options = request.get("options") or {}
    if not isinstance(task, dict):
        raise ContractError("task must be an object")
    if not isinstance(options, dict):
        raise ContractError("options must be an object")

    return build_worker_plan(
        task,
        repo_root=options.get("repo_root", "."),
        worktree_root=options.get("worktree_root", DEFAULT_WORKTREE_ROOT),
        evidence_root=options.get("evidence_root", DEFAULT_EVIDENCE_ROOT),
        execute_agent=bool(options.get("execute_agent", False)),
        push=bool(options.get("push", False)),
        open_pr=bool(options.get("open_pr", False)),
        model=options.get("model") or None,
        sandbox=str(options.get("sandbox") or DEFAULT_SANDBOX),
        approval=str(options.get("approval") or DEFAULT_APPROVAL),
        rule_sources=options.get("rule_sources") or options.get("ai_factory_rule_sources"),
    )
