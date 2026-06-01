#!/usr/bin/env python3
"""CLI wrapper for the MIL scoped memory contract."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from f.mil.memory_contract import (
    ALLOWED_MEMORY_TYPES,
    DEFAULT_PROJECT,
    DEFAULT_STORE_PATH,
    ENTITY_SCOPE_FIELDS,
    LocalJsonlMemoryStore,
    build_mem0_add_payload,
    build_mem0_search_payload,
    build_memory_record,
    build_search_filters,
    run_self_test,
)


def _parse_metadata(values: list[str]) -> dict[str, Any]:
    metadata: dict[str, Any] = {}
    for value in values:
        if "=" not in value:
            raise ValueError(f"metadata must use key=value format: {value}")
        key, raw = value.split("=", 1)
        if key == "confidence":
            metadata[key] = float(raw)
        else:
            metadata[key] = raw
    return metadata


def _memory_types(raw_values: list[str]) -> list[str]:
    memory_types: list[str] = []
    for raw_value in raw_values:
        memory_types.extend(item.strip() for item in raw_value.split(",") if item.strip())
    return memory_types


def _filter_args(args: argparse.Namespace) -> dict[str, Any]:
    scope = {field: getattr(args, field, None) for field in ENTITY_SCOPE_FIELDS}
    return build_search_filters(
        tenant_id=args.tenant_id,
        repo_id=args.repo_id,
        memory_types=_memory_types(args.memory_type),
        status=args.status,
        visibility=args.visibility,
        workspace_id=args.workspace_id,
        project_id=args.project_id,
        framework_id=args.framework_id,
        scope=args.scope,
        sensitivity=args.sensitivity,
        branch=args.branch,
        **scope,
    )


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
    add_parser.add_argument("--approved", action="store_true", help="Allow approval-required memory types.")
    add_parser.add_argument("--emit-mem0-payload", action="store_true")

    search_parser = subparsers.add_parser("search", help="Search local memory records.")
    search_parser.add_argument("--query", required=True)
    search_parser.add_argument("--tenant-id", required=True)
    search_parser.add_argument("--workspace-id")
    search_parser.add_argument("--repo-id", required=True)
    search_parser.add_argument("--project-id", default="mil")
    search_parser.add_argument("--framework-id")
    search_parser.add_argument("--scope")
    search_parser.add_argument("--memory-type", action="append", required=True)
    search_parser.add_argument("--status", default="approved")
    search_parser.add_argument("--visibility", default="repo")
    search_parser.add_argument("--sensitivity", default="internal")
    search_parser.add_argument("--branch")
    search_parser.add_argument("--user-id")
    search_parser.add_argument("--agent-id")
    search_parser.add_argument("--app-id")
    search_parser.add_argument("--run-id")
    search_parser.add_argument("--limit", type=int, default=5)
    search_parser.add_argument("--emit-mem0-payload", action="store_true")

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
                approved=args.approved,
            )
            response: dict[str, Any] = {"record": store.add(record)}
            if args.emit_mem0_payload:
                response["mem0_add_payload"] = build_mem0_add_payload(record)
            print(json.dumps(response, indent=2, sort_keys=True))
            return 0
        if args.command == "search":
            filters = _filter_args(args)
            results = store.search(args.query, filters=filters, limit=args.limit)
            response = {"filters": filters, "results": results}
            if args.emit_mem0_payload:
                response["mem0_search_payload"] = build_mem0_search_payload(
                    args.query,
                    filters=filters,
                    limit=args.limit,
                )
            print(json.dumps(response, indent=2, sort_keys=True))
            return 0
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    parser.error("command is required unless --self-test is used")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
