from __future__ import annotations

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))

from flow_contract import run_auggie_supervised_advisory


def main(target: dict) -> dict:
    return run_auggie_supervised_advisory(target)
