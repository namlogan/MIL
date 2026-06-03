from __future__ import annotations

from copy import deepcopy
from typing import Any

from apps.flange_qc_v2 import __version__
from apps.flange_qc_v2.domain import SubsystemHealth
from apps.flange_qc_v2.model_artifact import CONTRACT_VERSION as MODEL_ARTIFACT_CONTRACT_VERSION


def build_health_snapshot() -> dict[str, Any]:
    return {
        "service": "flange-qc-v2",
        "version": __version__,
        "status": "degraded",
        "mode": "bootstrap",
        "decision_authority": "none",
        "subsystems": deepcopy(SubsystemHealth.bootstrap().to_payload()),
        "model_boundary": {
            "contract_version": MODEL_ARTIFACT_CONTRACT_VERSION,
            "state": "manifest_ready_parallel_qc_only",
            "production_authority": False,
            "approval_required": [
                "MODEL_APPROVAL_REQUIRED",
                "PRODUCTION_APPROVAL_REQUIRED",
            ],
        },
        "blockers": [
            "qc_product_spec_approval_missing",
            "qc_sop_tolerance_approval_missing",
            "camera_hardware_validation_missing",
            "model_approval_missing",
            "audit_db_not_configured",
        ],
    }
