from __future__ import annotations

from copy import deepcopy
from typing import Any

from apps.flange_qc_v2 import __version__
from apps.flange_qc_v2.domain import SubsystemHealth


def build_health_snapshot() -> dict[str, Any]:
    return {
        "service": "flange-qc-v2",
        "version": __version__,
        "status": "degraded",
        "mode": "bootstrap",
        "decision_authority": "none",
        "subsystems": deepcopy(SubsystemHealth.bootstrap().to_payload()),
        "blockers": [
            "qc_product_spec_approval_missing",
            "camera_hardware_validation_missing",
            "model_approval_missing",
            "audit_db_not_configured",
        ],
    }
