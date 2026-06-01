"""MIL Memory0 gateway contract for local and Windmill execution.

Memory0/Mem0 is a controlled memory layer for SDLC continuity. It is not a
source of truth and agents must not write approved memories directly.
"""

from __future__ import annotations

import json
import re
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


DEFAULT_PROJECT = "MIL"
DEFAULT_PROJECT_ID = "mil"
DEFAULT_FRAMEWORK_ID = "ai-factory-sdlc"
DEFAULT_STORE_PATH = Path(".ai-factory/memory/local_memory.jsonl")
DEFAULT_AUDIT_PATH = Path(".ai-factory/memory/audit.jsonl")

ALLOWED_MEMORY_TYPES = {
    "framework_rule",
    "security_rule",
    "product_rule",
    "architecture_decision",
    "adr_summary",
    "domain_glossary",
    "requirement_interpretation",
    "implementation_lesson",
    "test_lesson",
    "review_lesson",
    "deployment_runbook",
    "incident_postmortem",
    "agent_handoff",
    "open_question",
    "deprecated_decision",
}
APPROVAL_REQUIRED_MEMORY_TYPES = {
    "framework_rule",
    "security_rule",
    "product_rule",
    "architecture_decision",
    "adr_summary",
    "requirement_interpretation",
    "deployment_runbook",
    "incident_postmortem",
    "deprecated_decision",
}
AUTO_CANDIDATE_MEMORY_TYPES = ALLOWED_MEMORY_TYPES - APPROVAL_REQUIRED_MEMORY_TYPES

ALLOWED_SCOPES = {"framework", "project", "task"}
ALLOWED_STATUSES = {"candidate", "reviewed", "approved", "superseded", "retired", "needs_review"}
RETRIEVABLE_STATUSES = {"approved"}
ALLOWED_SENSITIVITIES = {"public", "internal", "confidential"}
ALLOWED_CONFIDENCE = {"low", "medium", "high"}
ALLOWED_SOURCE_TYPES = {
    "pull_request",
    "issue",
    "commit",
    "docs",
    "adr",
    "test",
    "ci_run",
    "windmill_run",
    "release",
    "incident",
}
ALLOWED_VISIBILITIES = {"repo", "workspace", "tenant", "private"}
ENTITY_SCOPE_FIELDS = ("user_id", "agent_id", "app_id", "run_id")
REQUIRED_EVENT_FIELDS = (
    "memory_type",
    "scope",
    "status",
    "source_ref",
    "content",
    "sensitivity",
)
REQUIRED_METADATA_FIELDS = (
    "tenant_id",
    "workspace_id",
    "repo",
    "repo_id",
    "source_ref",
    "confidence",
    "status",
    "sensitivity",
    "created_by",
)

SOURCE_OF_TRUTH_PRIORITY = [
    "compliance_legal_security",
    "current_prd_spec_sop_contract",
    "git_code_and_tests",
    "approved_adr",
    "approved_memory",
    "candidate_memory",
    "conversation_context",
]

SECRET_PATTERNS = [
    re.compile(r"github_pat_[A-Za-z0-9_]{20,}"),
    re.compile(r"(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9_]{20,}"),
    re.compile(r"sk-[A-Za-z0-9_-]{20,}"),
    re.compile(r"(?i)bearer\s+[A-Za-z0-9._-]{20,}"),
    re.compile(
        r"(?i)\b(accessToken|authtoken|api[_-]?key|token|secret|password)"
        r"(\s*[:=]\s*)[\"']?[A-Za-z0-9._:/+=-]{12,}[\"']?"
    ),
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
]
RESTRICTED_PAYLOAD_PATTERNS = [
    *SECRET_PATTERNS,
    re.compile(r"(?im)^\s*[A-Z0-9_]*(SECRET|TOKEN|PASSWORD|API_KEY)\s*="),
    re.compile(r"(?i)\bchain[- ]of[- ]thought\b"),
    re.compile(r"(?i)\braw customer data\b"),
    re.compile(r"(?i)\bdatabase dump\b"),
    re.compile(r"(?i)\bmodel weights?\b"),
    re.compile(r"(?i)\braw factory (image|video)\b"),
]


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _memory_id() -> str:
    return f"mem_{uuid.uuid4().hex[:16]}"


