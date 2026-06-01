from __future__ import annotations

from f.mil.flow_contract import run_merge_controller_policy


def main(request: dict) -> dict:
    return run_merge_controller_policy(request)
