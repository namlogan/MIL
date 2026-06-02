from __future__ import annotations

from copy import deepcopy
from typing import Any

from apps.flange_qc_v2 import __version__


_BOOTSTRAP_SUBSYSTEMS = {
    "camera": "unavailable",
    "gpu": "unavailable",
    "model": "unavailable",
    "product_specs": "draft_requires_qc_owner_approval",
    "sop_decision_engine": "not_implemented",
    "audit_db": "not_configured",
    "replay_source": "not_configured",
}


def build_health_snapshot() -> dict[str, Any]:
    return {
        "service": "flange-qc-v2",
        "version": __version__,
        "status": "degraded",
        "mode": "bootstrap",
        "decision_authority": "none",
        "subsystems": deepcopy(_BOOTSTRAP_SUBSYSTEMS),
        "blockers": [
            "qc_product_spec_approval_missing",
            "camera_hardware_validation_missing",
            "model_approval_missing",
            "audit_db_not_configured",
        ],
    }
