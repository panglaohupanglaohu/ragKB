#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# verify_v4_local.sh — 本机一键复核 v4 "接口通路门" + 全程回归
#
# 用途：在有 fastapi 的本机 rtk 环境跑 [~] 项的接口/回归验收，全绿后把
#       docs/Agent数字孪生场景演练与技能进化todos.md 对应条目 [~] → [x]。
#
# 覆盖：
#   test_v4_apis.py            → B-1.1/1.2/1.3/1.5, B-2.1~2.5, B-3.1~3.6, E-2
#   test_sandbox_secs.py
#   test_full_flow.py          → E-5（全程回归）
#   test_scenario_system.py    → 场景系统纯逻辑（基线，不应回归）
#   test_digital_twin_move_state_machine.py → C-4.1/F3（房间状态机 200/409）
#
# 不覆盖（需真 LLM，留给 Claude）：B-1.4, C-1.4, C-2.5, E-3
#
# 用法：
#   bash scripts/verify_v4_local.sh                          # 只跑+报告（dry-run）
#   bash scripts/verify_v4_local.sh --apply                  # 全绿则回写 [~]→[x]
#   bash scripts/verify_v4_local.sh --with-server            # 含 E-5 活后端脚本（需 8080 在跑）
#   bash scripts/verify_v4_local.sh --with-server --apply    # 含 E-5 并回写
#   RUNNER="python3 -m" bash scripts/verify_v4_local.sh      # 不用 rtk 时覆盖运行器
#
# E-5 的 test_full_flow.py 是打 http://localhost:8080 的活后端 E2E 脚本（非 pytest），
# 仅 --with-server 且后端健康时才跑；想验 E-5 先 `bash start.sh` 起后端。
# ─────────────────────────────────────────────────────────────────────────────
set -uo pipefail

# ── 定位仓库根 ───────────────────────────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$ROOT" || { echo "无法进入仓库根: $ROOT"; exit 2; }

DOC="docs/Agent数字孪生场景演练与技能进化todos.md"
RUNNER="${RUNNER:-rtk}"        # 默认用 rtk；可用 RUNNER="python3 -m" 覆盖
APPLY=0
WITH_SERVER=0
for arg in "$@"; do
  case "$arg" in
    --apply)       APPLY=1 ;;
    --with-server) WITH_SERVER=1 ;;
    *) echo "未知参数: $arg（支持 --apply / --with-server）" ;;
  esac
done
TODAY="$(date +%Y-%m-%d)"

# test_full_flow.py 是"活后端 E2E 脚本"（无 pytest 用例，靠 assert+退出码）。
# 它只依赖标准库（json/urllib）+ 一个在跑的后端，不需要 rtk/venv/fastapi，
# 因此直接用 python3 跑（rtk 没有 `rtk python` 子命令）。可用 PYRUN 覆盖。
PYRUN="${PYRUN:-python3}"
SERVER_HEALTH="http://localhost:8080/api/v1/agent-config/health"

# ── 颜色 ─────────────────────────────────────────────────────────────────────
if [ -t 1 ]; then G='\033[32m'; R='\033[31m'; Y='\033[33m'; B='\033[1m'; N='\033[0m'; else G=''; R=''; Y=''; B=''; N=''; fi
pass(){ printf "${G}✔ PASS${N}  %s\n" "$1"; }
fail(){ printf "${R}✘ FAIL${N}  %s\n" "$1"; }
info(){ printf "${Y}•${N} %s\n" "$1"; }

# ── 运行单个 pytest 套件，返回 rc ───────────────────────────────────────────
run_suite() {
  local label="$1"; shift
  local target="$1"; shift
  if [ ! -e "$target" ]; then
    info "跳过 $label（找不到 $target）"; return 3
  fi
  printf "\n${B}── %s ──${N}\n" "$label"
  # shellcheck disable=SC2086
  $RUNNER pytest -q "$target"
  return $?
}

echo -e "${B}v4 本机验收${N}  repo=$ROOT  runner='$RUNNER'  apply=$APPLY  with-server=$WITH_SERVER  date=$TODAY"

# ── 跑各套件 ─────────────────────────────────────────────────────────────────
run_suite "test_v4_apis（接口通路门 B/E-2）"            tests/test_v4_apis.py;                       RC_API=$?
run_suite "test_sandbox_secs（E-5）"                    tests/test_sandbox_secs.py;                  RC_SECS=$?

