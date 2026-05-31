from __future__ import annotations

from f.mil.flow_contract import run_flow


def main(task: dict) -> dict:
    return run_flow("plan_to_pr", task)
