"""Policy facade for Memory0 gateway operations."""

from __future__ import annotations

from f.mil.memory_contract import (
    ALLOWED_MEMORY_TYPES,
    ALLOWED_SCOPES,
    ALLOWED_STATUSES,
    SOURCE_OF_TRUTH_PRIORITY,
)


def policy_summary() -> dict[str, object]:
    return {
        "allowed_memory_types": sorted(ALLOWED_MEMORY_TYPES),
        "allowed_scopes": sorted(ALLOWED_SCOPES),
        "allowed_statuses": sorted(ALLOWED_STATUSES),
        "source_of_truth_priority": SOURCE_OF_TRUTH_PRIORITY,
        "retrievable_status": "approved",
    }