def _required_text(value: Any, label: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise ValueError(f"{label} is required")
    return text


def _canonical_confidence(value: Any) -> str:
    if isinstance(value, (int, float)):
        number = float(value)
        if number >= 0.75:
            return "high"
        if number >= 0.45:
            return "medium"
        return "low"
    text = str(value or "").strip().lower()
    if text in ALLOWED_CONFIDENCE:
        return text
    raise ValueError(f"confidence must be one of {sorted(ALLOWED_CONFIDENCE)}")


def sanitize_text(text: str) -> str:
    sanitized = text
    replacements = [
        (SECRET_PATTERNS[0], "[REDACTED_GITHUB_TOKEN]"),
        (SECRET_PATTERNS[1], "[REDACTED_GITHUB_TOKEN]"),
        (SECRET_PATTERNS[2], "[REDACTED_API_KEY]"),
        (SECRET_PATTERNS[3], "Bearer [REDACTED_TOKEN]"),
        (SECRET_PATTERNS[4], r"\1\2[REDACTED_SECRET]"),
        (SECRET_PATTERNS[5], "[REDACTED_PRIVATE_KEY]"),
    ]
    for pattern, replacement in replacements:
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


def _contains_restricted_payload(value: Any) -> bool:
    if isinstance(value, dict):
        return any(_contains_restricted_payload(key) or _contains_restricted_payload(item) for key, item in value.items())
    if isinstance(value, list):
        return any(_contains_restricted_payload(item) for item in value)
    if not isinstance(value, str):
        return False
    return any(pattern.search(value) for pattern in RESTRICTED_PAYLOAD_PATTERNS)


def _reject_restricted_payload(value: Any) -> None:
    if _contains_restricted_payload(value):
        raise ValueError("restricted memory payload is not allowed")


def _entity_scope(metadata: dict[str, Any]) -> dict[str, str]:
    scope = {
        field: str(metadata[field]).strip()
        for field in ENTITY_SCOPE_FIELDS
        if str(metadata.get(field) or "").strip()
    }
    if not scope:
        raise ValueError("at least one Mem0 entity scope is required")
    return scope


def write_policy_for(memory_type: str) -> str:
    memory_type = _required_text(memory_type, "memory_type")
    if memory_type not in ALLOWED_MEMORY_TYPES:
        raise ValueError(f"unsupported memory_type: {memory_type}")
    if memory_type in APPROVAL_REQUIRED_MEMORY_TYPES:
        return "approval_required"
    return "candidate_then_review"


def _normalize_metadata(
    metadata: dict[str, Any],
    *,
    memory_type: str,
    approved: bool,
) -> dict[str, Any]:
    if not isinstance(metadata, dict):
        raise ValueError("metadata must be a JSON object")
    metadata = dict(metadata)
    if "source_ref" not in metadata and metadata.get("source_uri"):
        metadata["source_ref"] = metadata["source_uri"]
    if "source_uri" not in metadata and metadata.get("source_ref"):
        metadata["source_uri"] = metadata["source_ref"]
    metadata.setdefault("scope", "project")
    metadata.setdefault("project_id", DEFAULT_PROJECT_ID)
    metadata.setdefault("framework_id", DEFAULT_FRAMEWORK_ID)
    metadata.setdefault("sensitivity", "internal")
    metadata.setdefault("status", "approved" if approved else "candidate")
    metadata.setdefault("visibility", "repo")
    metadata.setdefault("source_type", "docs")
    metadata.setdefault("valid_until", "until_superseded")
    metadata.setdefault("tags", [])

    for field in REQUIRED_METADATA_FIELDS:
        if not str(metadata.get(field) or "").strip():
            raise ValueError(f"{field} is required" if field == "source_ref" else f"metadata.{field} is required")

    scope = str(metadata["scope"]).strip()
    if scope not in ALLOWED_SCOPES:
        raise ValueError(f"scope must be one of {sorted(ALLOWED_SCOPES)}")
    if scope == "framework" and not str(metadata.get("framework_id") or "").strip():
        raise ValueError("framework_id is required for framework memory")
    if scope in {"project", "task"} and not str(metadata.get("project_id") or "").strip():
        raise ValueError("project_id is required for project/task memory")
    if scope == "task" and not str(metadata.get("task_id") or "").strip():
        raise ValueError("task_id is required for task memory")

    status = str(metadata["status"]).strip()
    if status not in ALLOWED_STATUSES:
        raise ValueError(f"status must be one of {sorted(ALLOWED_STATUSES)}")
    sensitivity = str(metadata["sensitivity"]).strip()
    if sensitivity not in ALLOWED_SENSITIVITIES:
        raise ValueError(f"sensitivity must be one of {sorted(ALLOWED_SENSITIVITIES)}")
    visibility = str(metadata["visibility"]).strip()
    if visibility not in ALLOWED_VISIBILITIES:
        raise ValueError(f"metadata.visibility must be one of {sorted(ALLOWED_VISIBILITIES)}")

    source_type = str(metadata.get("source_type") or "docs").strip()
    if source_type not in ALLOWED_SOURCE_TYPES:
        raise ValueError(f"source_type must be one of {sorted(ALLOWED_SOURCE_TYPES)}")

    metadata["confidence"] = _canonical_confidence(metadata["confidence"])
    metadata["memory_type"] = memory_type
    metadata["status"] = status
    metadata["scope"] = scope
    metadata["sensitivity"] = sensitivity
    metadata["visibility"] = visibility
    metadata["source_type"] = source_type
    metadata.setdefault("source", "mil-memory-gateway")

    if status == "approved" and (
        not approved or not str(metadata.get("approved_by") or "").strip()
    ):
        raise ValueError("approved memory requires approval flag and metadata.approved_by")
    if memory_type in APPROVAL_REQUIRED_MEMORY_TYPES and status == "approved" and not approved:
        raise ValueError(f"memory_type {memory_type} requires approval")

    return metadata


def validate_memory_event(event: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(event, dict):
        raise ValueError("memory event must be a JSON object")
    for field in REQUIRED_EVENT_FIELDS:
        if not str(event.get(field) or "").strip():
            raise ValueError(f"{field} is required")
    write_policy_for(str(event["memory_type"]))
    metadata = {
        "tenant_id": event.get("tenant_id", "org_mil"),
        "workspace_id": event.get("workspace_id", "engineering"),
        "repo": event.get("repo", DEFAULT_PROJECT),
        "repo_id": event.get("repo_id", "github:namlogan/MIL"),
        "project_id": event.get("project_id"),
        "framework_id": event.get("framework_id"),
        "source_ref": event.get("source_ref"),
        "source_type": event.get("source_type", "docs"),
        "confidence": event.get("confidence", "medium"),
        "scope": event.get("scope"),
        "status": event.get("status"),
        "sensitivity": event.get("sensitivity"),
        "visibility": event.get("visibility", "repo"),
        "created_by": event.get("created_by", "memory_gateway"),
        "user_id": event.get("user_id"),
        "agent_id": event.get("agent_id"),
        "app_id": event.get("app_id"),
        "run_id": event.get("run_id"),
        "task_id": event.get("task_id"),
        "approved_by": event.get("approved_by"),
        "tags": event.get("tags", []),
        "valid_until": event.get("valid_until", "until_superseded"),
    }
    _normalize_metadata(
        metadata,
        memory_type=str(event["memory_type"]),
        approved=bool(event.get("approved_by")),
    )
    _entity_scope(metadata)
    _reject_restricted_payload(event)
    normalized = dict(event)
    normalized.setdefault("memory_id", _memory_id())
    normalized.setdefault("created_at", _utc_now())
    return normalized


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
    content = _required_text(text, "text")
    _reject_restricted_payload({"content": content, "metadata": metadata or {}})

    record_metadata = _normalize_metadata(
        dict(metadata or {}),
        memory_type=memory_type,
        approved=approved,
    )
    record_metadata.setdefault("task_id", task_id)
    entity_scope = _entity_scope(record_metadata)

    status = str(record_metadata["status"])
    content = sanitize_text(content).strip()
    memory_id = str(record_metadata.get("memory_id") or _memory_id())
    record = {
        "version": 3,
        "memory_id": memory_id,
        "memory_type": memory_type,
        "scope": record_metadata["scope"],
        "framework_id": record_metadata.get("framework_id"),
        "project_id": record_metadata.get("project_id"),
        "repo": record_metadata["repo"],
        "repo_id": record_metadata["repo_id"],
        "project": project,
        "task_id": task_id,
        "agent_id": record_metadata.get("agent_id"),
        "run_id": record_metadata.get("run_id"),
        "status": status,
        "source_ref": record_metadata["source_ref"],
        "source_type": record_metadata["source_type"],
        "content": content,
        "memory": content,
        "tags": record_metadata.get("tags") if isinstance(record_metadata.get("tags"), list) else [],
        "confidence": record_metadata["confidence"],
        "sensitivity": record_metadata["sensitivity"],
        "valid_until": record_metadata.get("valid_until", "until_superseded"),
        "created_by": record_metadata["created_by"],
        "created_at": _utc_now(),
        "metadata": record_metadata,
        "entity_scope": entity_scope,
        "retention_scope": {
            "tenant_id": record_metadata["tenant_id"],
            "workspace_id": record_metadata["workspace_id"],
            "repo_id": record_metadata["repo_id"],
            "project_id": record_metadata.get("project_id"),
            "framework_id": record_metadata.get("framework_id"),
            "scope": record_metadata["scope"],
            "visibility": record_metadata["visibility"],
            "status": status,
            "sensitivity": record_metadata["sensitivity"],
        },
        "write_policy": policy,
        "sanitized": True,
    }
    validate_memory_event(
        {
            **record,
            "tenant_id": record_metadata["tenant_id"],
            "workspace_id": record_metadata["workspace_id"],
            "visibility": record_metadata["visibility"],
            **entity_scope,
            "approved_by": record_metadata.get("approved_by"),
        }
    )
    return record


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
    status: str = "approved",
    visibility: str = "repo",
    workspace_id: str | None = None,
    project_id: str | None = None,
    framework_id: str | None = None,
    scope: str | None = None,
    sensitivity: str = "internal",
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

    status = str(status or "approved").strip()
    if status not in RETRIEVABLE_STATUSES:
        raise ValueError("memory preflight may retrieve only approved memory")
    sensitivity = str(sensitivity or "internal").strip()
    if sensitivity not in ALLOWED_SENSITIVITIES:
        raise ValueError(f"sensitivity must be one of {sorted(ALLOWED_SENSITIVITIES)}")

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
        {"status": "approved"},
        {"visibility": visibility},
        {"sensitivity": sensitivity},
        _memory_type_conditions(normalized_types),
        _entity_conditions(entity_scope),
        {"NOT": [{"status": "retired"}, {"status": "superseded"}]},
    ]
    if workspace_id:
        filters.insert(1, {"workspace_id": str(workspace_id).strip()})
    if project_id:
        filters.append({"project_id": str(project_id).strip()})
    if framework_id:
        filters.append({"framework_id": str(framework_id).strip()})
    if scope:
        filters.append({"scope": str(scope).strip()})
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
    for required in ["tenant_id", "repo_id", "memory_type", "approved"]:
        if required not in serialized:
            raise ValueError(f"strict filters are required for memory search: missing {required}")
    if not any(field in serialized for field in ENTITY_SCOPE_FIELDS):
        raise ValueError("strict filters are required for memory search: missing entity scope")
    return filters


def _write_records(path: Path, records: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(record, sort_keys=True) + "\n" for record in records),
        encoding="utf-8",
    )


