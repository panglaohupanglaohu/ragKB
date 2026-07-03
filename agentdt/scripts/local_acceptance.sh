#!/usr/bin/env bash
# 本机验收清单 — 一键跑完本会话所有"沙箱外/需本机"的验证项。
#
# 用法:
#   bash scripts/local_acceptance.sh                # 跑离线部分(单测/编译/闭环离线 demo)
#   bash scripts/local_acceptance.sh --with-server  # 额外跑需后端 8080 的项(SSE 流 / pytest 接口门 / 真试炼闭环)
#   TEAM=build_system AGENT=build_reviewer bash scripts/local_acceptance.sh --with-server  # 指定真试炼团队/评审员
#
# 在本机用 `rtk` 包裹更稳:  rtk bash scripts/local_acceptance.sh --with-server
set -u
cd "$(dirname "$0")/.."

WITH_SERVER=0
[ "${1:-}" = "--with-server" ] && WITH_SERVER=1
BASE_URL="${BASE_URL:-http://localhost:8080}"
TEAM="${TEAM:-}"
AGENT="${AGENT:-}"

PASS=0; FAIL=0; SKIP=0
section(){ echo; echo "════════════════════════════════════════"; echo "▶ $1"; echo "────────────────────────────────────────"; }
run(){ # run "<desc>" <cmd...>
  local desc="$1"; shift
  echo "• $desc"
  if "$@" >/tmp/_acc.log 2>&1; then echo "  ✅ PASS"; PASS=$((PASS+1));
  else echo "  ❌ FAIL (tail:)"; tail -5 /tmp/_acc.log | sed 's/^/    /'; FAIL=$((FAIL+1)); fi
}
skip(){ echo "• $1"; echo "  ⏭  SKIP ($2)"; SKIP=$((SKIP+1)); }

# ── 1. 前端单测(全量)──────────────────────────────────
section "1. 前端单测  (vitest)"
run "npx vitest run (全部前端用例)" npx vitest run

# ── 2. 后端语法编译(快速健全性)────────────────────────
section "2. 后端 py_compile(改动文件)"
run "agent_team_api.py" python3 -m py_compile src/backend/agent_team_api.py
run "agents/api.py"      python3 -m py_compile src/backend/agents/api.py
run "agents/skill_router.py" python3 -m py_compile src/backend/agents/skill_router.py
run "channels/system_evolution.py" python3 -m py_compile src/backend/channels/system_evolution.py
run "sandbox/twin_loop.py" python3 -m py_compile src/backend/sandbox/twin_loop.py

# ── 3. 技能闭环(离线,纯 sandbox,不需 LLM/外网)──────────
section "3. 技能闭环 离线 demo  (S-2)"
run "skill_closed_loop_demo.py(目标能力应 +18pp,exit 0)" python3 scripts/skill_closed_loop_demo.py

# ── 4. 后端接口门 + SSE 流(需 8080)────────────────────
section "4. 后端接口门 / SSE(需 --with-server + 后端在跑)"
if [ "$WITH_SERVER" = "1" ]; then
  run "pytest -q(全量后端)" python3 -m pytest -q
  echo "• system-evolution SSE 端点 (/evolution/stream)"
  code=$(curl -s -N -m 4 -o /tmp/_sse.txt -w "%{http_code}" "$BASE_URL/api/v1/agent-teams/evolution/stream" || echo 000)
  ct=$(grep -i 'event-stream' /tmp/_sse.txt >/dev/null 2>&1 && echo yes || echo no)
  if [ "$code" = "200" ]; then echo "  ✅ PASS (HTTP 200)"; PASS=$((PASS+1)); else echo "  ❌ FAIL (HTTP $code — 需登录/起服务)"; FAIL=$((FAIL+1)); fi
  run "plaza SSE 测试(静态+TestClient)" python3 -m pytest -q tests/test_evolution_stream.py
else
  skip "pytest 接口门" "未加 --with-server"
  skip "SSE /evolution/stream" "未加 --with-server"
fi

# ── 5. 技能闭环(真后端,需 8080 + 团队/评审员)──────────
section "5. 技能闭环 真后端 cross-check  (S-5.4)"
if [ "$WITH_SERVER" = "1" ] && [ -n "$TEAM" ] && [ -n "$AGENT" ]; then
  run "skill_closed_loop_live.py(对照离线 +18.3pp)" python3 scripts/skill_closed_loop_live.py --base-url "$BASE_URL/api/v1" --team "$TEAM" --agent "$AGENT"
else
  skip "skill_closed_loop_live.py" "需 --with-server 且设 TEAM=.. AGENT=.."
fi

# ── 6. 浏览器肉眼验收清单(脚本测不了,逐项点)────────────
section "6. 浏览器逐项点测(登录后手测)"
cat <<'EOF'
  [ ] 数字孪生:左选 Build System → 右「选择演练团队」即变;点议事厅 → 右「选择演练场景」跟随;手动选过具体场景后切房间不被覆盖 (L0)
  [ ] 跨页:数字孪生切团队 → 另开 skill-extract / agent-team-config / system-evolution 默认/实时跟随该团队 (L2/L4)
  [ ] system-evolution:断开后端 → 概览 SSE 断线后 30s 轮询降级生效 (A-3.3)
  [ ] plaza:讨论中 kill 后端再拉起 → 自动重连、消息不重复、状态栏先「重连中」(plaza A-3)
  [ ] skill-extract:赋予页勾选技能→⚡赋予/注入→提示熟练度抬升;未勾选点注入只提示不盲注 (S-5/S-6.1)
  [ ] skill-extract:多需求多次「路由」结果累加去重,「🧹清空」重置 (S-6.2)
  [ ] agent 详情聊天:发送后用户气泡 + 「正在思考…」立刻出现(不再像没发出) (#6)
  [ ] 任务页:卡死 running 任务返回体含 stuck/elapsed_sec(F12 看 /tasks 响应) (T1)
EOF

# ── 汇总 ───────────────────────────────────────────────
section "汇总"
echo "PASS=$PASS  FAIL=$FAIL  SKIP=$SKIP"
[ "$FAIL" = "0" ] && echo "✅ 自动项全绿(浏览器清单请逐项手测)" || echo "❌ 有失败项,见上方 tail"
exit $FAIL
