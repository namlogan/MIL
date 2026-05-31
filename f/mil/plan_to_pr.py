from __future__ import annotations

from typing import Any

from f.mil.plan_to_pr_contract import run_plan_to_pr


def main(
    request: dict[str, Any] | None = None,
    task: dict[str, Any] | None = None,
    options: dict[str, Any] | None = None,
    memory_context: list[dict[str, Any]] | None = None,
    augment_context: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    if request is not None:
        return run_plan_to_pr(request)

    payload: dict[str, Any] = {"task": task or {}}
    if options is not None:
        payload["options"] = options
    if memory_context is not None:
        payload["memory_context"] = memory_context
    if augment_context is not None:
        payload["augment_context"] = augment_context
    return run_plan_to_pr(payload)
