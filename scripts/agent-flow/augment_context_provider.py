#!/usr/bin/env python3
"""Preload Augment codebase context for MIL worker dispatch."""

from __future__ import annotations

import argparse
import json
import select
import subprocess
import sys
import time
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from f.mil.codex_worker_contract import redact_secrets
from f.mil.plan_to_pr_contract import AUGMENT_MCP_SERVER, AUGMENT_MCP_TOOL, MAX_CONTEXT_TEXT


WRAPPER_RELATIVE_PATH = "scripts/agent-flow/auggie_mcp_server.sh"
DEFAULT_TIMEOUT_SECONDS = 45
TOOL_RESPONSE_ID = 3


def _json_lines(output: str) -> list[dict[str, Any]]:
    values: list[dict[str, Any]] = []
    for line in output.splitlines():
        stripped = line.strip()
        if not stripped.startswith("{"):
            continue
        try:
            value = json.loads(stripped)
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            values.append(value)
    return values


def _content_text(result: dict[str, Any]) -> str:
    content = result.get("content")
    if not isinstance(content, list):
        return ""

    parts: list[str] = []
    for item in content:
        if not isinstance(item, dict):
            continue
        if item.get("type") == "text" and item.get("text"):
            parts.append(str(item["text"]))
    return "\n\n".join(parts).strip()


def parse_tool_call_result(
    stdout: str,
    *,
    response_id: int = TOOL_RESPONSE_ID,
    source_uri: str,
) -> dict[str, Any]:
    response = next((item for item in _json_lines(stdout) if item.get("id") == response_id), None)
    if response is None:
        return {
            "ok": False,
            "context_pack": [],
            "reasons": [f"missing Augment MCP tools/call response id={response_id}"],
        }

    if response.get("error"):
        return {
            "ok": False,
            "context_pack": [],
            "reasons": [redact_secrets(response["error"])[:MAX_CONTEXT_TEXT]],
        }

    result = response.get("result")
    if not isinstance(result, dict):
        return {
            "ok": False,
            "context_pack": [],
            "reasons": ["Augment MCP tools/call response missing result object"],
        }

    summary = redact_secrets(_content_text(result))[:MAX_CONTEXT_TEXT]
    if not summary:
        return {
            "ok": False,
            "context_pack": [],
            "reasons": ["Augment MCP returned no text content"],
        }

    return {
        "ok": True,
        "context_pack": [
            {
                "memory_id": "augment-codebase-retrieval-1",
                "source_uri": source_uri,
                "summary": summary,
            }
        ],
        "reasons": [],
    }


def _mcp_messages(query: str, repo_root: Path) -> list[dict[str, Any]]:
    return [
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "mil-augment-context-provider", "version": "1.0"},
            },
        },
        {"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}},
        {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}},
        {
            "jsonrpc": "2.0",
            "id": TOOL_RESPONSE_ID,
            "method": "tools/call",
            "params": {
                "name": AUGMENT_MCP_TOOL,
                "arguments": {
                    "information_request": query,
                    "directory_path": str(repo_root.resolve()),
                },
            },
        },
    ]


def retrieve_context_pack(
    *,
    query: str,
    repo_root: str | Path,
    wrapper_path: str | Path | None = None,
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
) -> dict[str, Any]:
    repo = Path(repo_root).resolve()
    wrapper = Path(wrapper_path).resolve() if wrapper_path else repo / WRAPPER_RELATIVE_PATH
    source_uri = f"augment://mcp/{AUGMENT_MCP_SERVER}/{AUGMENT_MCP_TOOL}/result"

    if not wrapper.exists():
        return {
            "ok": False,
            "context_pack": [],
            "reasons": [f"Augment MCP wrapper not found: {wrapper}"],
            "source_uri": source_uri,
        }

    process = subprocess.Popen(
        [str(wrapper)],
        cwd=repo,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
    )

    assert process.stdin is not None
    assert process.stdout is not None
    assert process.stderr is not None

    for message in _mcp_messages(query, repo):
        process.stdin.write(json.dumps(message) + "\n")
        process.stdin.flush()

    stdout_lines: list[str] = []
    stderr_lines: list[str] = []
    start = time.monotonic()
    got_tool_response = False
    timed_out = False

    while time.monotonic() - start < timeout_seconds:
        readable, _, _ = select.select([process.stdout, process.stderr], [], [], 0.5)
        for stream in readable:
            line = stream.readline()
            if not line:
                continue
            if stream is process.stdout:
                stdout_lines.append(line.rstrip("\n"))
                try:
                    item = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if item.get("id") == TOOL_RESPONSE_ID:
                    got_tool_response = True
            else:
                stderr_lines.append(line.rstrip("\n"))
        if got_tool_response:
            break
        if process.poll() is not None and not readable:
            break
    else:
        timed_out = True

    if process.poll() is None:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()

    parsed = parse_tool_call_result(
        "\n".join(stdout_lines),
        response_id=TOOL_RESPONSE_ID,
        source_uri=source_uri,
    )
    parsed["source_uri"] = source_uri
    parsed["timed_out"] = timed_out
    parsed["workspace_indexed"] = f"Workspace indexing complete: {repo}" in "\n".join(stderr_lines)
    if timed_out and parsed["ok"] is False:
        parsed["reasons"] = ["Augment MCP codebase-retrieval timed out"]
    return parsed


def run_self_test() -> None:
    stdout = json.dumps(
        {
            "result": {
                "content": [
                    {
                        "type": "text",
                        "text": "Path: scripts/agent-flow/auto_dispatcher.py\nContext.",
                    }
                ]
            },
            "id": TOOL_RESPONSE_ID,
        }
    )
    result = parse_tool_call_result(
        stdout,
        response_id=TOOL_RESPONSE_ID,
        source_uri=f"augment://mcp/{AUGMENT_MCP_SERVER}/{AUGMENT_MCP_TOOL}/result",
    )
    assert result["ok"] is True
    assert result["context_pack"]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", default=str(REPO_ROOT))
    parser.add_argument("--query", help="Natural-language Augment retrieval query.")
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT_SECONDS)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args(argv)

    if args.self_test:
        run_self_test()
        print("augment_context_provider self-test passed")
        return 0

    if not args.query:
        parser.error("--query is required unless --self-test is used")

    result = retrieve_context_pack(
        query=args.query,
        repo_root=args.repo,
        timeout_seconds=args.timeout,
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