# test_full_flow.py 不是 pytest 套件，是打 localhost:8080 的活后端 E2E 脚本。
# 仅 --with-server 且后端健康时按脚本方式跑；否则跳过（rc=3），E-5 不回写。
if [ "$WITH_SERVER" -eq 1 ]; then
  printf "\n${B}── test_full_flow（E-5 · 活后端脚本）──${N}\n"
  if curl -sS -m 5 -o /dev/null "$SERVER_HEALTH" 2>/dev/null; then
    # shellcheck disable=SC2086
    $PYRUN tests/test_full_flow.py; RC_FLOW=$?
  else
    info "后端未在 8080 响应（$SERVER_HEALTH），跳过；E-5 不回写。先起后端：bash start.sh"
    RC_FLOW=3
  fi
else
  info "test_full_flow（E-5）：未加 --with-server，跳过活后端脚本；E-5 不回写"
  RC_FLOW=3
fi

run_suite "test_scenario_system（基线）"                tests/test_scenario_system.py;               RC_SCEN=$?
run_suite "test_digital_twin_move_state_machine（C-4.1/F3）" tests/test_digital_twin_move_state_machine.py; RC_MOVE=$?

# ── 汇总 ─────────────────────────────────────────────────────────────────────
printf "\n${B}════════ 汇总 ════════${N}\n"
status(){ [ "$1" -eq 0 ] && pass "$2" || { [ "$1" -eq 3 ] && info "$2（未跑/缺文件）" || fail "$2"; }; }
status "$RC_API"  "test_v4_apis.py  → B-1.1/1.2/1.3/1.5, B-2.1~2.5, B-3.1~3.6, E-2"
status "$RC_SECS" "test_sandbox_secs.py  → E-5"
status "$RC_FLOW" "test_full_flow.py  → E-5"
status "$RC_SCEN" "test_scenario_system.py  → 场景基线"
status "$RC_MOVE" "test_digital_twin_move_state_machine.py  → C-4.1/F3"

# ── 计算可回写的条目 ─────────────────────────────────────────────────────────
ELIGIBLE=""
[ "$RC_API"  -eq 0 ] && ELIGIBLE="$ELIGIBLE B-1.1 B-1.2 B-1.3 B-1.5 B-2.1 B-2.2 B-2.3 B-2.4 B-2.5 B-3.1 B-3.2 B-3.3 B-3.4 B-3.5 B-3.6 E-2"
{ [ "$RC_SECS" -eq 0 ] && [ "$RC_FLOW" -eq 0 ]; } && ELIGIBLE="$ELIGIBLE E-5"
ELIGIBLE="$(echo "$ELIGIBLE" | xargs 2>/dev/null || true)"

if [ -z "$ELIGIBLE" ]; then
  printf "\n${R}无可回写条目${N}：相关套件未全绿，文档不改。先修测试再跑。\n"
  exit 1
fi

printf "\n${B}符合回写条件（全绿）的条目：${N}\n  %s\n" "$ELIGIBLE"

if [ "$APPLY" -ne 1 ]; then
  printf "\n${Y}dry-run${N}：未改文档。确认无误后加 --apply 回写：\n  bash scripts/verify_v4_local.sh --apply\n"
  exit 0
fi

# ── 回写 [~] → [x]（仅符合条件的条目，幂等）──────────────────────────────────
[ -f "$DOC" ] || { fail "找不到文档 $DOC"; exit 2; }
cp "$DOC" "$DOC.bak"   # 备份，回滚用 mv "$DOC.bak" "$DOC"

CHANGED=0
for ID in $ELIGIBLE; do
  # 仅匹配形如：- [~] **ID** ...   把该行首个 [~] 改 [x] 并在行尾追加验收戳
  if grep -qE "^- \[~\] \*\*${ID}\*\*" "$DOC"; then
    awk -v id="$ID" -v day="$TODAY" '
      $0 ~ ("^- \\[~\\] \\*\\*" id "\\*\\*") {
        sub(/\[~\]/, "[x]");
        print $0 "　〔本机 " day " 验收全绿，接口通路门通过（verify_v4_local.sh）〕";
        next
      }
      { print }
    ' "$DOC" > "$DOC.tmp" && mv "$DOC.tmp" "$DOC"
    pass "回写 $ID  [~]→[x]"
    CHANGED=$((CHANGED+1))
  else
    info "$ID 当前不是 [~]（可能已 [x] 或措辞不符），跳过"
  fi
done

printf "\n${B}完成${N}：回写 %s 条。备份在 %s（回滚：mv \"%s\" \"%s\"）\n" "$CHANGED" "$DOC.bak" "$DOC.bak" "$DOC"
printf "建议复核 diff：git diff -- \"%s\"\n" "$DOC"
