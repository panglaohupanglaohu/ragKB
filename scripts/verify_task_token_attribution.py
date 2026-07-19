#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""任务 Token 归因验收 — 分析台 / 工作台 是否认到「任务执行」消耗

北极星：优化对象 = 任务执行 token（phase=task + team_id + scenario_id=task_id）。
不把 cat_speak / tg_prepare / 空 team 杂项算进团队分析台。

检查项：
  1) 离线：临时库写入 build_system 任务消耗 → by_team / by_task 可见（代码路径）
  2) 离线：真实 storage/usage.db 诊断（归因率、build_system 任务消耗、未挂 team）
  3) 可选活后端：GET token-governance/dashboard + tokens/overview 口径一致

用法（项目根）:
  PYTHONPATH=src/backend python3 scripts/verify_task_token_attribution.py
  PYTHONPATH=src/backend python3 scripts/verify_task_token_attribution.py --team build_system
  PYTHONPATH=src/backend python3 scripts/verify_task_token_attribution.py --live
  PYTHONPATH=src/backend python3 scripts/verify_task_token_attribution.py --strict
      # --strict: 真实库里目标队 phase=task 且 total>0 必须存在，否则 FAIL

退出码：有 FAIL 则 1；仅 WARN 为 0。
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src" / "backend"))

USAGE_DB = ROOT / "storage" / "usage.db"

PASS = 0
FAIL = 0
WARN = 0


def _ok(name: str, detail: str = "") -> None:
    global PASS
    PASS += 1
    print(f"  PASS  {name}" + (f" — {detail}" if detail else ""))


def _fail(name: str, detail: str = "") -> None:
    global FAIL
    FAIL += 1
    print(f"  FAIL  {name}" + (f" — {detail}" if detail else ""))


def _warn(name: str, detail: str = "") -> None:
    global WARN
    WARN += 1
    print(f"  WARN  {name}" + (f" — {detail}" if detail else ""))


def _section(title: str) -> None:
    print(f"\n=== {title} ===")


# ── 1) 代码路径：临时库可写可读 ──────────────────────────────


def check_write_path_offline(team_id: str) -> None:
    _section("1) 离线写入路径（temp usage.db）")
    from agents.budget.models import UsageRecord
    from agents.budget.store import UsageStore
    from agents.token_ledger import TokenLedger

    task_id = f"task_verify_attr_{int(time.time())}"
    with tempfile.TemporaryDirectory() as tmp:
        db = Path(tmp) / "usage.db"
        store = UsageStore(db)
        # 模拟任务 step 记账
        store.record_usage(
            UsageRecord(
                session_id="sess_verify_attr",
                agent_id="build_architect",
                team_id=team_id,
                model="verify-model",
                input_tokens=1000,
                output_tokens=500,
                total_tokens=1500,
                phase="task",
                scenario_id=task_id,
                run_id="sess_verify_attr",
            )
        )
        # 噪声：未归因（分析台 by_team 默认应排除）
        store.record_usage(
            UsageRecord(
                session_id="sess_noise",
                agent_id="",
                team_id="",
                model="noise",
                input_tokens=99999,
                output_tokens=0,
                total_tokens=99999,
                phase="task",
                scenario_id="",
                run_id="sess_noise",
            )
        )
        # tg_prepare 不计为任务消耗（total=0）
        store.record_usage(
            UsageRecord(
                session_id="tg:x",
                agent_id="tg",
                team_id=team_id,
                model="tg_prepare_save:1",
                input_tokens=0,
                output_tokens=0,
                total_tokens=0,
                phase="tg_prepare",
                scenario_id=task_id,
                run_id="tg:x",
            )
        )

        ledger = TokenLedger(store=store)
        by_team = ledger.by_team("30d", include_unattributed=False)
        hit = next((r for r in by_team if r.get("team_id") == team_id), None)
        if hit and int(hit.get("total") or 0) == 1500:
            _ok("by_team 看见任务消耗", f"{team_id} total=1500 calls={hit.get('calls')}")
        else:
            _fail("by_team 看见任务消耗", f"got {hit}")

        unattr = ledger.by_team("30d", include_unattributed=True)
        empty = next((r for r in unattr if (r.get("team_id") or "") == ""), None)
        if empty and int(empty.get("total") or 0) >= 99999:
            _ok("未归因可单独查出", f"empty team total={empty.get('total')}")
        else:
            _fail("未归因可单独查出", f"got {empty}")

        by_task = ledger.by_task(window="30d", team_id=team_id, limit=20)
        th = next((r for r in by_task if r.get("task_key") == task_id), None)
        if th and int(th.get("total") or 0) == 1500:
            _ok("by_task 按 scenario_id 聚合", f"task_key={task_id} total=1500")
        else:
            _fail("by_task 按 scenario_id 聚合", f"got {th} all={by_task[:3]}")

        # 默认 by_team 不含空 team
        if not any((r.get("team_id") or "") == "" for r in by_team):
            _ok("by_team 默认排除空 team_id")
        else:
            _fail("by_team 默认排除空 team_id")


# ── 2) 真实库诊断 ────────────────────────────────────────────


