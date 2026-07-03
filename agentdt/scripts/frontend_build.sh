#!/bin/bash
set -euo pipefail

cd "$(dirname "$0")/.."

BUNDLED_NODE="${HOME}/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node"

if [ -x "${BUNDLED_NODE}" ]; then
  NODE_BIN="${BUNDLED_NODE}"
elif command -v node >/dev/null 2>&1; then
  NODE_BIN="$(command -v node)"
else
  echo "❌ Node.js runtime not found."
  exit 1
fi

if [ ! -d "node_modules" ]; then
  echo "❌ node_modules is missing. Install frontend dependencies first."
  exit 1
fi

exec "${NODE_BIN}" node_modules/vite/bin/vite.js build --config vite.config.mjs "$@"
