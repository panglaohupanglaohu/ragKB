#!/bin/bash
# AgentsGroup2026 — Quick Start Script
set -euo pipefail

cd "$(dirname "$0")"
ROOT_DIR="$(pwd)"
BUNDLED_NODE="${HOME}/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node"
NODE_BIN=""
USE_SYSTEM_NPM=0

echo "🚀 AgentsGroup2026 Starting..."
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 not found. Please install Python 3.11+"
    exit 1
fi

# Check port availability
check_port() {
    if lsof -ti:$1 &>/dev/null; then
        echo "❌ Port $1 is already in use."
        echo "   Stop the process using that port, or change the configured port."
        exit 1
    fi
}
check_port 8080
check_port 5173

# Python bootstrap helpers
PYTHON_CORE_MODULES=(fastapi uvicorn pydantic httpx cryptography)
PYTHON_OPTIONAL_MODULES=(aiohttp pytest pytest_asyncio)

list_missing_modules() {
    local python_bin="$1"
    shift
    "$python_bin" - "$@" <<'PY'
import importlib.util
import sys

mods = sys.argv[1:]
missing = [name for name in mods if importlib.util.find_spec(name) is None]
print(" ".join(missing))
raise SystemExit(0 if not missing else 1)
PY
}

has_modules() {
    local python_bin="$1"
    shift
    list_missing_modules "$python_bin" "$@" >/dev/null 2>&1
}

# Create venv if needed
if [ ! -d "venv" ]; then
    echo "📦 Creating Python virtual environment (reusing system site-packages when available)..."
    python3 -m venv --system-site-packages venv
fi

VENV_PY="${ROOT_DIR}/venv/bin/python"
RUNTIME_PY="$VENV_PY"

echo "📦 Checking Python dependencies..."
if has_modules "$VENV_PY" "${PYTHON_CORE_MODULES[@]}"; then
    echo "   ✅ Using project virtualenv"
elif has_modules python3 "${PYTHON_CORE_MODULES[@]}"; then
    echo "   ⚠️  Virtualenv is missing core packages; falling back to system Python"
    echo "   ℹ️  Delete ./venv later if you want it recreated cleanly"
    RUNTIME_PY="python3"
else
    echo "   ⚠️  Core packages missing; trying direct wheel install (without editable build)..."
    if "$VENV_PY" -m pip install --disable-pip-version-check \
        fastapi 'uvicorn[standard]' pydantic httpx cryptography aiohttp pytest pytest-asyncio; then
        if has_modules "$VENV_PY" "${PYTHON_CORE_MODULES[@]}"; then
            echo "   ✅ Installed core Python dependencies into virtualenv"
        else
            echo "   ❌ Python dependencies are still incomplete after install attempt"
            exit 1
        fi
    else
        echo "   ❌ Unable to install missing Python packages automatically."
        echo "      This machine can still start with system Python only if it already has:"
        echo "      ${PYTHON_CORE_MODULES[*]}"
        exit 1
    fi
fi

OPTIONAL_MISSING="$(list_missing_modules "$RUNTIME_PY" "${PYTHON_OPTIONAL_MODULES[@]}" 2>/dev/null || true)"
if [ -n "${OPTIONAL_MISSING}" ]; then
    echo "   ⚠️  Optional Python modules missing: ${OPTIONAL_MISSING}"
    echo "      Some cost/OpenCost or dev-only features may stay degraded until they are installed."
fi

# Install Node deps
if command -v npm &> /dev/null && command -v node &> /dev/null; then
    USE_SYSTEM_NPM=1
    NODE_BIN="$(command -v node)"
elif [ -x "${BUNDLED_NODE}" ]; then
    NODE_BIN="${BUNDLED_NODE}"
else
    echo "❌ Node.js runtime not found. Install node/npm or provide the bundled Codex runtime."
    exit 1
fi

if [ ! -d "node_modules" ]; then
    echo "📦 Installing Node dependencies..."
    if [ "${USE_SYSTEM_NPM}" -eq 1 ]; then
        if ! npm install --silent 2>/dev/null; then
            echo "⚠️  npm install had issues, trying without --silent..."
            npm install
        fi
    else
        echo "❌ node_modules is missing and npm is unavailable in this shell."
        echo "   Start once from a shell with npm, or vendor node_modules before retrying."
        exit 1
    fi
fi

echo ""
echo "✅ Dependencies ready"
if [ "${USE_SYSTEM_NPM}" -eq 1 ]; then
    echo "   Frontend toolchain: system npm/node"
else
    echo "   Frontend toolchain: bundled Codex node"
fi
echo ""

# Start backend
echo "🔧 Starting backend on port 8080..."
cd src/backend
"${RUNTIME_PY}" main.py --port 8080 &
BACKEND_PID=$!
cd ../..

# Wait for backend to be ready
echo "   Waiting for backend..."
for i in $(seq 1 15); do
    if curl -s http://localhost:8080/api/v1/health > /dev/null 2>&1; then
        echo "   ✅ Backend ready"
        break
    fi
    if ! kill -0 $BACKEND_PID 2>/dev/null; then
        echo "   ❌ Backend failed to start. Check logs."
        exit 1
    fi
    sleep 1
done

# Start frontend
echo "🌐 Starting frontend on port 5173..."
if [ "${USE_SYSTEM_NPM}" -eq 1 ]; then
    npm run dev &
else
    "${NODE_BIN}" node_modules/vite/bin/vite.js --config vite.config.mjs &
fi
FRONTEND_PID=$!

# Wait for frontend
sleep 2
if ! kill -0 $FRONTEND_PID 2>/dev/null; then
    echo "❌ Frontend failed to start"
    kill $BACKEND_PID 2>/dev/null
    exit 1
fi

echo ""
echo "════════════════════════════════════════"
echo "  AgentsGroup2026 is running!"
echo ""
echo "  Frontend: http://localhost:5173"
echo "  Backend:  http://localhost:8080"
echo "  API Docs: http://localhost:8080/docs"
echo "════════════════════════════════════════"
echo ""
echo "Press Ctrl+C to stop all services"

cleanup() {
    echo ""
    echo "Shutting down..."
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    wait $BACKEND_PID 2>/dev/null
    wait $FRONTEND_PID 2>/dev/null
    echo "Done."
    exit 0
}
trap cleanup SIGINT SIGTERM
wait
