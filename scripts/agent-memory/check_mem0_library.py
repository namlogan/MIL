#!/usr/bin/env python3
"""Check Mem0 OSS library mode for development."""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
from pathlib import Path
from typing import Callable, Mapping


PYTHON_INSTALL_COMMAND = "pip install mem0ai"
NODE_INSTALL_COMMAND = "npm install mem0ai"
PYTHON_DEFAULT_STORE = {
    "history": "~/.mem0/history.db",
    "vector": "/tmp/qdrant",
}
NODE_DEFAULT_STORE = {
    "history": "{mem0_dir}/history.db",
    "vector": "memory",
}

ModuleAvailable = Callable[[str], bool]


def _python_module_available(module: str) -> bool:
    return importlib.util.find_spec(module) is not None


def _read_package_json(repo_root: Path) -> dict[str, object]:
    package_json = repo_root / "package.json"
    if not package_json.exists():
        return {}
    data = json.loads(package_json.read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else {}


def _node_package_configured(repo_root: Path, package: str = "mem0ai") -> bool:
    data = _read_package_json(repo_root)
    for field in ("dependencies", "devDependencies", "optionalDependencies"):
        deps = data.get(field, {})
        if isinstance(deps, dict) and package in deps:
            return True
    return (repo_root / "node_modules" / package).exists()


def _llm_provider(env: Mapping[str, str]) -> str:
    if env.get("OPENAI_API_KEY"):
        return "openai"
    if env.get("OLLAMA_HOST") or env.get("OLLAMA_BASE_URL") or env.get("MEM0_LLM_PROVIDER") == "ollama":
        return "ollama"
    return ""


def check_library(
    *,
    runtime: str = "auto",
    repo_root: str | Path | None = None,
    env: Mapping[str, str] | None = None,
    python_module_available: ModuleAvailable = _python_module_available,
    require_llm: bool = False,
) -> dict[str, object]:
    values = dict(os.environ if env is None else env)
    root = Path(repo_root or Path.cwd()).resolve()
    selected_runtime = runtime.strip().lower()
    if selected_runtime == "auto":
        selected_runtime = "node" if _node_package_configured(root) else "python"

    errors: list[str] = []
    warnings: list[str] = []
    provider = _llm_provider(values)
    if not provider:
        message = (
            "No external LLM provider is configured; this is OK for MIL internal "
            "deterministic memory smoke, but real Mem0 Memory() extraction/search "
            "needs an explicit provider."
        )
        warnings.append(message)
        if require_llm:
            errors.append(
                "OPENAI_API_KEY, OLLAMA_HOST, or another explicit Mem0 LLM provider is required."
            )

    if selected_runtime == "python":
        package_available = python_module_available("mem0")
        if not package_available:
            errors.append("Python package mem0ai is not installed.")
        return {
            "ok": not errors,
            "runtime": "python",
            "package": "mem0ai",
            "module": "mem0",
            "package_available": package_available,
            "llm_provider": provider,
            "store": PYTHON_DEFAULT_STORE,
            "install_command": PYTHON_INSTALL_COMMAND,
            "smoke_import": "python3 -c 'from mem0 import Memory; print(\"MEM0_LIBRARY_OK\")'",
            "errors": errors,
            "warnings": warnings,
        }

    if selected_runtime == "node":
        package_available = _node_package_configured(root)
        if not package_available:
            errors.append("Node package mem0ai is not installed or listed in package.json.")
        return {
            "ok": not errors,
            "runtime": "node",
            "package": "mem0ai",
            "package_available": package_available,
            "llm_provider": provider,
            "store": NODE_DEFAULT_STORE,
            "install_command": NODE_INSTALL_COMMAND,
            "smoke_import": "node -e 'import(\"mem0ai/oss\").then(() => console.log(\"MEM0_LIBRARY_OK\"))'",
            "errors": errors,
            "warnings": warnings,
        }

    return {
        "ok": False,
        "runtime": selected_runtime,
        "errors": ["runtime must be one of auto, python, or node"],
        "warnings": warnings,
    }


def run_self_test() -> None:
    python_result = check_library(
        runtime="python",
        env={"OPENAI_API_KEY": "secret"},
        python_module_available=lambda module: module == "mem0",
    )
    assert python_result["ok"] is True, python_result
    assert "secret" not in json.dumps(python_result)
    missing = check_library(
        runtime="python",
        env={"OPENAI_API_KEY": "secret"},
        python_module_available=lambda module: False,
    )
    assert missing["ok"] is False, missing


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runtime", choices=["auto", "python", "node"], default="auto")
    parser.add_argument("--repo", default=str(Path(__file__).resolve().parents[2]))
    parser.add_argument(
        "--require-llm",
        action="store_true",
        help="Fail if no explicit LLM/embedder provider is configured for real Mem0 Memory() calls.",
    )
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args(argv)

    if args.self_test:
        run_self_test()
        print("check_mem0_library self-test passed")
        return 0

    result = check_library(runtime=args.runtime, repo_root=args.repo, require_llm=args.require_llm)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
