#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "${REPO_ROOT}"

: "${WINDMILL_TOKEN:?WINDMILL_TOKEN is required}"
: "${WINDMILL_WORKSPACE_ID:?WINDMILL_WORKSPACE_ID is required}"
: "${WINDMILL_BASE_URL:?WINDMILL_BASE_URL is required}"

WINDMILL_WORKSPACE_NAME="${WINDMILL_WORKSPACE_NAME:-mil}"
WINDMILL_BRANCH="${WINDMILL_BRANCH:-main}"

python3 scripts/windmill/validate_windmill_project.py --self-test

wmill workspace add \
  "${WINDMILL_WORKSPACE_NAME}" \
  "${WINDMILL_WORKSPACE_ID}" \
  "${WINDMILL_BASE_URL}" \
  --token "${WINDMILL_TOKEN}"

wmill workspace switch "${WINDMILL_WORKSPACE_NAME}"
wmill workspace bind --workspace "${WINDMILL_WORKSPACE_NAME}" --branch "${WINDMILL_BRANCH}"
wmill sync push --dry-run
