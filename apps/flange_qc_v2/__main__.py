from __future__ import annotations

import json

from apps.flange_qc_v2.health import build_health_snapshot


def main() -> int:
    print(json.dumps(build_health_snapshot(), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
