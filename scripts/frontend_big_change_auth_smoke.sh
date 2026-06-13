#!/usr/bin/env bash
# CB-FE-04: 登录后页面 smoke 脚本（curl cookie jar 版）
# 验证: 注册/登录 → cookie 生效 → 受保护 API 不再 401 → 目标页面/脚本可访问
#
# 用法:
#   bash scripts/frontend_big_change_auth_smoke.sh [base_url]
#   默认 base_url=http://127.0.0.1:8080
#
# 输出: 成功时 exit 0，失败时输出最后一个 HTTP 状态和响应摘要

set -euo pipefail

BASE_URL="${1:-http://127.0.0.1:8080}"
JAR="$(mktemp -t cb-auth-smoke.XXXXXX)"
USER="cb_smoke_$(date +%s)_${RANDOM}"
PASS="TestPass123!"
FAIL_LOG="$(mktemp -t cb-auth-smoke-fail.XXXXXX)"
trap 'rm -f "$JAR" "$FAIL_LOG"' EXIT

red()  { echo -e "\033[31m$*\033[0m"; }
green(){ echo -e "\033[32m$*\033[0m"; }
dim()  { echo -e "\033[2m$*\033[0m"; }

fail() {
  red "❌ FAIL: $*"
  echo "--- last response (first 300 chars) ---"
  head -c 300 "$FAIL_LOG" 2>/dev/null || true
  exit 1
}

log_step() { dim "  → $*"; }

# ── Step 1: 注册用户 ──
log_step "注册用户 $USER"
curl -sS -o "$FAIL_LOG" -c "$JAR" -H 'Content-Type: application/json' \
  -d "{\"username\":\"$USER\",\"password\":\"$PASS\"}" \
  "$BASE_URL/api/v1/auth/register" >/dev/null 2>&1 || true
# 注册可能返回 200(新用户)或 409(已存在)，两者都接受
reg_code=$(curl -sS -o /dev/null -w '%{http_code}' -c "$JAR" -b "$JAR" \
  -H 'Content-Type: application/json' \
  -d "{\"username\":\"$USER\",\"password\":\"$PASS\"}" \
  "$BASE_URL/api/v1/auth/register" 2>/dev/null || echo "000")
if [ "$reg_code" != "200" ] && [ "$reg_code" != "409" ] && [ "$reg_code" != "201" ]; then
  # 尝试登录代替
  log_step "注册返回 $reg_code，尝试登录"
  curl -sS -o "$FAIL_LOG" -c "$JAR" -b "$JAR" \
    -H 'Content-Type: application/json' \
    -d "{\"username\":\"$USER\",\"password\":\"$PASS\"}" \
    "$BASE_URL/api/v1/auth/login" >/dev/null 2>&1 || true
fi

# ── Step 2: 验证认证状态 ──
log_step "检查 /api/v1/auth/me"
me_resp=$(curl -sS -o "$FAIL_LOG" -w '%{http_code}' -b "$JAR" "$BASE_URL/api/v1/auth/me" 2>/dev/null)
if [ "$me_resp" != "200" ]; then
  fail "/api/v1/auth/me returned $me_resp"
fi
if ! grep -q '"authenticated":true' "$FAIL_LOG" 2>/dev/null; then
  fail "/api/v1/auth/me not authenticated"
fi
green "  ✓ authenticated"

# ── Step 3: 页面与拆分脚本 200 ──
for path in \
  /Agent-digital-twin.html \
  /js/digital-twin/secs-core.js \
  /js/digital-twin/director.js \
  /js/digital-twin/v4-scenario-evolution.js \
  /js/digital-twin-cli.js \
  /js/sandbox-twin.js
do
  log_step "GET $path"
  code=$(curl -sS -o "$FAIL_LOG" -w '%{http_code}' -b "$JAR" "$BASE_URL$path" 2>/dev/null)
  if [ "$code" != "200" ]; then
    fail "$path returned $code"
  fi
  green "  ✓ $path"
done

# ── Step 4: 受保护 API 不再 401 ──
log_step "GET /api/v1/twin-trials (should not 401)"
code=$(curl -sS -o "$FAIL_LOG" -w '%{http_code}' -b "$JAR" "$BASE_URL/api/v1/twin-trials" 2>/dev/null)
if [ "$code" = "401" ]; then
  fail "/api/v1/twin-trials still 401"
fi
green "  ✓ /api/v1/twin-trials HTTP $code"

# ── All clear ──
green "✅ Auth smoke passed — user=$USER"
exit 0