def _sql_stats(db: Path) -> dict:
    if not db.is_file():
        return {"exists": False}
    con = sqlite3.connect(str(db))
    cur = con.cursor()
    out: dict = {"exists": True, "path": str(db)}

    def q(sql: str, args=()):
        return cur.execute(sql, args).fetchall()

    out["total_rows"] = q("SELECT COUNT(*) FROM usage_log")[0][0]
    out["total_tokens"] = q(
        "SELECT COALESCE(SUM(total_tokens),0) FROM usage_log WHERE total_tokens>0"
    )[0][0]
    out["task_tokens"] = q(
        "SELECT COALESCE(SUM(total_tokens),0) FROM usage_log "
        "WHERE phase='task' AND total_tokens>0"
    )[0][0]
    out["task_with_team"] = q(
        "SELECT COALESCE(SUM(total_tokens),0), COUNT(*) FROM usage_log "
        "WHERE phase='task' AND total_tokens>0 AND team_id IS NOT NULL AND team_id!=''"
    )[0]
    out["task_unscoped"] = q(
        "SELECT COALESCE(SUM(total_tokens),0), COUNT(*) FROM usage_log "
        "WHERE phase='task' AND total_tokens>0 AND (team_id IS NULL OR team_id='')"
    )[0]
    out["task_with_scenario"] = q(
        "SELECT COALESCE(SUM(total_tokens),0), COUNT(*) FROM usage_log "
        "WHERE phase='task' AND total_tokens>0 AND scenario_id IS NOT NULL AND scenario_id!=''"
    )[0]
    out["by_team_task"] = q(
        "SELECT team_id, COALESCE(SUM(total_tokens),0), COUNT(*) FROM usage_log "
        "WHERE phase='task' AND total_tokens>0 AND team_id!='' "
        "GROUP BY team_id ORDER BY SUM(total_tokens) DESC LIMIT 15"
    )
    out["tg_prepare_by_team"] = q(
        "SELECT team_id, COUNT(*), COALESCE(SUM(total_tokens),0) FROM usage_log "
        "WHERE phase='tg_prepare' GROUP BY team_id LIMIT 10"
    )
    con.close()
    return out


def check_real_db(team_id: str, strict: bool) -> None:
    _section("2) 真实 usage.db 诊断（任务维）")
    st = _sql_stats(USAGE_DB)
    if not st.get("exists"):
        _fail("usage.db 存在", str(USAGE_DB))
        return
    _ok("usage.db 存在", str(USAGE_DB))

    tot = int(st["total_tokens"] or 0)
    task_tok = int(st["task_tokens"] or 0)
    with_team_tok, with_team_n = int(st["task_with_team"][0] or 0), int(st["task_with_team"][1] or 0)
    unsc_tok, unsc_n = int(st["task_unscoped"][0] or 0), int(st["task_unscoped"][1] or 0)
    with_sc_tok, with_sc_n = int(st["task_with_scenario"][0] or 0), int(st["task_with_scenario"][1] or 0)

    print(f"  · 全库 total_tokens>0 合计: {tot:,}")
    print(f"  · phase=task 合计:         {task_tok:,}")
    print(f"  · task 且有 team_id:       {with_team_tok:,} tokens / {with_team_n} 行")
    print(f"  · task 且空 team_id:       {unsc_tok:,} tokens / {unsc_n} 行  ← 工作台「窗口」会含这部分")
    print(f"  · task 且有 scenario_id:   {with_sc_tok:,} tokens / {with_sc_n} 行  ← 任务账单 by_task")

    if task_tok > 0:
        rate = with_team_tok / task_tok
        print(f"  · 任务 team 归因率:        {rate:.1%}")
        if rate >= 0.5:
            _ok("任务 team 归因率", f"{rate:.1%}")
        elif rate > 0:
            _warn("任务 team 归因率偏低", f"{rate:.1%} — 分析台 by_team 远小于窗口全量")
        else:
            _warn(
                "任务 team 归因率=0",
                "phase=task 全无 team_id → 分析台各队消耗均为 0（与窗口全量不可比）",
            )
    else:
        _warn("无 phase=task 正 token", "库中尚无任务执行消耗")

    # 目标队
    team_rows = {r[0]: (int(r[1] or 0), int(r[2] or 0)) for r in (st["by_team_task"] or [])}
    t_tok, t_n = team_rows.get(team_id, (0, 0))
    print(f"  · 目标队 {team_id} phase=task: {t_tok:,} tokens / {t_n} 行")
    if st["by_team_task"]:
        print("  · by_team (phase=task, total>0) top:")
        for tid, tok, n in st["by_team_task"][:8]:
            print(f"      {tid or '(empty)':20s}  {tok:>12,}  calls={n}")
    else:
        print("  · by_team (phase=task): （空）")

    tg_prep = st.get("tg_prepare_by_team") or []
    if tg_prep:
        print("  · tg_prepare（治理试跑，通常 total=0，不算任务消耗）:")
        for tid, n, tok in tg_prep[:6]:
            print(f"      {tid or '(empty)':20s}  rows={n}  tokens={tok}")

    if t_tok > 0:
        _ok(f"{team_id} 任务消耗已入账", f"{t_tok:,} tokens / {t_n} 行 → 分析台应能显示")
    else:
        msg = (
            f"{team_id} 无 phase=task 且 total>0 记录；"
            "分析台显示 0 与库一致。请用加固后的任务路径重跑一步真任务。"
        )
        if strict:
            _fail(f"{team_id} 任务消耗已入账", msg)
        else:
            _warn(f"{team_id} 任务消耗已入账", msg)

    # 与工作台「窗口」误解澄清
    if unsc_tok > 0 and t_tok == 0:
        _ok(
            "口径解释",
            f"窗口全量≈{task_tok:,} 含未挂 team={unsc_tok:,}；"
            f"分析台只认有 team 的任务行，故 {team_id}=0 属预期而非 KPI 算错",
        )


