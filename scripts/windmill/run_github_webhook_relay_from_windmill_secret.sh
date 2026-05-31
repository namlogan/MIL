#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

WMILL_WORKSPACE="${WMILL_WORKSPACE:-mil-local}"
SECRET_PATH="${MIL_GITHUB_WEBHOOK_SECRET_PATH:-f/mil/github_webhook_secret}"

secret_json="$(wmill --workspace "${WMILL_WORKSPACE}" variable get "${SECRET_PATH}" --json)"
secret="$(
  printf '%s' "${secret_json}" | python3 -c '
import json
import sys

value = json.load(sys.stdin).get("value", "")
if value:
    print(value)
'
)"

if [[ -z "${secret}" ]]; then
  echo "Windmill secret ${SECRET_PATH} is missing or empty" >&2
  exit 1
fi

export MIL_GITHUB_WEBHOOK_SECRET="${secret}"
args=(
  python3 "${REPO_ROOT}/scripts/windmill/github_webhook_public_relay.py"
  --host "${MIL_WEBHOOK_RELAY_HOST:-127.0.0.1}" \
  --port "${MIL_WEBHOOK_RELAY_PORT:-18090}" \
  --public-route "${MIL_WEBHOOK_PUBLIC_ROUTE:-/mil/github-webhook}" \
  --windmill-url "${MIL_WINDMILL_WEBHOOK_URL:-http://localhost:8090/api/r/admins/mil/github-webhook}"
)

if [[ "${MIL_AUTO_DISPATCH_ENABLED:-0}" =~ ^(1|true|TRUE|yes|YES|on|ON)$ ]]; then
  args+=(--auto-dispatch)
fi
args+=(--auto-dispatch-repo "${MIL_AUTO_DISPATCH_REPO:-${REPO_ROOT}}")
args+=(--auto-dispatch-queue "${MIL_AUTO_DISPATCH_QUEUE:-.ai-factory/queue/webhooks}")

exec "${args[@]}"
