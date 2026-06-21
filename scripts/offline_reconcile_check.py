#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""离线对账自检 — 无需 LLM / 运行环境即可验证 Token 账本恒等式与技能合并逻辑。

覆盖（对真实 storage/usage.db 与技能合并逻辑实跑）：
  C1  跨维恒等       Σby_phase == Σby_team(全量) == summary.total
  C2  run 级一致     LEDGER.run(rid).total == DB 直查 SUM(total_tokens)
  C3  技能卡一致     by_skill[i].total == DB 直查（同窗口）
  RP  报告对账       cost_report.reconciliation.consistent（全局 + team 过滤）
  MG  合并单测       skill_evolver.merge_skills 行为正确（fixture，不污染真实数据）

用法：
  python3 scripts/offline_reconcile_check.py [--window 7d] [--db PATH]
退出码：全部通过 0；任一失败 1。

注：C4/C5/C6（再节省、棘轮单调、drill 非零）与 3D 视觉验收需真实 LLM/浏览器，本脚本不覆盖。
"""
from __future__ import annotations

import argparse
import os
import sqlite3
import sys

# 让脚本可从仓库任意位置运行：定位 repo root 与 src/backend
_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
_BACKEND = os.path.join(_ROOT, "src", "backend")
if _BACKEND not in sys.path:
    sys.path.insert(0, _BACKEND)

GREEN, RED, DIM, RESET = "\033[32m", "\033[31m", "\033[2m", "\033[0m"
if not sys.stdout.isatty():
    GREEN = RED = DIM = RESET = ""


class Results:
    def __init__(self, quiet: bool = False):
        self.passed = 0
        self.failed = 0
        self.quiet = quiet  # 静默模式：只打印失败项 + 末尾汇总（用于 start.sh 预检）

    def check(self, name: str, ok: bool, detail: str = "") -> bool:
        if ok:
            self.passed += 1
            if not self.quiet:
                print(f"  [{GREEN}PASS{RESET}] {name}" + (f"  {DIM}{detail}{RESET}" if detail else ""))
        else:
            self.failed += 1
            print(f"  [{RED}FAIL{RESET}] {name}" + (f"  {DIM}{detail}{RESET}" if detail else ""))
        return ok


def _default_db() -> str:
    return os.path.join(_ROOT, "storage", "usage.db")


def run_ledger_checks(r: Results, window: str, db_path: str) -> None:
    if not r.quiet:
        print(f"\n{DIM}── Token 账本对账（window={window}, db={db_path}）──{RESET}")
    try:
        from agents.token_ledger import LEDGER
    except Exception as e:  # pragma: no cover
        r.check("import token_ledger", False, str(e))
        return
    if not os.path.isfile(db_path):
        r.check("usage.db 存在", False, db_path)
        return

    ws = LEDGER._window_start(window)
    conn = sqlite3.connect(db_path)

    # C1 跨维恒等（含未归因，同口径）
    phase_sum = sum(v["total"] for v in LEDGER.by_phase(window).values())
    try:
        team_all = LEDGER.by_team(window, include_unattributed=True)
    except TypeError:
        team_all = LEDGER.by_team(window)  # 旧签名兜底
    team_sum = sum(t["total"] for t in team_all)
    total = LEDGER.summary(window)["total"]
    r.check("C1 跨维恒等 Σby_phase==Σby_team(全量)==summary",
            phase_sum == team_sum == total,
            f"phase={phase_sum} team={team_sum} summary={total}")

    # C2 run 级一致
    runs = [x[0] for x in conn.execute(
        "SELECT DISTINCT run_id FROM usage_log WHERE run_id<>'' LIMIT 200")]
    c2_bad = []
    for rid in runs:
        api = LEDGER.run(rid)["total"]
        db = conn.execute(
            "SELECT COALESCE(SUM(total_tokens),0) FROM usage_log WHERE run_id=? AND total_tokens>0",
            (rid,)).fetchone()[0]
        if api != db:
            c2_bad.append((rid, api, db))
    r.check("C2 run 级一致 (LEDGER.run == DB 直查)",
            not c2_bad,
            f"{len(runs)} runs, {len(c2_bad)} 不一致" + (f" 例:{c2_bad[0]}" if c2_bad else ""))

    # C3 技能卡一致
    c3_bad = []
    for s in LEDGER.by_skill(window):
        db = conn.execute(
            "SELECT COALESCE(SUM(total_tokens),0) FROM usage_log WHERE skill_id=? AND date>=? AND total_tokens>0",
            (s["skill_id"], ws)).fetchone()[0]
        if s["total"] != db:
            c3_bad.append((s["skill_id"], s["total"], db))
    r.check("C3 技能卡一致 (by_skill == DB 直查)",
            not c3_bad,
            f"{len(LEDGER.by_skill(window))} skills, {len(c3_bad)} 不一致")
    conn.close()


def run_report_checks(r: Results, window: str) -> None:
    if not r.quiet:
        print(f"\n{DIM}── 成本报告对账（reconciliation.consistent）──{RESET}")
    try:
        from agents.cost_report import generate_cost_report
    except Exception as e:  # pragma: no cover
        r.check("import cost_report", False, str(e))
        return
    rep = generate_cost_report(window=window)
    rec = rep.get("reconciliation", {})
    r.check("RP 全局报告对账 consistent",
            bool(rec.get("consistent")),
            f"phase={rec.get('phase_sum')} team={rec.get('team_sum')} 未归因={rec.get('unattributed')}")
    # team 过滤：取一个有数据的团队
    try:
        from agents.token_ledger import LEDGER
        teams = [t for t in LEDGER.by_team(window) if (t.get("team_id") or "").strip()]
        if teams:
            tid = teams[0]["team_id"]
            rep2 = generate_cost_report(window=window, team=tid)
            r.check(f"RP team 过滤报告对账 consistent (team={tid})",
                    bool(rep2["reconciliation"]["consistent"]))
    except Exception as e:
        r.check("RP team 过滤报告", False, str(e))


def run_merge_check(r: Results) -> None:
    if not r.quiet:
        print(f"\n{DIM}── 技能合并逻辑（fixture，不写真实数据）──{RESET}")
    try:
        from agents.skill_evolver import SkillEvolver
        from agents.skill_library import SkillDefinition, SkillLifecycleStage
    except Exception as e:  # pragma: no cover
        r.check("import skill_evolver/library", False, str(e))
        return

    def mk(sid, instr, uc, sc, fc, tools):
        return SkillDefinition(
            skill_id=sid, name="结构化代码评审", description="对代码做结构化评审",
            category="dev", icon="🔍", slug="code-review-" + sid, instructions=instr,
            required_tools=tools, source="extracted", origin_team_id="teamX",
            lifecycle_stage=SkillLifecycleStage.TEAM_LOCAL, version=1,
            usage_count=uc, success_count=sc, fail_count=fc)

    s1 = mk("aaa1", "短指令", 10, 6, 4, ["grep"])
    s2 = mk("bbb2", "更长更完整的评审指令：先看接口契约，再看错误处理，最后看测试覆盖", 5, 3, 2, ["read_file"])

    class FakeLib:
        _team_manager = None

        def __init__(self, skills):
            self._s = {x.skill_id: x for x in skills}
            self.persisted = []

        def _find_skill(self, team, sid):
            return self._s.get(sid)

        def _persist_skill(self, skill, team):
            self.persisted.append(skill)

    ev = SkillEvolver()
    ev._skill_library = FakeLib([s1, s2])
    res = ev.merge_skills("teamX", ["aaa1", "bbb2"], "keep_longest")
    ok_call = res.get("status") == "merged" and ev._skill_library.persisted
    if not ok_call:
        r.check("MG merge_skills 调用成功", False, str(res))
        return
    m = ev._skill_library.persisted[0]
    r.check("MG keep_longest 取较长 instructions", m.instructions == s2.instructions)
    r.check("MG usage/success/fail 合并 (15/9/6)",
            (m.usage_count, m.success_count, m.fail_count) == (15, 9, 6),
            f"{m.usage_count}/{m.success_count}/{m.fail_count}")
    r.check("MG required_tools 并集", set(m.required_tools) == {"grep", "read_file"})
    r.check("MG effectiveness 重算 0.6", abs(m.effectiveness - 0.6) < 1e-6)
    r.check("MG lineage 指向 primary & source=merged",
            m.lineage == s2.skill_id and m.source == "merged")


def _strip_inline_comment(argv):
    """容错：zsh 交互模式不把 '#' 当注释，会把 `# 默认 7d` 当参数传进来。
    这里在解析前丢弃以 '#' 开头的 token 及其之后的一切，让示例可直接复制粘贴。"""
    out = []
    for a in argv:
        if a.startswith("#"):
            break
        out.append(a)
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="离线对账自检 (C1/C2/C3 + 报告 + 合并)")
    ap.add_argument("--window", default="7d", help="时间窗口 (24h/7d/30d/all)，默认 7d")
    ap.add_argument("--db", default=_default_db(), help="usage.db 路径")
    ap.add_argument("--quiet", action="store_true", help="只打印失败项 + 汇总（用于启动预检）")
    args = ap.parse_args(_strip_inline_comment(sys.argv[1:]))

    if not args.quiet:
        print(f"{DIM}AgentsGroup2026 · 离线对账自检{RESET}")
    r = Results(quiet=args.quiet)
    run_ledger_checks(r, args.window, args.db)
    run_report_checks(r, args.window)
    run_merge_check(r)

    total = r.passed + r.failed
    print()
    if r.failed == 0:
        print(f"{GREEN}OFFLINE CHECK PASS{RESET}: {r.passed}/{total} 全部通过")
        print(f"{DIM}（C4/C5/C6 再节省·棘轮单调·drill 非零，及 3D 视觉验收需真实 LLM/浏览器，本脚本不覆盖）{RESET}")
        return 0
    print(f"{RED}OFFLINE CHECK FAIL{RESET}: {r.failed}/{total} 项失败")
    return 1


if __name__ == "__main__":
    sys.exit(main())
