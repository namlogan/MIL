from __future__ import annotations

from f.mil.plan_to_pr_contract import run_plan_to_pr


def main(
    request: dict = None,
    task: dict = None,
    options: dict = None,
    memory_context: list = None,
    augment_context: list = None,
) -> dict:
    if request is not None:
        return run_plan_to_pr(request)

    payload: dict = {"task": task or {}}
    if options is not None:
        payload["options"] = options
    if memory_context is not None:
        payload["memory_context"] = memory_context
    if augment_context is not None:
        payload["augment_context"] = augment_context
    return run_plan_to_pr(payload)
