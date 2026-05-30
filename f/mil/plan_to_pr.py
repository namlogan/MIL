from __future__ import annotations

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))

from flow_contract import run_flow


def main(task: dict) -> dict:
    return run_flow("plan_to_pr", task)
