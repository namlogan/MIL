from __future__ import annotations

#requirements:
#wmill
import json
import urllib.error
import urllib.request
from typing import Any, Callable

try:
    import wmill  # type: ignore
except ImportError:  # pragma: no cover - local unit tests inject token directly.
    wmill = None  # type: ignore


DEFAULT_API_BASE = "https://api.github.com"
DEFAULT_CONTEXT = "ai-gate/final-review"
DEFAULT_TOKEN_VARIABLE_PATH = "f/mil/github_status_token"
VALID_STATES = {"error", "failure", "pending", "success"}


def _required(value: Any, name: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise ValueError(f"{name} is required")
    return text


def build_status_payload(
    state: str,
    context: str = DEFAULT_CONTEXT,
    description: str = "",
    target_url: str = "",
) -> dict[str, str]:
    normalized_state = _required(state, "state").lower()
    if normalized_state not in VALID_STATES:
        raise ValueError(f"unsupported GitHub status state: {state}")

    payload = {
        "state": normalized_state,
        "context": _required(context, "context"),
        "description": str(description or normalized_state)[:140],
    }
    if target_url:
        payload["target_url"] = str(target_url)
    return payload


def _get_secret_variable(path: str) -> str:
    if wmill is None:
        raise RuntimeError("wmill client is required to read Windmill secret variables")
    return _required(wmill.get_variable(path), "github token")


def publish_commit_status(
    owner: str,
    repo: str,
    sha: str,
    payload: dict[str, str],
    token: str | None = None,
    token_variable_path: str = DEFAULT_TOKEN_VARIABLE_PATH,
    api_base: str = DEFAULT_API_BASE,
    urlopen: Callable[..., Any] = urllib.request.urlopen,
) -> dict[str, Any]:
    github_token = token or _get_secret_variable(token_variable_path)
    url = (
        f"{api_base.rstrip('/')}/repos/"
        f"{_required(owner, 'owner')}/{_required(repo, 'repo')}/statuses/{_required(sha, 'sha')}"
    )
    body = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=body,
        method="POST",
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {github_token}",
            "Content-Type": "application/json",
            "User-Agent": "mil-windmill-ai-gate",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )

    try:
        with urlopen(request, timeout=30) as response:
            raw_response = response.read().decode("utf-8")
            response_body = json.loads(raw_response) if raw_response else {}
            status_code = int(getattr(response, "status", 0))
    except urllib.error.HTTPError as exc:
        error_text = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"GitHub status publish failed: {exc.code} {error_text}") from exc

    return {
        "ok": 200 <= status_code < 300,
        "status_code": status_code,
        "state": payload["state"],
        "context": payload["context"],
        "sha": sha,
        "url": response_body.get("url", ""),
    }


def main(status: dict[str, Any]) -> dict[str, Any]:
    payload = build_status_payload(
        state=_required(status.get("state"), "state"),
        context=str(status.get("context") or DEFAULT_CONTEXT),
        description=str(status.get("description") or ""),
        target_url=str(status.get("target_url") or ""),
    )

    owner = _required(status.get("owner"), "owner")
    repo = _required(status.get("repo"), "repo")
    sha = _required(status.get("sha"), "sha")

    if bool(status.get("dry_run")):
        return {
            "dry_run": True,
            "owner": owner,
            "repo": repo,
            "sha": sha,
            "payload": payload,
        }

    return publish_commit_status(
        owner=owner,
        repo=repo,
        sha=sha,
        payload=payload,
        token_variable_path=str(
            status.get("token_variable_path") or DEFAULT_TOKEN_VARIABLE_PATH
        ),
        api_base=str(status.get("api_base") or DEFAULT_API_BASE),
    )
