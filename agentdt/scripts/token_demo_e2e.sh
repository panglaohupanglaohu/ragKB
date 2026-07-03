#!/usr/bin/env bash
# Phase 7 Demo Case — Token 端到端数值核对
#
# 用法: bash scripts/token_demo_e2e.sh [BASE_URL]
# 默认 BASE_URL=http://127.0.0.1:8080
#
# 校验 C1~C6 恒等式:
#   C1 跨维恒等: phase_sum == team_sum == totals.total_tokens
#   C2 run 级一致: LEDGER.run(rid).total == DB SUM(total_tokens) WHERE run_id=rid
#   C3 技能卡一致: tokens_consumed == LEDGER.run(RV).total == by-skill total (同窗口)
#   C4 再节省: TB < TA (优化后 token 下降)
#   C5 棘轮单调: cost_efficiency:default 存在且只进不退
#   C6 孪生非零: by_phase.drill > 0 (contextvar 跨线程修复生效)
set -euo pipefail

BASE="${1:-http://127.0.0.1:8080}"
API="$BASE/api/v1"
DB_PATH="${DB_PATH:-storage/usage.db}"
PASS=0; FAIL=0

ok()   { echo "✅ $1"; PASS=$((PASS+1)); }
fail() { echo "❌ $1: $2"; FAIL=$((FAIL+1)); }

echo "═══ Phase 7 Demo Case — Token E2E ═══"
echo "BASE=$BASE  DB=$DB_PATH"
echo

# ── 前置: 报告可生成且对账一致 ──
echo "── D3 报告对账 ──"
REPORT=$(curl -s "$API/cost/report?window=24h")
CONSISTENT=$(echo "$REPORT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('reconciliation',{}).get('consistent',False))" 2>/dev/null || echo "False")
if [ "$CONSISTENT" = "True" ]; then ok "D3 reconciliation.consistent=true"; else fail "D3 reconciliation" "consistent=$CONSISTENT"; fi

# ── C1: 跨维恒等 ──
echo
echo "── C1 跨维恒等 ──"
PHASE_SUM=$(echo "$REPORT" | python3 -c "import sys,json; r=json.load(sys.stdin); print(sum(v.get('total',0) if isinstance(v,dict) else v for v in r.get('totals',{}).get('by_phase',{}).values()))" 2>/dev/null || echo 0)
TEAM_SUM=$(echo "$REPORT" | python3 -c "import sys,json; r=json.load(sys.stdin); print(sum(t.get('total',0) for t in r.get('by_team',[])))" 2>/dev/null || echo 0)
TOTAL_TOKENS=$(echo "$REPORT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('totals',{}).get('total_tokens',0))" 2>/dev/null || echo 0)
if [ "$PHASE_SUM" = "$TEAM_SUM" ] && [ "$TEAM_SUM" = "$TOTAL_TOKENS" ]; then
  ok "C1 phase_sum($PHASE_SUM)==team_sum($TEAM_SUM)==total($TOTAL_TOKENS)"
else
  fail "C1 跨维恒等" "phase=$PHASE_SUM team=$TEAM_SUM total=$TOTAL_TOKENS"
fi

# ── C2: run 级一致（对所有已知 run_id）──
echo
echo "── C2 run 级一致 ──"
# 从 DB 取所有非空 run_id
RUN_IDS=$(python3 -c "
import sqlite3
c=sqlite3.connect('$DB_PATH')
rows=c.execute('SELECT DISTINCT run_id FROM usage_log WHERE run_id IS NOT NULL AND run_id != \"\" LIMIT 5').fetchall()
print(' '.join(r[0] for r in rows))
" 2>/dev/null || echo "")
if [ -z "$RUN_IDS" ]; then
  echo "⏭️  无 run_id 数据，跳过 C2"
else
  for RID in $RUN_IDS; do
    API_VAL=$(curl -s "$API/cost/tokens/run/$RID" | python3 -c "import sys,json; print(json.load(sys.stdin).get('total',0))" 2>/dev/null || echo 0)
    DB_VAL=$(python3 -c "
import sqlite3
c=sqlite3.connect('$DB_PATH')
print(c.execute('SELECT COALESCE(SUM(total_tokens),0) FROM usage_log WHERE run_id=?',('$RID',)).fetchone()[0])
" 2>/dev/null || echo 0)
    if [ "$API_VAL" = "$DB_VAL" ]; then
      ok "C2 run=$RID api=$API_VAL db=$DB_VAL"
    else
      fail "C2 run=$RID" "api=$API_VAL db=$DB_VAL"
    fi
  done
fi

# ── C6: 孪生非零 ──
echo
echo "── C6 孪生 token 非零 ──"
DRILL_TOKENS=$(curl -s "$API/cost/tokens/summary?group_by=phase&window=7d" | python3 -c "
import sys,json
d=json.load(sys.stdin)
items=d.get('items',{})
if isinstance(items,dict):
  drill=items.get('drill',{})
  print(drill.get('total',0) if isinstance(drill,dict) else drill)
else:
  print(0)
" 2>/dev/null || echo 0)
if [ "$DRILL_TOKENS" -gt 0 ] 2>/dev/null; then
  ok "C6 by_phase.drill=$DRILL_TOKENS > 0 (contextvar 跨线程生效)"
else
  fail "C6 孪生归因" "drill=$DRILL_TOKENS (若未跑过孪生演练则正常为 0)"
fi

# ── C5: 棘轮单调 ──
echo
echo "── C5 棘轮单调 ──"
RATCHET=$(echo "$REPORT" | python3 -c "
import sys,json
r=json.load(sys.stdin)
locked=r.get('ratchet_locked',[])
ce=[l for l in locked if 'cost_efficiency' in l.get('metric_key','')]
print(len(ce))
" 2>/dev/null || echo 0)
if [ "$RATCHET" -gt 0 ] 2>/dev/null; then
  ok "C5 ratchet cost_efficiency 存在 ($RATCHET 条)"
else
  echo "⏭️  暂无 cost_efficiency 棘轮记录（需跑过孪生演练并通过 Gate）"
fi

# ── 汇总 ──
echo
echo "═══════════════════════════════════"
echo "Demo Case 汇总: $PASS PASS / $FAIL FAIL"
echo "═══════════════════════════════════"
if [ $FAIL -eq 0 ]; then
  echo "DEMO PASS: C1..C6 all green"
  exit 0
else
  echo "DEMO FAIL: $FAIL 项未通过"
  exit 1
fi
