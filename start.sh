#!/bin/bash
# AgentsGroup2026 — Quick Start Script
# 注：不设 set -e，因为后台进程和子shell的退出码会导致脚本提前终止
set -u
set -o pipefail

cd "$(dirname "$0")"
ROOT_DIR="$(pwd)"
BUNDLED_NODE="${HOME}/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node"
NODE_BIN=""
USE_SYSTEM_NPM=0

echo "🚀 AgentsGroup2026 Starting..."
echo ""

# 启用版本化 git pre-commit 钩子（一次性、幂等）：提交前跑离线对账自检（零 token）
if [ -d ".githooks" ] && git rev-parse --git-dir >/dev/null 2>&1; then
    if [ "$(git config --get core.hooksPath 2>/dev/null || true)" != ".githooks" ]; then
        git config core.hooksPath .githooks 2>/dev/null \
            && echo "🪝 已启用 git pre-commit 钩子 (core.hooksPath=.githooks)，提交前自动对账" \
            && echo ""
    fi
fi

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 not found. Please install Python 3.11+"
    exit 1
fi

# 加载 .env 到当前 shell（API key 环境变量引用方案）。
# 后端 main.py 也会通过 env_loader 再加载一次，这里在 shell 层先导出，
# 让前端/子进程/其它脚本也能读到；缺失时提示用户运行 setup_keys.sh。
if [ -f ".env" ]; then
    set -a  # 自动导出后续 source 的变量
    # shellcheck disable=SC1091
    . ./.env
    set +a
    echo "🔑 已加载 .env 环境变量（API key 引用 env:VAR_NAME 生效）"
    echo ""
else
    echo "🔑 未发现 .env — 若模型 API Key 用 env:VAR_NAME 引用，请先运行:"
    echo "     bash scripts/setup_keys.sh"
    echo "   （填入真实密钥后重启本脚本即可；否则请在页面直接填明文 key）"
    echo ""
fi

# 启动前清理 8080/5173 上的旧进程，防止端口被占用
cleanup_port() {
    local port=$1 pids
    pids=$(lsof -ti:"$port" 2>/dev/null || true)
    if [ -n "$pids" ]; then
        echo "🧹 清理端口 $port 旧进程 (PID: $pids)"
        kill -9 $pids 2>/dev/null || true
        sleep 1
        echo "   ✅ 端口 $port 已释放"
    else
        echo "   ✅ 端口 $port 空闲"
    fi
}
echo "🔍 检查端口..."
cleanup_port 8080
cleanup_port 5173
echo ""

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

# 离线对账自检（零 LLM、零 token：仅读本地 usage.db + 跑技能合并 fixture）
# 不阻断启动：发现不一致只告警；首次运行无 usage.db 时跳过。
if [ -f "storage/usage.db" ]; then
    echo "🧮 离线对账自检 (C1/C2/C3 + 合并，零 token)..."
    if "${RUNTIME_PY}" scripts/offline_reconcile_check.py --quiet --window 7d; then
        echo "   ✅ 账本对账一致"
    else
        echo "   ⚠️  对账自检发现不一致（不阻断启动，详情见上方 FAIL 项 / 可手动跑 scripts/offline_reconcile_check.py 排查）"
    fi
    echo ""
else
    echo "🧮 离线对账自检：跳过（storage/usage.db 尚未生成，首次运行属正常）"
    echo ""
fi

# Local development admin bootstrap. Production deployments should set
# ADMIN_PASSWORD explicitly instead of relying on this quick-start helper.
DEV_ADMIN_PASSWORD_FILE="${ROOT_DIR}/config/.dev_admin_password"

admin_account_exists() {
    "$RUNTIME_PY" - "${ROOT_DIR}/config/users.json" <<'PY'
import json
import sys
from pathlib import Path

path = Path(sys.argv[1])
try:
    users = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
except Exception:
    users = {}

raise SystemExit(0 if isinstance(users, dict) and "admin" in users else 1)
PY
}

generate_dev_admin_password() {
    "$RUNTIME_PY" - "${DEV_ADMIN_PASSWORD_FILE}" <<'PY'
import secrets
import string
import sys
from pathlib import Path

alphabet = string.ascii_letters + string.digits
password = "".join(secrets.choice(alphabet) for _ in range(20))
path = Path(sys.argv[1])
path.parent.mkdir(parents=True, exist_ok=True)
path.write_text(password + "\n", encoding="utf-8")
path.chmod(0o600)
PY
}

if [ -z "${ADMIN_PASSWORD:-}" ] && [ -z "${AG_ALLOW_DEFAULT_ADMIN:-}" ]; then
    if [ ! -s "${DEV_ADMIN_PASSWORD_FILE}" ] && ! admin_account_exists; then
        generate_dev_admin_password
    fi

    if [ -s "${DEV_ADMIN_PASSWORD_FILE}" ]; then
        ADMIN_PASSWORD="$(tr -d '\r\n' < "${DEV_ADMIN_PASSWORD_FILE}")"
        export ADMIN_PASSWORD
        echo "🔐 Local development admin login:"
        echo "   Username: admin"
        echo "   Password: ${ADMIN_PASSWORD}"
        echo "   Stored at config/.dev_admin_password (gitignored). Set ADMIN_PASSWORD to override."
        echo ""
    else
        echo "🔐 Auth: existing admin account found. Set ADMIN_PASSWORD to reset it."
        echo ""
    fi
elif [ -n "${ADMIN_PASSWORD:-}" ]; then
    echo "🔐 Auth: ADMIN_PASSWORD provided for admin login"
    echo ""
else
    case "${AG_ALLOW_DEFAULT_ADMIN:-}" in
        1|true|TRUE|True|yes|YES|Yes)
            echo "🔐 Auth: AG_ALLOW_DEFAULT_ADMIN enabled; local login is admin / admin123"
            echo ""
            ;;
    esac
fi

# Start backend
echo "🔧 Starting backend on port 8080..."
cd src/backend
# 开发热重载（bug-055 根治"改了后端没生效"）：默认开启 uvicorn --reload，
# 后端代码一落盘自动重启，与 vite 前端热更对齐。AG_NO_RELOAD=1 可关闭（生产/性能场景）。
if [ "${AG_NO_RELOAD:-}" = "1" ]; then
    "${RUNTIME_PY}" main.py --port 8080 &
else
    echo "♻️  后端热重载已开启 (uvicorn --reload)——改完后端代码无需手动重启；AG_NO_RELOAD=1 可关闭"
    "${RUNTIME_PY}" main.py --port 8080 --reload &
fi
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
