#!/usr/bin/env python3
"""MIL memory-layer contract.

This module gives the AI Factory a deterministic local memory adapter for
tests and dry-runs. The production provider may be Mem0 Platform or a
self-hosted Mem0 stack, but the safety contract is the same: sanitize before
write, scope every memory, and never let retrieved memory approve a merge.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


DEFAULT_PROJECT = "MIL"
DEFAULT_STORE_PATH = Path(".ai-factory/memory/local_memory.jsonl")
ALLOWED_MEMORY_TYPES = {
    "plan",
    "developer_handoff",
    "qa_gate",
    "merge_gate",
    "ci_pattern",
    "review_note",
    "operator_note",
}

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
    """Redact common token shapes before storing agent memory."""

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


def build_memory_record(
    *,
    project: str,
    task_id: str,
    memory_type: str,
    text: str,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    project = project.strip()
    task_id = task_id.strip()
    memory_type = memory_type.strip()
    if not project:
        raise ValueError("project is required")
    if not task_id:
        raise ValueError("task_id is required")
    if memory_type not in ALLOWED_MEMORY_TYPES:
        raise ValueError(f"unsupported memory_type: {memory_type}")

    sanitized_text = sanitize_text(text).strip()
    if not sanitized_text:
        raise ValueError("text is required")

    record_metadata = sanitize_value(metadata or {})
    if not isinstance(record_metadata, dict):
        raise ValueError("metadata must be a JSON object")
    record_metadata.setdefault("source", "mil-ai-factory")

    return {
        "version": 1,
        "project": project,
        "task_id": task_id,
        "memory_type": memory_type,
        "memory": sanitized_text,
        "metadata": record_metadata,
        "created_at": _utc_now(),
        "sanitized": True,
    }


def _tokens(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9_:-]+", text.lower()))


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
        project: str | None = DEFAULT_PROJECT,
        task_id: str | None = None,
        limit: int = 5,
    ) -> list[dict[str, Any]]:
        query_tokens = _tokens(query)
        scored: list[tuple[int, str, dict[str, Any]]] = []
        for record in self.iter_records():
            if project and record.get("project") != project:
                continue
            if task_id and record.get("task_id") != task_id:
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


def _parse_metadata(values: list[str]) -> dict[str, Any]:
    metadata: dict[str, Any] = {}
    for value in values:
        if "=" not in value:
            raise ValueError(f"metadata must use key=value format: {value}")
        key, raw = value.split("=", 1)
        metadata[key] = raw
    return metadata


def run_self_test() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        store = LocalJsonlMemoryStore(Path(tmpdir) / "memory.jsonl")
        record = build_memory_record(
            project=DEFAULT_PROJECT,
            task_id="MEM-SELF-TEST",
            memory_type="plan",
            text=(
                "Use mem0 for project memory. accessToken: "
                "13f6f4f5c84c0ce8ec2b780595dcb28ca2019c2f36f313ac8146497702999318"
            ),
            metadata={"github": "ghp_123456789012345678901234567890123456"},
        )
        store.add(record)
        stored = store.search("project memory", project=DEFAULT_PROJECT)
        assert len(stored) == 1
        serialized = json.dumps(stored[0], sort_keys=True)
        assert "13f6f4f5c84c0ce8ec2b780595dcb28ca2019c2f36f313ac8146497702999318" not in serialized
        assert "ghp_123456789012345678901234567890123456" not in serialized
        assert "[REDACTED_SECRET]" in serialized
        assert "[REDACTED_GITHUB_TOKEN]" in serialized


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--store", default=str(DEFAULT_STORE_PATH), help="JSONL memory store path.")
    parser.add_argument("--self-test", action="store_true", help="Run built-in safety tests.")

    subparsers = parser.add_subparsers(dest="command")
    add_parser = subparsers.add_parser("add", help="Add a sanitized memory record.")
    add_parser.add_argument("--project", default=DEFAULT_PROJECT)
    add_parser.add_argument("--task-id", required=True)
    add_parser.add_argument("--memory-type", required=True, choices=sorted(ALLOWED_MEMORY_TYPES))
    add_parser.add_argument("--text", required=True)
    add_parser.add_argument("--metadata", action="append", default=[], help="key=value metadata.")

    search_parser = subparsers.add_parser("search", help="Search local memory records.")
    search_parser.add_argument("--query", required=True)
    search_parser.add_argument("--project", default=DEFAULT_PROJECT)
    search_parser.add_argument("--task-id")
    search_parser.add_argument("--limit", type=int, default=5)

    args = parser.parse_args(argv)
    if args.self_test:
        run_self_test()
        print("memory_contract self-test passed")
        return 0

    store = LocalJsonlMemoryStore(Path(args.store))
    try:
        if args.command == "add":
            record = build_memory_record(
                project=args.project,
                task_id=args.task_id,
                memory_type=args.memory_type,
                text=args.text,
                metadata=_parse_metadata(args.metadata),
            )
            print(json.dumps(store.add(record), indent=2, sort_keys=True))
            return 0
        if args.command == "search":
            results = store.search(
                args.query,
                project=args.project,
                task_id=args.task_id,
                limit=args.limit,
            )
            print(json.dumps({"results": results}, indent=2, sort_keys=True))
            return 0
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    parser.error("command is required unless --self-test is used")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
