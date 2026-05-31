from __future__ import annotations

from f.mil.flow_contract import run_flow


def main(task: dict) -> dict:
    return run_flow("fix_ci_or_review", task)
