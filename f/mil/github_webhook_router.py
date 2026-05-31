from __future__ import annotations

#requirements:
#wmill
import hashlib
import hmac
import json
import re
from typing import Any

try:
    import wmill  # type: ignore
except ImportError:  # pragma: no cover - local unit tests inject the secret.
    wmill = None  # type: ignore

from f.mil.flow_contract import run_flow
from f.mil.plan_to_pr_contract import run_plan_to_pr


DEFAULT_WEBHOOK_SECRET_VARIABLE_PATH = "f/mil/github_webhook_secret"
DEFAULT_CHECKS = ["control-plane", "ai-gate/final-review"]
HOSTED_AI_FACTORY_RULE_SOURCES = [
    {
        "name": "paths.rules_file",
        "path": ".ai-factory/RULES.md",
        "content": """# MIL AI Factory Rules

AI Factory 2.x-compatible top-level axioms. Area-specific rules live under
`.ai-factory/rules/` and are registered in `.ai-factory/config.yaml`.

Rule priority: `rules.<area> > rules/base.md > paths.rules_file`.

## Rules

- Start work from a GitHub issue or approved local task file.
- Keep one task per branch and keep implementation inside `allowed_files`.
- Codex is the only implementation worker; Augment, Mem0, and Auggie are context, memory, or advisory lanes only.
- Run implementation through the configured `codex_worker` runner or an explicitly approved local equivalent.
- Write tests or record why tests are not applicable.
- Record developer handoff, checks, risks, rollback note, and worker evidence in the PR or `.ai-factory/qa/`.
- Emit the final machine-readable `aif-gate-result` block after the human summary.
- Allowed MIL merge decisions are `APPROVE_MERGE`, `REQUEST_CHANGES`, `REJECT`, and `BLOCKED_NEEDS_HUMAN`.
- Never merge, deploy, bypass branch protection, or approve restricted work without human approval.
- Never store secrets, raw tokens, customer data, raw proprietary source, or raw transcripts in memory.
- Restricted changes include production deploy behavior, production secrets, billing, customer data retention/deletion, auth boundaries, destructive migrations, legal/compliance behavior, and safety-critical behavior.""",
    },
    {
        "name": "rules.base",
        "path": ".ai-factory/rules/base.md",
        "content": """# Base Rules

> Project-wide base conventions loaded after `.ai-factory/RULES.md`.

## Rules

- Prefer small, reviewable changes tied to one issue and one branch.
- Preserve GitHub as the source of truth for issues, PRs, CI state, review evidence, and merge decisions.
- Keep AI Factory artifacts command-scoped: rules are owned by rule setup, plans by planning, QA by gate/review, and memory by memory writeback.
- When a task needs broad architecture decisions, produce a plan and request approval before implementation.
- Handoffs must include what changed, why it changed, tests run, risks left, and rollback note.
- Use conventional commits for local checkpoint commits and do not add AI co-author trailers.""",
    },
    {
        "name": "rules.implementation",
        "path": ".ai-factory/rules/implementation.md",
        "content": """# Implementation Rules

> Area rules for Codex implementation work and `codex_worker` sessions.

## Rules

- Run implementation through plan/checkpoint discipline: understand issue scope, apply scoped changes, run checks, then produce handoff evidence.
- `codex_worker` must load issue scope, allowed files, checks, Mem0 context, Augment context, and the AI Factory rule hierarchy before coding.
- Do not edit outside `allowed_files`; if required files are missing from scope, stop and request scope expansion.
- Do not silently continue after restricted changes are detected; return a blocked state before creating commands or edits.
- Use isolated worktrees for unattended implementation so worker state cannot pollute `main`.
- Run required checks from the task payload before commit; if a check cannot run, record the blocker as evidence.
- Keep PRs small enough for review; split unrelated work into separate tasks or branches.
- Update docs only when the task or plan requires docs, or when behavior-facing contracts changed.""",
    },
    {
        "name": "rules.memory",
        "path": ".ai-factory/rules/memory.md",
        "content": """# Memory Rules

> Area rules for Mem0-backed project memory.

## Rules

- Treat memory as retrieval hints and operational learning only; never as source of truth for requirements, code, PR state, CI, or merge approval.
- Retrieve memory only with strict tenant, repo, task, memory type, status, visibility, and entity-scope filters.
- Store only distilled operational summaries with provenance, confidence, source URI, and approval state when required.
- Never write secrets, raw tokens, raw transcripts, customer data, full proprietary source, or generated patches before review.
- Architecture decisions, human preferences, repo conventions, review rules, and security policy memory require explicit human approval before writeback.
- Every memory context inserted into a worker prompt must be compact and provenance-bearing.""",
    },
    {
        "name": "rules.quality_gates",
        "path": ".ai-factory/rules/quality-gates.md",
        "content": """# Quality Gate Rules

> Area rules for AI Factory gates, Codex QA, and merge-controller decisions.

## Rules

- Gate output must keep human-readable findings first and append exactly one final `aif-gate-result` JSON block.
- `aif-gate-result` must include `schema_version`, `gate`, `status`, `blocking`, `blockers`, `affected_files`, and `suggested_next`.
- AI Factory 2.x gate status values are lowercase `pass`, `warn`, and `fail`; MIL merge decisions remain `APPROVE_MERGE`, `REQUEST_CHANGES`, `REJECT`, and `BLOCKED_NEEDS_HUMAN`.
- `blocking: true` is allowed only when explicit hard-rule violations, failed required checks, missing required evidence, or restricted-change approval gaps exist.
- Gate checks must inspect issue acceptance criteria, diff scope, required checks, security/restricted triggers, unresolved review threads, memory write policy, and rollback note.
- Final merge remains protected by GitHub branch protection and required status contexts, not by an LLM-only decision.""",
    },
    {
        "name": "rules.security",
        "path": ".ai-factory/rules/security.md",
        "content": """# Security Rules

> Area rules for credentials, restricted changes, and sensitive operations.

## Rules

- Agents must not print, copy, commit, request, or store production secrets.
- All secrets must stay in GitHub or Windmill secret stores and be referenced by variable path or environment name only.
- Hardcoded API keys, tokens, passwords, private keys, and session cookies are blocking security violations.
- Use least-privilege worker credentials: read-only workers inspect, write workers push agent branches, merge workers merge only after protections pass, and release workers require human approval.
- Authentication, authorization, billing, customer data handling, destructive migrations, production deployment behavior, and legal/compliance changes require human approval before merge.
- Security gate findings with concrete secret exposure or auth boundary impact must block the PR.""",
    },
    {
        "name": "rules.windmill",
        "path": ".ai-factory/rules/windmill.md",
        "content": """# Windmill Rules

> Area rules for Windmill orchestration and webhook-driven workers.

## Rules

- Windmill is an orchestrator and audit surface, not the source of truth for requirements or merge approval.
- Windmill may prepare `codex_worker` command packs, dispatch workers, publish statuses, comment on PRs, and request human approval.
- Windmill must not reinterpret gate policy, bypass branch protection, auto-merge code, or continue a worker after PR readiness unless a separate task requires it.
- Windmill write flows must use least-privilege secrets and must not expose token values in logs, memory, prompts, or artifacts.
- GitHub webhook handlers must verify signatures before dispatch and ignore unmatched events without agent calls.
- Public relay or tunnel endpoints must route only the GitHub webhook path into Windmill.""",
    },
]
PR_GATE_ACTIONS = {"opened", "reopened", "synchronize", "ready_for_review"}
ISSUE_ROUTE_ACTIONS = {"opened", "edited", "labeled", "reopened"}
FAILED_WORKFLOW_CONCLUSIONS = {
    "action_required",
    "cancelled",
    "failure",
    "startup_failure",
    "timed_out",
}