def _audit_payload(action: str, record: dict[str, Any], *, actor: str, source_ref: str) -> dict[str, Any]:
    return {
        "action": action,
        "memory_id": record.get("memory_id"),
        "memory_type": record.get("memory_type"),
        "scope": record.get("scope"),
        "project_id": record.get("project_id"),
        "framework_id": record.get("framework_id"),
        "status": record.get("status"),
        "source_ref": source_ref,
        "actor": actor,
        "created_at": _utc_now(),
    }


def append_audit_event(
    audit_path: Path,
    *,
    action: str,
    record: dict[str, Any],
    actor: str,
    source_ref: str,
) -> dict[str, Any]:
    _reject_restricted_payload({"actor": actor, "source_ref": source_ref})
    event = _audit_payload(action, record, actor=actor, source_ref=source_ref)
    audit_path.parent.mkdir(parents=True, exist_ok=True)
    with audit_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, sort_keys=True) + "\n")
    return event


@dataclass(frozen=True)
class LocalJsonlMemoryStore:
    path: Path

    def add(self, record: dict[str, Any], audit_path: Path | None = None) -> dict[str, Any]:
        validate_memory_event(
            {
                **record,
                "tenant_id": record.get("metadata", {}).get("tenant_id"),
                "workspace_id": record.get("metadata", {}).get("workspace_id"),
                "visibility": record.get("metadata", {}).get("visibility", "repo"),
                **(record.get("entity_scope") if isinstance(record.get("entity_scope"), dict) else {}),
                "approved_by": record.get("metadata", {}).get("approved_by"),
            }
        )
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, sort_keys=True) + "\n")
        if audit_path:
            append_audit_event(
                audit_path,
                action="add",
                record=record,
                actor=str(record.get("created_by") or "memory_gateway"),
                source_ref=str(record.get("source_ref") or ""),
            )
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
        audit_path: Path | None = None,
    ) -> list[dict[str, Any]]:
        results = search_records(self.iter_records(), query, filters=filters, limit=limit)
        if audit_path:
            audit_record = results[0] if results else {"memory_id": "", "memory_type": "", "status": "approved"}
            append_audit_event(
                audit_path,
                action="search",
                record=audit_record,
                actor="memory_gateway",
                source_ref="memory_search",
            )
        return results

    def update_status(
        self,
        memory_id: str,
        status: str,
        *,
        source_ref: str,
        actor: str,
        audit_path: Path | None = None,
    ) -> dict[str, Any]:
        memory_id = _required_text(memory_id, "memory_id")
        status = _required_text(status, "status")
        source_ref = _required_text(source_ref, "source_ref")
        actor = _required_text(actor, "actor")
        if status not in ALLOWED_STATUSES:
            raise ValueError(f"status must be one of {sorted(ALLOWED_STATUSES)}")

        records = list(self.iter_records())
        updated: dict[str, Any] | None = None
        for index, record in enumerate(records):
            if record.get("memory_id") != memory_id:
                continue
            metadata = dict(record.get("metadata") or {})
            metadata["status"] = status
            metadata["last_reviewed_by"] = actor
            metadata["last_status_source_ref"] = source_ref
            if status == "approved":
                metadata["approved_by"] = actor
            record = {
                **record,
                "status": status,
                "metadata": metadata,
                "updated_at": _utc_now(),
            }
            records[index] = record
            updated = record
            break
        if updated is None:
            raise ValueError(f"memory_id not found: {memory_id}")

        _write_records(self.path, records)
        if audit_path:
            action = "supersede" if status == "superseded" else "retire" if status == "retired" else "update"
            append_audit_event(
                audit_path,
                action=action,
                record=updated,
                actor=actor,
                source_ref=source_ref,
            )
        return updated


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
        if str(record.get("status") or record.get("metadata", {}).get("status") or "") != "approved":
            continue

        memory = str(record.get("memory") or record.get("content") or "")
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
            "memory_id": record.get("memory_id"),
            "project": record.get("project"),
            "project_id": record.get("project_id"),
            "framework_id": record.get("framework_id"),
            "task_id": record.get("task_id"),
            "memory_type": record.get("memory_type"),
            "scope": record.get("scope"),
            "status": record.get("status"),
            "source_ref": record.get("source_ref"),
            "sensitivity": record.get("sensitivity"),
        }
    )
    payload: dict[str, Any] = {
        "messages": [{"role": "user", "content": str(record.get("memory") or record.get("content") or "")}],
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


def build_context_pack(records: Iterable[dict[str, Any]], *, top_k: int = 10) -> list[dict[str, Any]]:
    pack: list[dict[str, Any]] = []
    for index, record in enumerate(records, 1):
        if index > top_k:
            break
        metadata = record.get("metadata") if isinstance(record.get("metadata"), dict) else {}
        status = str(record.get("status") or metadata.get("status") or "")
        if status != "approved":
            continue
        pack.append(
            {
                "memory_id": str(record.get("memory_id") or record.get("id") or f"local-{index}"),
                "memory_type": str(record.get("memory_type") or metadata.get("memory_type") or ""),
                "scope": str(record.get("scope") or metadata.get("scope") or ""),
                "content": str(record.get("content") or record.get("memory") or ""),
                "memory": str(record.get("memory") or record.get("content") or ""),
                "source_ref": str(record.get("source_ref") or metadata.get("source_ref") or metadata.get("source_uri") or ""),
                "confidence": record.get("confidence") or metadata.get("confidence"),
                "status": status,
            }
        )
    return pack


def build_memory_conflict_event(
    memory_record: dict[str, Any],
    *,
    source_ref: str,
    reason: str,
) -> dict[str, Any]:
    source_ref = _required_text(source_ref, "source_ref")
    reason = _required_text(reason, "reason")
    _reject_restricted_payload({"source_ref": source_ref, "reason": reason})
    metadata = memory_record.get("metadata") if isinstance(memory_record.get("metadata"), dict) else {}
    content = (
        f"Memory {memory_record.get('memory_id')} conflicts with source-of-truth {source_ref}: "
        f"{reason}"
    )
    event = {
        "memory_id": _memory_id(),
        "memory_type": "deprecated_decision",
        "scope": memory_record.get("scope") or metadata.get("scope") or "project",
        "framework_id": memory_record.get("framework_id") or metadata.get("framework_id") or DEFAULT_FRAMEWORK_ID,
        "project_id": memory_record.get("project_id") or metadata.get("project_id") or DEFAULT_PROJECT_ID,
        "repo": memory_record.get("repo") or metadata.get("repo") or DEFAULT_PROJECT,
        "repo_id": memory_record.get("repo_id") or metadata.get("repo_id") or "github:namlogan/MIL",
        "task_id": memory_record.get("task_id") or metadata.get("task_id") or "",
        "status": "candidate",
        "source_ref": source_ref,
        "source_type": "docs",
        "content": content,
        "memory": content,
        "tags": ["memory_conflict"],
        "confidence": "high",
        "sensitivity": "internal",
        "created_by": "memory_gateway",
        "created_at": _utc_now(),
        "conflicts_with_memory_id": memory_record.get("memory_id"),
        "conflict_policy": SOURCE_OF_TRUTH_PRIORITY,
    }
    return event


def run_self_test() -> None:
    metadata = {
        "tenant_id": "org_mil",
        "workspace_id": "engineering",
        "repo": "MIL",
        "repo_id": "github:namlogan/MIL",
        "project_id": DEFAULT_PROJECT_ID,
        "framework_id": DEFAULT_FRAMEWORK_ID,
        "user_id": "repo:github:namlogan/MIL",
        "agent_id": "codex",
        "run_id": "windmill-job-123",
        "source_ref": "https://github.com/namlogan/MIL/pull/26",
        "source_type": "pull_request",
        "confidence": "high",
        "status": "approved",
        "scope": "project",
        "sensitivity": "internal",
        "visibility": "repo",
        "created_by": "memory_gateway",
        "approved_by": "logan",
    }
    record = build_memory_record(
        project=DEFAULT_PROJECT,
        task_id="MEM-SELF-TEST",
        memory_type="implementation_lesson",
        text="Use Memory0 only as a scoped SDLC learning layer.",
        metadata=metadata,
        approved=True,
    )
    filters = build_search_filters(
        tenant_id="org_mil",
        repo_id="github:namlogan/MIL",
        project_id=DEFAULT_PROJECT_ID,
        memory_types=["implementation_lesson"],
        user_id="repo:github:namlogan/MIL",
    )
    results = search_records([record], "SDLC learning", filters=filters)
    assert results and results[0]["memory_id"] == record["memory_id"]
    try:
        build_memory_record(
            project=DEFAULT_PROJECT,
            task_id="MEM-SELF-TEST",
            memory_type="implementation_lesson",
            text="accessToken: 13f6f4f5c84c0ce8ec2b780595dcb28ca2019c2f36f313ac8146497702999318",
            metadata={**metadata, "status": "candidate"},
        )
    except ValueError as exc:
        assert "restricted memory payload" in str(exc)
    else:
        raise AssertionError("restricted payload was not rejected")


def main(request: dict[str, Any] | None = None) -> dict[str, Any]:
    if request and request.get("self_test"):
        run_self_test()
    return {
        "decision": "MEMORY_GATEWAY_CONTRACT_READY",
        "allowed_memory_types": sorted(ALLOWED_MEMORY_TYPES),
        "approval_required_memory_types": sorted(APPROVAL_REQUIRED_MEMORY_TYPES),
        "required_metadata_fields": list(REQUIRED_METADATA_FIELDS),
        "required_event_fields": list(REQUIRED_EVENT_FIELDS),
        "entity_scope_fields": list(ENTITY_SCOPE_FIELDS),
        "source_of_truth_priority": SOURCE_OF_TRUTH_PRIORITY,
        "retrievable_statuses": sorted(RETRIEVABLE_STATUSES),
    }
