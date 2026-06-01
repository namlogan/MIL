#!/usr/bin/env python3
"""Create a portable, non-secret MIL agent-factory backup."""

from __future__ import annotations

import argparse
import fnmatch
import json
import subprocess
import tarfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DEFAULT_PROJECT_ID = "MIL"
DEFAULT_ARCHIVE_PREFIX = "MIL-agent-factory"
EXCLUDE_PATTERNS = (
    ".git/**",
    ".env",
    ".env.*",
    ".windmill/runtime/**",
    ".ai-factory/queue/**",
    ".ai-factory/tmp/**",
    ".ai-factory/memory/*.jsonl",
    ".ai-factory/memory/*.db",
    "**/__pycache__/**",
    "**/*.pyc",
    "node_modules/**",
    "dist/**",
)


def _run(command: list[str], *, cwd: str | Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=str(cwd),
        text=True,
        capture_output=True,
        check=False,
    )


def _git_output(command: list[str], repo_root: str | Path) -> str:
    completed = _run(command, cwd=repo_root)
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr.strip() or f"command failed: {' '.join(command)}")
    return completed.stdout


def _matches_any(path: str, patterns: tuple[str, ...] = EXCLUDE_PATTERNS) -> bool:
    normalized = path.strip().lstrip("./")
    return any(fnmatch.fnmatch(normalized, pattern) for pattern in patterns)


def select_backup_files(repo_root: str | Path) -> list[str]:
    """Return tracked files that are safe to include in the portable snapshot."""

    output = _git_output(["git", "ls-files", "-z"], repo_root)
    files = [item for item in output.split("\0") if item]
    selected = [
        path
        for path in files
        if not _matches_any(path) and (Path(repo_root) / path).is_file()
    ]
    return sorted(selected)


def _head_sha(repo_root: str | Path) -> str:
    return _git_output(["git", "rev-parse", "HEAD"], repo_root).strip()


def _remote_url(repo_root: str | Path) -> str:
    completed = _run(["git", "remote", "get-url", "origin"], cwd=repo_root)
    return completed.stdout.strip() if completed.returncode == 0 else ""


def _write_tarball(
    *,
    repo_root: Path,
    archive_path: Path,
    root_name: str,
    files: list[str],
) -> None:
    with tarfile.open(archive_path, "w:gz") as archive:
        for relative_path in files:
            archive.add(
                repo_root / relative_path,
                arcname=str(Path(root_name) / relative_path),
                recursive=False,
            )


def _write_git_bundle(repo_root: Path, bundle_path: Path) -> None:
    completed = _run(["git", "bundle", "create", str(bundle_path), "--all"], cwd=repo_root)
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr.strip() or "git bundle create failed")


def _manifest(
    *,
    project_id: str,
    root_name: str,
    repo_root: Path,
    files: list[str],
    archive_path: Path,
    bundle_path: Path,
) -> dict[str, Any]:
    return {
        "schema_version": "1.0",
        "project_id": project_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "source_repo": str(repo_root),
        "remote_url": _remote_url(repo_root),
        "head_sha": _head_sha(repo_root),
        "archive_root": root_name,
        "archive_path": str(archive_path),
        "bundle_path": str(bundle_path),
        "file_count": len(files),
        "files": files,
        "excluded_patterns": list(EXCLUDE_PATTERNS),
        "required_external_secrets": [
            "Windmill f/mil/github_webhook_secret",
            "Windmill f/mil/github_status_token",
            "ngrok or Cloudflare tunnel credential",
            "Augment/Auggie local credentials",
            "Codex/OpenAI local credentials",
            "Mem0 credential if Mem0 is enabled",
        ],
        "restore_entrypoints": [
            "docs/agent-factory-workflow-and-starter.md",
            "docs/portable-agent-factory-runbook.md",
            "docs/windmill-setup.md",
            "docs/augment-setup.md",
        ],
        "post_restore_checks": [
            "python3 -m unittest discover -s tests -v",
            "python3 -m compileall -q scripts tests f",
            "python3 scripts/ai-factory/bootstrap_runtime.py --check",
            "python3 scripts/windmill/validate_windmill_project.py --self-test",
            "python3 scripts/agent-gate/validate_ai_factory.py --self-test",
        ],
        "notes": [
            "This backup intentionally excludes runtime artifacts and secret values.",
            "Restore secrets from a password manager or vault, not from this manifest.",
            "Rename project IDs, Windmill paths, webhook route, and MCP server names for each new project.",
        ],
    }


def create_backup(
    *,
    repo_root: str | Path,
    output_dir: str | Path,
    project_id: str = DEFAULT_PROJECT_ID,
    archive_prefix: str = DEFAULT_ARCHIVE_PREFIX,
) -> dict[str, Any]:
    repo = Path(repo_root).resolve()
    out = Path(output_dir).expanduser().resolve()
    out.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    root_name = f"{archive_prefix}-{timestamp}"
    archive_path = out / f"{root_name}.tar.gz"
    bundle_path = out / f"{root_name}.bundle"
    manifest_path = out / f"{root_name}.manifest.json"

    files = select_backup_files(repo)
    _write_tarball(
        repo_root=repo,
        archive_path=archive_path,
        root_name=root_name,
        files=files,
    )
    _write_git_bundle(repo, bundle_path)
    manifest = _manifest(
        project_id=project_id,
        root_name=root_name,
        repo_root=repo,
        files=files,
        archive_path=archive_path,
        bundle_path=bundle_path,
    )
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    return {
        "ok": True,
        "project_id": project_id,
        "archive_path": str(archive_path),
        "bundle_path": str(bundle_path),
        "manifest_path": str(manifest_path),
        "file_count": len(files),
        "head_sha": manifest["head_sha"],
    }


def run_self_test() -> None:
    repo = Path(__file__).resolve().parents[2]
    files = select_backup_files(repo)
    assert "AGENTS.md" in files
    assert "f/mil/github_webhook_router.py" in files
    assert not any(path.startswith(".ai-factory/queue/") for path in files)
    assert not any("__pycache__" in path for path in files)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", default=str(Path(__file__).resolve().parents[2]))
    parser.add_argument(
        "--output-dir",
        default=str(Path.home() / "Backups" / DEFAULT_PROJECT_ID),
    )
    parser.add_argument("--project-id", default=DEFAULT_PROJECT_ID)
    parser.add_argument("--archive-prefix", default=DEFAULT_ARCHIVE_PREFIX)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args(argv)

    if args.self_test:
        run_self_test()
        print("create_agent_factory_backup self-test passed")
        return 0

    result = create_backup(
        repo_root=args.repo,
        output_dir=args.output_dir,
        project_id=args.project_id,
        archive_prefix=args.archive_prefix,
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
