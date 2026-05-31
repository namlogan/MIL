from __future__ import annotations

from f.mil.flow_contract import run_auggie_supervised_advisory


def main(target: dict) -> dict:
    return run_auggie_supervised_advisory(target)