# ── 3) 活后端 ────────────────────────────────────────────────


def _http_get(url: str, timeout: float = 12.0) -> dict:
    req = urllib.request.Request(url, method="GET")
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def check_live(base: str, team_id: str, window: str) -> None:
    _section(f"3) 活后端 {base}")
    base = base.rstrip("/")
    try:
        dash = _http_get(f"{base}/api/v1/cost/token-governance/dashboard?window={window}")
    except Exception as e:
        _fail("GET token-governance/dashboard", str(e))
        return
    summary = dash.get("summary") or {}
    attr = dash.get("attribution") or {}
    win_total = int(summary.get("total") or 0)
    attr_total = int(attr.get("attributed_total") or 0)
    unsc = int(attr.get("unscoped_total") or 0)
    print(f"  · TG dashboard window={window} total={win_total:,} attributed={attr_total:,} unscoped={unsc:,}")
    if win_total >= 0:
        _ok("dashboard 可达", f"total={win_total:,}")
    if attr_total == 0 and win_total > 0:
        _warn("dashboard 任务归因", "attributed=0 而窗口>0 — 与 usage 空 team 一致")
    else:
        _ok("dashboard 任务归因", f"share={attr.get('attributed_share')}")

    try:
        ov = _http_get(f"{base}/api/v1/cost/tokens/overview?window={window}")
    except Exception as e:
        _warn("GET tokens/overview", str(e))
        ov = {}
    by_team = ov.get("by_team") or []
    team_hit = None
    for row in by_team:
        tid = row.get("team_id") or row.get("key") or row.get("team") or ""
        if tid == team_id:
            team_hit = row
            break
    if team_hit and int(team_hit.get("tokens") or team_hit.get("total") or 0) > 0:
        _ok(
            f"overview by_team[{team_id}]",
            f"tokens={team_hit.get('tokens') or team_hit.get('total')}",
        )
    else:
        _warn(
            f"overview by_team[{team_id}]",
            f"无正消耗（got {team_hit}）；分析台效率/构成会显示 0",
        )

    # 可选 sustainability
    try:
        sust = _http_get(f"{base}/api/v1/sustainability/group")
        teams = sust.get("teams") or []
        st = next((t for t in teams if t.get("team_id") == team_id), None)
        if st is not None:
            tok = float(st.get("tokens_consumed") or 0)
            print(f"  · sustainability {team_id} tokens_consumed={tok} dq={st.get('data_quality')}")
            if tok > 0:
                _ok("sustainability 团队消耗", f"{tok}")
            else:
                _warn("sustainability 团队消耗", "0 — 依赖 LEDGER.by_team 有 team 归因")
        else:
            _warn("sustainability 无该队", team_id)
    except Exception as e:
        _warn("sustainability/group", str(e))


# ── main ─────────────────────────────────────────────────────


def main() -> int:
    ap = argparse.ArgumentParser(description="任务 Token 归因验收（分析台 / 工作台）")
    ap.add_argument("--team", default="build_system", help="目标团队 id（默认 build_system）")
    ap.add_argument("--window", default="30d", help="活后端窗口 24h|7d|30d")
    ap.add_argument("--live", action="store_true", help="打活后端 8080")
    ap.add_argument("--base", default="http://127.0.0.1:8080", help="活后端 base URL")
    ap.add_argument(
        "--strict",
        action="store_true",
        help="真实库目标队必须有 phase=task total>0，否则 FAIL",
    )
    ap.add_argument("--offline-only", action="store_true", help="只跑 temp 写入路径")
    args = ap.parse_args()

    print("任务 Token 归因验收")
    print(f"  team={args.team}  window={args.window}  strict={args.strict}")

    check_write_path_offline(args.team)
    if not args.offline_only:
        check_real_db(args.team, strict=args.strict)
        if args.live:
            check_live(args.base, args.team, args.window)

    _section("汇总")
    print(f"  PASS={PASS}  FAIL={FAIL}  WARN={WARN}")
    if FAIL:
        print("  结果: FAIL")
        print(
            "  提示: 代码路径应 PASS；若真实库 WARN/FAIL，请用加固后的任务执行路径"
            "（team_id+task_id 注入）重跑一步 build 任务后再验。"
        )
        return 1
    print("  结果: PASS" + ("（含 WARN）" if WARN else ""))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