def _get_secret_variable(path: str) -> str:
    if wmill is None:
        raise RuntimeError("wmill client is required to read Windmill secret variables")
    value = str(wmill.get_variable(path) or "").strip()
    if not value:
        raise ValueError("GitHub webhook secret variable is empty")
    return value


def _normalize_headers(headers: dict[str, Any]) -> dict[str, str]:
    return {str(key).lower(): str(value) for key, value in headers.items()}


def _verify_github_signature(
    headers: dict[str, str],
    raw_string: str,
    secret: str,
) -> None:
    signature = headers.get("x-hub-signature-256", "")
    if not signature.startswith("sha256="):
        raise ValueError("missing GitHub webhook signature")

    expected = hmac.new(
        secret.encode("utf-8"),
        raw_string.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    observed = signature.removeprefix("sha256=")
    if not hmac.compare_digest(observed, expected):
        raise ValueError("invalid GitHub webhook signature")


def _parse_payload(raw_string: str) -> dict[str, Any]:
    try:
        payload = json.loads(raw_string)
    except json.JSONDecodeError as exc:
        raise ValueError("GitHub webhook body must be JSON") from exc
    if not isinstance(payload, dict):
        raise ValueError("GitHub webhook payload must be a JSON object")
    return payload


def preprocessor(event: dict[str, Any]) -> dict[str, Any]:
    if event.get("kind") not in {"http", "webhook"}:
        raise ValueError("GitHub webhook router expects an HTTP trigger event")

    raw_string = event.get("raw_string")
    if not isinstance(raw_string, str) or not raw_string:
        raise ValueError("missing raw GitHub webhook body")

    headers = _normalize_headers(dict(event.get("headers") or {}))
    secret = _get_secret_variable(DEFAULT_WEBHOOK_SECRET_VARIABLE_PATH)
    _verify_github_signature(headers, raw_string, secret)

    github_event = headers.get("x-github-event", "").strip()
    if not github_event:
        raise ValueError("missing GitHub event header")

    return {
        "request": {
            "github_event": github_event,
            "delivery": headers.get("x-github-delivery", "").strip(),
            "payload": _parse_payload(raw_string),
            "signature_verified": True,
        }
    }


def _labels(issue: dict[str, Any]) -> set[str]:
    names: set[str] = set()
    for label in issue.get("labels") or []:
        if isinstance(label, dict):
            name = label.get("name")
        else:
            name = label
        if name:
            names.add(str(name).strip().lower())
    return names


def _task_id_from_title(title: str, fallback: str) -> str:
    match = re.search(r"\bMIL-\d+\b", title or "", flags=re.IGNORECASE)
    if match:
        return match.group(0).upper()
    return fallback


def _repository(payload: dict[str, Any]) -> str:
    repository = payload.get("repository") or {}
    return str(repository.get("full_name") or "")


def _base_task(task_id: str, goal: str, body: str = "") -> dict[str, Any]:
    return {
        "task_id": task_id,
        "goal": goal,
        "title": goal,
        "body": body,
        "acceptance_criteria": [],
        "allowed_files": [],
        "out_of_scope_files": [],
        "checks": DEFAULT_CHECKS,
        "restricted_changes": [],
        "residual_risks": [],
    }


def _normalize_section_title(title: str) -> str:
    return re.sub(r"\s+", " ", title.strip().lower())


def _issue_form_sections(body: str) -> dict[str, list[str]]:
    sections: dict[str, list[str]] = {}
    current = ""
    for raw_line in body.splitlines():
        line = raw_line.rstrip()
        heading = re.match(r"^###\s+(.+?)\s*$", line)
        if heading:
            current = _normalize_section_title(heading.group(1))
            sections.setdefault(current, [])
            continue
        if current:
            sections[current].append(line)
    return sections


def _section_text(sections: dict[str, list[str]], *names: str) -> str:
    for name in names:
        lines = sections.get(_normalize_section_title(name))
        if lines is not None:
            return "\n".join(lines).strip()
    return ""


def _first_non_empty_line(text: str) -> str:
    for line in text.splitlines():
        stripped = line.strip()
        if stripped:
            return stripped
    return ""


def _markdown_list_items(text: str) -> list[str]:
    items: list[str] = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        match = re.match(r"^[-*]\s+(?:\[[ xX]\]\s*)?(.+?)\s*$", line)
        if match:
            item = match.group(1).strip()
            if item:
                items.append(item)
    if items:
        return items
    return [line.strip() for line in text.splitlines() if line.strip()]


def _file_scope_items(text: str) -> tuple[list[str], list[str]]:
    allowed: list[str] = []
    out_of_scope: list[str] = []
    target: list[str] | None = None
    for raw_line in text.splitlines():
        line = raw_line.strip()
        lowered = line.lower().rstrip(":")
        if lowered in {"allowed", "allowed files"}:
            target = allowed
            continue
        if lowered in {"out of scope", "out-of-scope", "out of scope files"}:
            target = out_of_scope
            continue
        match = re.match(r"^[-*]\s+(.+?)\s*$", line)
        if match and target is not None:
            target.append(match.group(1).strip())
    return allowed, out_of_scope


def _restricted_items(text: str) -> list[str]:
    restricted: list[str] = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        match = re.match(r"^[-*]\s+\[[xX]\]\s+(.+?)\s*$", line)
        if not match:
            continue
        item = match.group(1).strip()
        if item and item.lower() != "none of the above":
            restricted.append(item)
    return restricted


def _parse_issue_form_task_fields(body: str) -> dict[str, Any]:
    sections = _issue_form_sections(body)
    if not sections:
        return {}

    task_id = _first_non_empty_line(_section_text(sections, "Task ID"))
    goal = _section_text(sections, "User or business goal", "Goal")
    acceptance = _markdown_list_items(_section_text(sections, "Acceptance criteria"))
    allowed, out_of_scope = _file_scope_items(
        _section_text(sections, "Allowed files and out-of-scope files", "Allowed files")
    )
    checks = _markdown_list_items(_section_text(sections, "Required checks", "Checks"))
    restricted = _restricted_items(
        _section_text(sections, "Restricted change check", "Restricted changes")
    )
    rollback = _section_text(sections, "Rollback note", "Rollback")

    parsed: dict[str, Any] = {}
    if re.fullmatch(r"MIL-\d+", task_id, flags=re.IGNORECASE):
        parsed["task_id"] = task_id.upper()
    if goal:
        parsed["goal"] = goal
    if acceptance:
        parsed["acceptance_criteria"] = acceptance
    if allowed:
        parsed["allowed_files"] = allowed
    if out_of_scope:
        parsed["out_of_scope_files"] = out_of_scope
    if checks:
        parsed["checks"] = checks
    if restricted:
        parsed["restricted_changes"] = restricted
    if rollback:
        parsed["rollback_note"] = rollback
    return parsed


def _hosted_rule_sources() -> list[dict[str, str]]:
    return [dict(source) for source in HOSTED_AI_FACTORY_RULE_SOURCES]


def _plan_to_pr_options(request: dict[str, Any]) -> dict[str, Any]:
    options = request.get("options") or {}
    if not isinstance(options, dict):
        options = {}
    normalized = dict(options)
    if not normalized.get("rule_sources") and not normalized.get("ai_factory_rule_sources"):
        normalized["rule_sources"] = _hosted_rule_sources()
    return normalized


def _github_context(
    event: str,
    payload: dict[str, Any],
    delivery: str,
) -> dict[str, Any]:
    issue = payload.get("issue") or {}
    pull_request = payload.get("pull_request") or {}
    workflow_run = payload.get("workflow_run") or {}
    workflow_prs = workflow_run.get("pull_requests") or []
    workflow_pr = workflow_prs[0] if workflow_prs else {}

    return {
        "event": event,
        "delivery": delivery,
        "repository": _repository(payload),
        "action": payload.get("action", ""),
        "issue_number": issue.get("number"),
        "pr_number": pull_request.get("number") or workflow_pr.get("number"),
        "head_sha": (
            (pull_request.get("head") or {}).get("sha")
            or workflow_run.get("head_sha")
            or ""
        ),
        "url": pull_request.get("html_url") or "",
    }


def _matched(
    flow: str,
    task: dict[str, Any],
    github: dict[str, Any],
    reason: str,
) -> dict[str, Any]:
    return {
        "matched": True,
        "flow": flow,
        "task": task,
        "github": github,
        "reason": reason,
    }


def _ignored(github: dict[str, Any], reason: str) -> dict[str, Any]:
    return {
        "matched": False,
        "github": github,
        "reason": reason,
    }


def _route_issue_event(
    payload: dict[str, Any],
    github: dict[str, Any],
) -> dict[str, Any]:
    action = str(payload.get("action") or "")
    issue = payload.get("issue") or {}
    if action not in ISSUE_ROUTE_ACTIONS:
        return _ignored(github, f"ignored issues.{action}")

    label_names = _labels(issue)
    title = str(issue.get("title") or "")
    body = str(issue.get("body") or "")
    parsed_fields = _parse_issue_form_task_fields(body)
    task_id = str(
        parsed_fields.get("task_id")
        or _task_id_from_title(title, f"MIL-{int(issue.get('number') or 0):03d}")
    )
    task = _base_task(task_id, title, body)
    task.update(parsed_fields)

    if "agent:plan" in label_names:
        return _matched("issue_to_plan", task, github, "issue has agent:plan label")
    if "agent:build" in label_names or "agent:auto-build" in label_names:
        return _matched("plan_to_pr", task, github, "issue has build routing label")
    return _ignored(github, "issue has no agent routing label")


def _route_pull_request_event(
    payload: dict[str, Any],
    github: dict[str, Any],
) -> dict[str, Any]:
    action = str(payload.get("action") or "")
    pull_request = payload.get("pull_request") or {}
    if action not in PR_GATE_ACTIONS:
        return _ignored(github, f"ignored pull_request.{action}")
    if pull_request.get("draft"):
        return _ignored(github, "draft pull request is not gateable")

    title = str(pull_request.get("title") or "")
    number = int(pull_request.get("number") or 0)
    task = _base_task(_task_id_from_title(title, f"PR-{number}"), title)
    task["pr_number"] = number
    task["branch"] = str((pull_request.get("head") or {}).get("ref") or "")
    task["head_sha"] = str((pull_request.get("head") or {}).get("sha") or "")
    return _matched("pr_quality_gate", task, github, "pull request is ready for gate")


def _route_workflow_run_event(
    payload: dict[str, Any],
    github: dict[str, Any],
) -> dict[str, Any]:
    action = str(payload.get("action") or "")
    workflow_run = payload.get("workflow_run") or {}
    if action != "completed":
        return _ignored(github, f"ignored workflow_run.{action}")

    pull_requests = workflow_run.get("pull_requests") or []
    if not pull_requests:
        return _ignored(github, "workflow_run has no pull request context")

    pr_number = int((pull_requests[0] or {}).get("number") or 0)
    task = _base_task(f"PR-{pr_number}", f"Workflow run for PR #{pr_number}")
    task["pr_number"] = pr_number
    task["head_sha"] = str(workflow_run.get("head_sha") or "")

    conclusion = str(workflow_run.get("conclusion") or "")
    if conclusion in FAILED_WORKFLOW_CONCLUSIONS:
        return _matched("fix_ci_or_review", task, github, f"workflow_run {conclusion}")
    if conclusion == "success":
        return _matched("pr_quality_gate", task, github, "workflow_run success")
    return _ignored(github, f"ignored workflow conclusion {conclusion}")


def _route_issue_comment_event(
    payload: dict[str, Any],
    github: dict[str, Any],
) -> dict[str, Any]:
    action = str(payload.get("action") or "")
    if action != "created":
        return _ignored(github, f"ignored issue_comment.{action}")

    issue = payload.get("issue") or {}
    comment = payload.get("comment") or {}
    body = str(comment.get("body") or "").strip().lower()
    title = str(issue.get("title") or "")
    issue_body = str(issue.get("body") or "")
    parsed_fields = _parse_issue_form_task_fields(issue_body)
    task_id = str(
        parsed_fields.get("task_id")
        or _task_id_from_title(title, f"MIL-{int(issue.get('number') or 0):03d}")
    )
    task = _base_task(task_id, title, issue_body)
    task.update(parsed_fields)
    task["issue_number"] = issue.get("number")

    if "/agent plan" in body:
        return _matched("issue_to_plan", task, github, "comment requested plan")
    if "/agent build" in body or "/agent autobuild" in body or "/agent auto-build" in body:
        return _matched("plan_to_pr", task, github, "comment requested build")
    if "/agent qa" in body or "/agent gate" in body:
        return _matched("pr_quality_gate", task, github, "comment requested QA gate")
    if "/agent fix" in body:
        return _matched("fix_ci_or_review", task, github, "comment requested fix")
    return _ignored(github, "issue comment has no supported agent command")


def route_github_webhook(request: dict[str, Any]) -> dict[str, Any]:
    event = str(request.get("github_event") or "").strip()
    payload = request.get("payload")
    if not isinstance(payload, dict):
        raise ValueError("request requires payload object")
    github = _github_context(event, payload, str(request.get("delivery") or ""))

    if event == "issues":
        return _route_issue_event(payload, github)
    if event == "pull_request":
        return _route_pull_request_event(payload, github)
    if event == "workflow_run":
        return _route_workflow_run_event(payload, github)
    if event == "issue_comment":
        return _route_issue_comment_event(payload, github)
    return _ignored(github, f"unsupported GitHub event {event}")


def main(request: dict[str, Any]) -> dict[str, Any]:
    route = route_github_webhook(request)
    if not route["matched"]:
        return {
            "decision": "IGNORED_NO_ROUTE",
            "route": route,
        }

    if route["flow"] == "plan_to_pr":
        result = run_plan_to_pr(
            {
                "task": route["task"],
                "options": _plan_to_pr_options(request),
                "memory_context": request.get("memory_context", []),
                "augment_context": request.get("augment_context", []),
            }
        )
    else:
        result = run_flow(route["flow"], route["task"])

    return {
        "decision": "ROUTED_TO_FLOW",
        "route": route,
        "result": result,
    }
