#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

if [[ -f "${REPO_ROOT}/.env.local" ]]; then
  set -a
  # shellcheck disable=SC1091
  source "${REPO_ROOT}/.env.local"
  set +a
fi

: "${AUGMENT_SESSION_AUTH:?AUGMENT_SESSION_AUTH must be configured in the environment or .env.local}"

exec auggie \
  --workspace-root "${REPO_ROOT}" \
  --rules "${REPO_ROOT}/AGENTS.md" \
  --allow-indexing \
  "$@"
