"""MIL scoped memory contract for local and Windmill execution."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


DEFAULT_PROJECT = "MIL"
DEFAULT_STORE_PATH = Path(".ai-factory/memory/local_memory.jsonl")

AUTO_WRITE_MEMORY_TYPES = {
    "plan",
    "developer_handoff",
    "qa_gate",
    "merge_gate",
    "ci_pattern",
    "review_note",
    "operator_note",
    "failure_pattern",
    "agent_performance",
    "incident_learning",
    "run_summary",
    "tool_failure",
}
APPROVAL_REQUIRED_MEMORY_TYPES = {
    "repo_convention",
    "architecture_decision",
    "human_preference",
    "review_rule",
    "security_policy",
}
ALLOWED_MEMORY_TYPES = AUTO_WRITE_MEMORY_TYPES | APPROVAL_REQUIRED_MEMORY_TYPES
REQUIRED_METADATA_FIELDS = (
    "tenant_id",
    "workspace_id",
    "repo",
    "repo_id",
    "source_uri",
    "confidence",
    "status",
    "visibility",
    "created_by",
)
ENTITY_SCOPE_FIELDS = ("user_id", "agent_id", "app_id", "run_id")
ALLOWED_STATUSES = {"active", "draft", "superseded", "retired"}
ALLOWED_VISIBILITIES = {"repo", "workspace", "tenant", "private"}

SECRET_PATTERNS = [
    (re.compile(r"github_pat_[A-Za-z0-9_]{20,}"), "[REDACTED_GITHUB_TOKEN]"),
    (re.compile(r"(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9_]{20,}"), "[REDACTED_GITHUB_TOKEN]"),
    (re.compile(r"sk-[A-Za-z0-9_-]{20,}"), "[REDACTED_API_KEY]"),
    (re.compile(r"(?i)bearer\s+[A-Za-z0-9._-]{20,}"), "Bearer [REDACTED_TOKEN]"),
    (
        re.compile(
            r"(?i)\b(accessToken|authtoken|api[_-]?key|token|secret|password)"
            r"(\s*[:=]\s*)[\"']?[A-Za-z0-9._:/+=-]{12,}[\"']?"
        ),
        r"\1\2[REDACTED_SECRET]",
    ),
]


def sanitize_text(text: str) -> str:
    sanitized = text
    for pattern, replacement in SECRET_PATTERNS:
        sanitized = pattern.sub(replacement, sanitized)
    return sanitized


def sanitize_value(value: Any) -> Any:
    if isinstance(value, str):
        return sanitize_text(value)
    if isinstance(value, list):
        return [sanitize_value(item) for item in value]
    if isinstance(value, dict):
        return {str(key): sanitize_value(item) for key, item in value.items()}
    return value


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _required_text(value: Any, label: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise ValueError(f"{label} is required")
    return text


def _coerce_confidence(value: Any) -> float:
    try:
        confidence = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError("metadata.confidence must be a number between 0 and 1") from exc
    if confidence < 0 or confidence > 1:
        raise ValueError("metadata.confidence must be a number between 0 and 1")
    return confidence


def _entity_scope(metadata: dict[str, Any]) -> dict[str, str]:
    scope = {
        field: str(metadata[field]).strip()
        for field in ENTITY_SCOPE_FIELDS
        if str(metadata.get(field) or "").strip()
    }
    if not scope:
        raise ValueError("at least one Mem0 entity scope is required")
    return scope


def _validate_metadata(
    metadata: dict[str, Any],
    *,
    memory_type: str,
    approved: bool,
) -> dict[str, Any]:
    for field in REQUIRED_METADATA_FIELDS:
        if not str(metadata.get(field) or "").strip():
            raise ValueError(f"metadata.{field} is required")

    metadata = dict(metadata)
    metadata["confidence"] = _coerce_confidence(metadata["confidence"])

    status = str(metadata["status"]).strip()
    if status not in ALLOWED_STATUSES:
        raise ValueError(f"metadata.status must be one of {sorted(ALLOWED_STATUSES)}")
    visibility = str(metadata["visibility"]).strip()
    if visibility not in ALLOWED_VISIBILITIES:
        raise ValueError(f"metadata.visibility must be one of {sorted(ALLOWED_VISIBILITIES)}")

    if memory_type in APPROVAL_REQUIRED_MEMORY_TYPES:
        if not approved or not str(metadata.get("approved_by") or "").strip():
            raise ValueError(f"memory_type {memory_type} requires approval")

    metadata.setdefault("source", "mil-ai-factory")
    metadata["memory_type"] = memory_type
    return metadata


def write_policy_for(memory_type: str) -> str:
    if memory_type in AUTO_WRITE_MEMORY_TYPES:
        return "auto"
    if memory_type in APPROVAL_REQUIRED_MEMORY_TYPES:
        return "approval_required"
    raise ValueError(f"unsupported memory_type: {memory_type}")


def build_memory_record(
    *,
    project: str,
    task_id: str,
    memory_type: str,
    text: str,
    metadata: dict[str, Any] | None = None,
    approved: bool = False,
) -> dict[str, Any]:
    project = _required_text(project, "project")
    task_id = _required_text(task_id, "task_id")
    memory_type = _required_text(memory_type, "memory_type")
    policy = write_policy_for(memory_type)

    sanitized_text = sanitize_text(text).strip()
    if not sanitized_text:
        raise ValueError("text is required")

    record_metadata = sanitize_value(metadata or {})
    if not isinstance(record_metadata, dict):
        raise ValueError("metadata must be a JSON object")
    record_metadata = _validate_metadata(
        record_metadata,
        memory_type=memory_type,
        approved=approved,
    )
    entity_scope = _entity_scope(record_metadata)

    return {
        "version": 2,
        "project": project,
        "task_id": task_id,
        "memory_type": memory_type,
        "memory": sanitized_text,
        "metadata": record_metadata,
        "entity_scope": entity_scope,
        "retention_scope": {
            "tenant_id": record_metadata["tenant_id"],
            "workspace_id": record_metadata["workspace_id"],
            "repo_id": record_metadata["repo_id"],
            "visibility": record_metadata["visibility"],
            "status": record_metadata["status"],
        },
        "write_policy": policy,
        "created_at": _utc_now(),
        "sanitized": True,
    }


def _memory_type_conditions(memory_types: list[str]) -> dict[str, Any]:
    if len(memory_types) == 1:
        return {"memory_type": memory_types[0]}
    return {"OR": [{"memory_type": memory_type} for memory_type in memory_types]}


def _entity_conditions(entity_scope: dict[str, str]) -> dict[str, Any]:
    conditions = [{field: value} for field, value in entity_scope.items()]
    if len(conditions) == 1:
        return conditions[0]
    return {"OR": conditions}


def build_search_filters(
    *,
    tenant_id: str | None = None,
    repo_id: str | None = None,
    memory_types: list[str] | tuple[str, ...] | None = None,
    status: str = "active",
    visibility: str = "repo",
    workspace_id: str | None = None,
    user_id: str | None = None,
    agent_id: str | None = None,
    app_id: str | None = None,
    run_id: str | None = None,
    branch: str | None = None,
) -> dict[str, Any]:
    tenant_id = _required_text(tenant_id, "tenant_id")
    repo_id = _required_text(repo_id, "repo_id")
    normalized_types = [str(memory_type).strip() for memory_type in (memory_types or [])]
    normalized_types = [memory_type for memory_type in normalized_types if memory_type]
    if not normalized_types:
        raise ValueError("at least one memory_type is required")
    for memory_type in normalized_types:
        write_policy_for(memory_type)

    entity_scope = {
        "user_id": user_id,
        "agent_id": agent_id,
        "app_id": app_id,
        "run_id": run_id,
    }
    entity_scope = {
        field: str(value).strip()
        for field, value in entity_scope.items()
        if str(value or "").strip()
    }
    if not entity_scope:
        raise ValueError("at least one Mem0 entity scope is required")

    filters: list[dict[str, Any]] = [
        {"tenant_id": tenant_id},
        {"repo_id": repo_id},
        {"status": status},
        {"visibility": visibility},
        _memory_type_conditions(normalized_types),
        _entity_conditions(entity_scope),
    ]
    if workspace_id:
        filters.insert(1, {"workspace_id": str(workspace_id).strip()})
    if branch:
        filters.append({"branch": str(branch).strip()})
    return {"AND": filters}


def _tokens(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9_:-]+", text.lower()))


def _lookup_value(record: dict[str, Any], key: str) -> Any:
    if key in record:
        return record[key]
    metadata = record.get("metadata")
    if isinstance(metadata, dict) and key in metadata:
        return metadata[key]
    scope = record.get("entity_scope")
    if isinstance(scope, dict) and key in scope:
        return scope[key]
    return None


def _condition_matches(record: dict[str, Any], condition: dict[str, Any]) -> bool:
    if "AND" in condition:
        return all(_condition_matches(record, item) for item in condition["AND"])
    if "OR" in condition:
        return any(_condition_matches(record, item) for item in condition["OR"])
    if "NOT" in condition:
        negated = condition["NOT"]
        if isinstance(negated, list):
            return not any(_condition_matches(record, item) for item in negated)
        return not _condition_matches(record, negated)

    for key, expected in condition.items():
        actual = _lookup_value(record, key)
        if isinstance(expected, dict):
            if "eq" in expected and actual != expected["eq"]:
                return False
            if "ne" in expected and actual == expected["ne"]:
                return False
            if "contains" in expected and str(expected["contains"]) not in str(actual or ""):
                return False
            if "in" in expected and actual not in expected["in"]:
                return False
        elif actual != expected:
            return False
    return True


def _ensure_strict_filters(filters: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(filters, dict) or "AND" not in filters:
        raise ValueError("strict filters are required for memory search")
    serialized = json.dumps(filters, sort_keys=True)
    for required in ["tenant_id", "repo_id", "memory_type"]:
        if required not in serialized:
            raise ValueError(f"strict filters are required for memory search: missing {required}")
    if not any(field in serialized for field in ENTITY_SCOPE_FIELDS):
        raise ValueError("strict filters are required for memory search: missing entity scope")
    return filters


@dataclass(frozen=True)
class LocalJsonlMemoryStore:
    path: Path

    def add(self, record: dict[str, Any]) -> dict[str, Any]:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, sort_keys=True) + "\n")
        return record

    def iter_records(self) -> Iterable[dict[str, Any]]:
        if not self.path.exists():
            return []

        records: list[dict[str, Any]] = []
        for line_number, line in enumerate(self.path.read_text(encoding="utf-8").splitlines(), 1):
            if not line.strip():
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"invalid JSONL memory at line {line_number}: {exc}") from exc
            if isinstance(record, dict):
                records.append(record)
        return records

    def search(
        self,
        query: str,
        *,
        filters: dict[str, Any] | None = None,
        limit: int = 5,
    ) -> list[dict[str, Any]]:
        return search_records(self.iter_records(), query, filters=filters, limit=limit)


def search_records(
    records: Iterable[dict[str, Any]],
    query: str,
    *,
    filters: dict[str, Any] | None = None,
    limit: int = 5,
) -> list[dict[str, Any]]:
    strict_filters = _ensure_strict_filters(filters)
    query_tokens = _tokens(query)
    scored: list[tuple[int, str, dict[str, Any]]] = []
    for record in records:
        if not _condition_matches(record, strict_filters):
            continue

        memory = str(record.get("memory") or "")
        record_tokens = _tokens(memory)
        score = len(query_tokens & record_tokens)
        if query.lower() and query.lower() in memory.lower():
            score += 3
        if not query_tokens:
            score = 1
        if score > 0:
            scored.append((score, str(record.get("created_at") or ""), record))

    scored.sort(key=lambda item: (item[0], item[1]), reverse=True)
    return [record for _, _, record in scored[:limit]]


def build_mem0_add_payload(record: dict[str, Any]) -> dict[str, Any]:
    entity_scope = record.get("entity_scope")
    if not isinstance(entity_scope, dict) or not entity_scope:
        raise ValueError("record.entity_scope is required")
    metadata = dict(record.get("metadata") or {})
    metadata.update(
        {
            "project": record.get("project"),
            "task_id": record.get("task_id"),
            "memory_type": record.get("memory_type"),
            "source_uri": metadata.get("source_uri"),
        }
    )
    payload: dict[str, Any] = {
        "messages": [{"role": "user", "content": str(record.get("memory") or "")}],
        "metadata": metadata,
        "infer": False,
    }
    payload.update(entity_scope)
    return payload


def build_mem0_search_payload(
    query: str,
    *,
    filters: dict[str, Any],
    limit: int = 5,
) -> dict[str, Any]:
    return {
        "query": _required_text(query, "query"),
        "filters": _ensure_strict_filters(filters),
        "limit": int(limit),
    }


def build_context_pack(records: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    pack: list[dict[str, Any]] = []
    for index, record in enumerate(records, 1):
        metadata = record.get("metadata") if isinstance(record.get("metadata"), dict) else {}
        pack.append(
            {
                "memory_id": str(record.get("memory_id") or record.get("id") or f"local-{index}"),
                "memory_type": str(record.get("memory_type") or metadata.get("memory_type") or ""),
                "memory": str(record.get("memory") or ""),
                "source_uri": str(metadata.get("source_uri") or ""),
                "confidence": metadata.get("confidence"),
            }
        )
    return pack


def run_self_test() -> None:
    metadata = {
        "tenant_id": "org_mil",
        "workspace_id": "engineering",
        "repo": "MIL",
        "repo_id": "github:namlogan/MIL",
        "user_id": "repo:github:namlogan/MIL",
        "agent_id": "codex",
        "run_id": "windmill-job-123",
        "source_uri": "https://github.com/namlogan/MIL/pull/26",
        "confidence": 0.82,
        "status": "active",
        "visibility": "repo",
        "created_by": "agent",
        "github": "ghp_123456789012345678901234567890123456",
    }
    record = build_memory_record(
        project=DEFAULT_PROJECT,
        task_id="MEM-SELF-TEST",
        memory_type="plan",
        text=(
            "Use mem0 for project memory. accessToken: "
            "13f6f4f5c84c0ce8ec2b780595dcb28ca2019c2f36f313ac8146497702999318"
        ),
        metadata=metadata,
    )
    filters = build_search_filters(
        tenant_id="org_mil",
        repo_id="github:namlogan/MIL",
        memory_types=["plan"],
        user_id="repo:github:namlogan/MIL",
    )
    results = search_records([record], "project memory", filters=filters)
    serialized = json.dumps(results[0], sort_keys=True)
    assert "13f6f4f5c84c0ce8ec2b780595dcb28ca2019c2f36f313ac8146497702999318" not in serialized
    assert "ghp_123456789012345678901234567890123456" not in serialized
    assert "[REDACTED_SECRET]" in serialized
    assert "[REDACTED_GITHUB_TOKEN]" in serialized


def main(request: dict[str, Any] | None = None) -> dict[str, Any]:
    if request and request.get("self_test"):
        run_self_test()
    return {
        "decision": "MEMORY_CONTRACT_READY",
        "allowed_memory_types": sorted(ALLOWED_MEMORY_TYPES),
        "approval_required_memory_types": sorted(APPROVAL_REQUIRED_MEMORY_TYPES),
        "required_metadata_fields": list(REQUIRED_METADATA_FIELDS),
        "entity_scope_fields": list(ENTITY_SCOPE_FIELDS),
    }
