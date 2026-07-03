# -*- coding: utf-8 -*-
"""技能闭环验证 Demo — Structured Code Review skill 在数字孪生中的成效。

闭环链路:
  skill-extract 萃取「结构化代码评审」skill
    → 赋予评审员 agent(提升其 code_review 熟练度先验 0.45 → 0.85)
    → 在真实场景 code_review_delivery 跑数字孪生试炼(TwinLoop)
    → 对比 baseline / treatment 的 code_review 任务成功率与团队整体成功率
    → 成效可量化、可复现 = 闭环成立。

特点:纯 sandbox.* 模块,不依赖 FastAPI / 真 LLM / 外网,可离线复跑。
用法:  python3 scripts/skill_closed_loop_demo.py
       (在仓库根目录执行;本机用 `rtk python3 ...` 亦可)
"""
import sys, os, json, asyncio, random, statistics

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src", "backend"))

from sandbox.scenario_compiler import compile_scenario, build_chaos_timeline
from sandbox.scenario_models import ScenarioSpec
from sandbox.twin_loop import TwinLoopEngine
from sandbox.memory_system import MemoryPool
from sandbox.world_state import WorldStateManager
from sandbox.models import SimulationMode

SCENARIO_PATH = os.path.join(os.path.dirname(__file__), "..", "config", "scenarios", "code_review_delivery.json")

# 场景角色 → agent 技能（覆盖 taskflow 全部 required_skills）
AGENTS = {
    "dev1": ["coding", "testing"],
    "dev2": ["coding"],
    "rev1": ["code_review", "task_breakdown"],   # 评审员:被授予「结构化代码评审」skill
    "tst1": ["testing"],
    "rel1": ["release_ops", "report_writing"],
}
# 除 code_review 外其余技能熟练度对照两组完全一致,隔离 skill 的净效果
BASE_PROF = {"coding": 0.6, "testing": 0.6, "task_breakdown": 0.6,
             "release_ops": 0.6, "report_writing": 0.6}
CR_BASELINE = 0.45    # 未授予 skill:评审员 code_review 熟练度低(低于场景期望 0.65)
CR_TREATMENT = 0.85   # 授予「结构化代码评审」skill 后的 code_review 熟练度

_spec_dict = json.load(open(SCENARIO_PATH, encoding="utf-8"))
_spec = ScenarioSpec.from_dict(_spec_dict)
_compiled = compile_scenario(_spec, {})


def _run_once(code_review_prof: float, seed: int):
    random.seed(seed)
    ws = WorldStateManager()
    for aid, skills in AGENTS.items():
        ws.sync_agent_state(aid, {"role": "dev", "state": "idle", "skills": skills, "tools": []})
    ws.sync_tasks(_compiled["pending_tasks"])
    if _compiled.get("room_stages"):
        ws.set_room_stages(_compiled["room_stages"])
    if _compiled.get("resources"):
        ws.sync_resources(_compiled["resources"])
    if _compiled.get("constraints"):
        ws.sync_constraints(_compiled["constraints"])

    eng = TwinLoopEngine(ws, MemoryPool())
    sess = eng.create_session(team_id="demo", mode=SimulationMode.WHAT_IF,
                              max_steps=_spec.recommended_max_steps or 130, speed_factor=10000.0)
    eng.set_chaos_timeline(sess.session_id, build_chaos_timeline(_spec))

    priors = {}
    for aid, skills in AGENTS.items():
        priors[aid] = {s: BASE_PROF.get(s, 0.5) for s in skills}
        if "code_review" in skills:
            priors[aid]["code_review"] = code_review_prof
    eng.set_proficiency_priors(sess.session_id, priors)

    asyncio.run(eng.run_simulation(sess.session_id))
    recs = eng.drain_usage_records(sess.session_id)
    total_reward = sum(getattr(st, "global_reward", 0) for st in sess.steps)
    cr = [r for r in recs if r.skill_name == "code_review"]
    cr_ok = sum(1 for r in cr if r.outcome == "success")
    all_ok = sum(1 for r in recs if r.outcome == "success")
    return {
        "total_reward": total_reward,
        "cr_uses": len(cr), "cr_ok": cr_ok,
        "all_uses": len(recs), "all_ok": all_ok,
    }


def _agg(prof, seeds):
    runs = [_run_once(prof, s) for s in seeds]
    cr_uses = sum(r["cr_uses"] for r in runs); cr_ok = sum(r["cr_ok"] for r in runs)
    all_uses = sum(r["all_uses"] for r in runs); all_ok = sum(r["all_ok"] for r in runs)
    return {
        "mean_reward": statistics.mean(r["total_reward"] for r in runs),
        "cr_rate": cr_ok / max(cr_uses, 1),
        "all_rate": all_ok / max(all_uses, 1),
        "cr_uses": cr_uses, "all_uses": all_uses,
    }


def main():
    seeds = list(range(1, 31))  # 30 个固定种子,消除单次随机波动
    base = _agg(CR_BASELINE, seeds)
    treat = _agg(CR_TREATMENT, seeds)
    cr_gain_pp = (treat["cr_rate"] - base["cr_rate"]) * 100
    all_gain_pp = (treat["all_rate"] - base["all_rate"]) * 100

    print("=" * 64)
    print("技能闭环验证:结构化代码评审 skill @ code_review_delivery 场景")
    print(f"  种子数 {len(seeds)} · 场景 taskflow 8 任务 · 评审为瓶颈环节")
    print("-" * 64)
    print(f"{'指标':<22}{'baseline(0.45)':>18}{'treatment(0.85)':>18}")
    print(f"{'code_review 成功率':<22}{base['cr_rate']:>17.1%}{treat['cr_rate']:>18.1%}")
    print(f"{'团队整体成功率':<22}{base['all_rate']:>17.1%}{treat['all_rate']:>18.1%}")
    print(f"{'平均总奖励':<22}{base['mean_reward']:>17.2f}{treat['mean_reward']:>18.2f}")
    print("-" * 64)
    print(f"✅ code_review 能力提升: +{cr_gain_pp:.1f} 个百分点")
    print(f"✅ 团队整体成功率提升: +{all_gain_pp:.1f} 个百分点")
    print("=" * 64)
    # 闭环判据:目标技能成功率显著提升
    ok = treat["cr_rate"] > base["cr_rate"] + 0.05
    print("闭环结论:", "成立 ✅(目标能力显著提升)" if ok else "未达阈值 ❌")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
