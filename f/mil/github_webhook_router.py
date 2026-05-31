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
    if "agent:build" in label_names:
        return _matched("plan_to_pr", task, github, "issue has agent:build label")
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
    task_id = _task_id_from_title(title, f"MIL-{int(issue.get('number') or 0):03d}")
    task = _base_task(task_id, title)
    task["issue_number"] = issue.get("number")

    if "/agent plan" in body:
        return _matched("issue_to_plan", task, github, "comment requested plan")
    if "/agent build" in body:
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
        options = request.get("options") or {}
        if not isinstance(options, dict):
            options = {}
        result = run_plan_to_pr(
            {
                "task": route["task"],
                "options": options,
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
