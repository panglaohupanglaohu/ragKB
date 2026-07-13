# -*- coding: utf-8 -*-
"""Eco Runtime Config REST API — 仿生生态运行时可配置参数管理.

GET   /api/v1/eco-runtime/config     — 获取全量配置（默认补全后）
GET   /api/v1/eco-runtime/defaults   — 获取内置默认（供"恢复默认"）
PUT   /api/v1/eco-runtime/config     — 部分更新（只覆盖已知 section/键）
POST  /api/v1/eco-runtime/reset      — 恢复全部默认
POST  /api/v1/eco-runtime/analyze    — LLM 分析锦标赛/演练结果，给出洞察
"""
from __future__ import annotations

import asyncio
import logging
from typing import Any, Dict, List

from fastapi import APIRouter
from pydantic import BaseModel

from .runtime.eco_runtime_config import get_eco_runtime_config

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/eco-runtime", tags=["eco-runtime"])


class EcoRuntimeUpdateRequest(BaseModel):
    """部分更新请求：{section: {key: value}}，未知 section/键会被后端忽略。"""
    model_config = {"extra": "allow"}
    mental_state: Dict[str, Any] = {}
    metabolism: Dict[str, Any] = {}
    learning: Dict[str, Any] = {}
    selection: Dict[str, Any] = {}
    mating: Dict[str, Any] = {}


@router.get("/config", summary="获取仿生生态运行时全量参数")
def get_config() -> Dict[str, Any]:
    return get_eco_runtime_config().get_config()


@router.get("/defaults", summary="获取内置默认参数")
def get_defaults() -> Dict[str, Any]:
    return get_eco_runtime_config().get_defaults()


@router.put("/config", summary="部分更新仿生生态运行时参数")
def update_config(req: EcoRuntimeUpdateRequest) -> Dict[str, Any]:
    updates = {k: v for k, v in req.model_dump(exclude_none=True).items() if v}
    return get_eco_runtime_config().update(updates)


@router.post("/reset", summary="恢复全部默认参数")
def reset_config() -> Dict[str, Any]:
    return get_eco_runtime_config().reset()


class HabitatContractFromPlanRequest(BaseModel):
    """从执行计划编译 TaskHabitatContract（v4）."""
    plan: Dict[str, Any] = {}
    plaza_id: str = ""
    discussion_id: str = ""


class HabitatContractFromTasksRequest(BaseModel):
    tasks: List[Dict[str, Any]] = []
    team_id: str = ""  # 可选：拉取该队 agent 基因组作 demand，闭环对齐


@router.post("/habitat-contract/from-plan", summary="计划 → TaskHabitatContract")
def habitat_contract_from_plan(req: HabitatContractFromPlanRequest) -> Dict[str, Any]:
    from sandbox.plan_eco_bridge import (
        compile_plan_to_habitat_contract,
        validate_habitat_contract,
    )
    plan = dict(req.plan or {})
    # 可选：从讨论 structured 计划拉取（兼容不同 store API）
    if not plan.get("steps") and req.plaza_id and req.discussion_id:
        try:
            from agents.execution_plan import load_plan_from_discussion, ExecutionPlan
            disc = None
            try:
                from agents.plaza_store import PlazaStore
                store = PlazaStore()
                get_disc = getattr(store, "get_discussion", None) or getattr(store, "load_discussion", None)
                if callable(get_disc):
                    disc = get_disc(req.discussion_id) if get_disc.__code__.co_argcount <= 2 else get_disc(req.plaza_id, req.discussion_id)
            except Exception:
                disc = None
            if disc is not None:
                ep = load_plan_from_discussion(disc)
                if ep is not None:
                    plan = ep.to_dict()
            if not plan.get("steps"):
                return {"ok": False, "error": "no_structured_plan", "hint": "pass plan.steps in body"}
        except Exception as e:
            logger.warning("from-plan load discussion failed: %s", e)
            return {"ok": False, "error": str(e)}
    if not plan.get("steps"):
        return {"ok": False, "error": "plan has no steps"}
    try:
        contract = compile_plan_to_habitat_contract(plan)
    except Exception as e:
        return {"ok": False, "error": str(e)}
    issues = validate_habitat_contract(contract)
    return {"ok": True, "contract": contract.to_dict(), "issues": issues}


@router.post("/habitat-contract/from-tasks", summary="任务列表 → TaskHabitatContract")
def habitat_contract_from_tasks(req: HabitatContractFromTasksRequest) -> Dict[str, Any]:
    from sandbox.plan_eco_bridge import (
        compile_tasks_to_habitat_contract,
        validate_habitat_contract,
    )
    agent_skills_map: Dict[str, List[str]] = {}
    team_skill_ids: List[str] = []
    team_id = (req.team_id or "").strip()
    if team_id:
        try:
            from agents.api import _team_manager as _tm
            team = _tm.get_team(team_id) if _tm else None
            if team is not None:
                agents = getattr(team, "agents", None) or {}
                if isinstance(agents, dict):
                    for aid, a in agents.items():
                        if isinstance(a, dict):
                            sk = list(a.get("skills") or a.get("skill_ids") or [])
                        else:
                            sk = list(getattr(a, "skills", None) or getattr(a, "skill_ids", None) or [])
                        # skills 可能是 id 列表或对象
                        cleaned = []
                        for s in sk:
                            if isinstance(s, str):
                                cleaned.append(s)
                            elif isinstance(s, dict):
                                cleaned.append(str(s.get("skill_id") or s.get("id") or s.get("name") or ""))
                        cleaned = [c for c in cleaned if c]
                        if cleaned:
                            agent_skills_map[str(aid)] = cleaned
                tskills = getattr(team, "skills", None) or {}
                if isinstance(tskills, dict):
                    for sid, sv in tskills.items():
                        if isinstance(sv, dict):
                            team_skill_ids.append(str(sv.get("skill_id") or sid))
                        else:
                            team_skill_ids.append(str(sid))
        except Exception as e:
            logger.warning("from-tasks team skill load failed: %s", e)
    try:
        contract = compile_tasks_to_habitat_contract(
            list(req.tasks or []),
            agent_skills_map=agent_skills_map or None,
            team_skill_ids=team_skill_ids or None,
        )
    except Exception as e:
        return {"ok": False, "error": str(e)}
    issues = validate_habitat_contract(contract)
    return {
        "ok": True,
        "contract": contract.to_dict(),
        "issues": issues,
        "aligned_agents": list(agent_skills_map.keys()),
    }


class SkillIntegrationSuggestRequest(BaseModel):
    result: Dict[str, Any] = {}
    contract: Dict[str, Any] = {}


class SkillIntegrationApplyRequest(BaseModel):
    team_id: str = ""
    confirm: bool = False
    report: Dict[str, Any] = {}
    feedback_router: bool = False


class DispatchWinnerRequest(BaseModel):
    team_id: str = ""
    agent_id: str = ""
    skill_genome: List[str] = []
    plan_id: str = ""
    topic: str = ""
    fingerprint: str = ""
    survival_ticks: int = 0
    create_task: bool = True


@router.post("/skill-integration/suggest", summary="从演练结果生成 Skill 集成建议（只读）")
def skill_integration_suggest(req: SkillIntegrationSuggestRequest) -> Dict[str, Any]:
    from sandbox.skill_integration import build_integration_report
    report = build_integration_report(req.result or {}, req.contract or {})
    return {"ok": True, "report": report}


@router.post("/skill-integration/apply", summary="写回技能绑定（需 confirm=true）")
def skill_integration_apply(req: SkillIntegrationApplyRequest) -> Dict[str, Any]:
    """默认 suggest_only：confirm=false 只返回 will apply 计数；true 才改 agent.skills."""
    bindings = list((req.report or {}).get("recommended_bindings") or [])
    if not req.team_id:
        return {"ok": False, "error": "team_id required"}
    if not bindings:
        return {"ok": False, "error": "no recommended_bindings"}
    if not req.confirm:
        return {
            "ok": True,
            "applied": 0,
            "would_apply": len(bindings),
            "hint": "pass confirm=true to write agent.skills",
        }
    try:
        from agents.api import _team_manager
    except Exception:
        _team_manager = None
    if _team_manager is None:
        return {"ok": False, "error": "team_manager_not_ready"}
    team = _team_manager.get_team(req.team_id)
    if team is None:
        return {"ok": False, "error": "team_not_found"}
    applied = 0
    audit: List[Dict[str, Any]] = []
    for b in bindings:
        aid = str(b.get("agent_id") or "")
        add_skills = list(b.get("add_skills") or [])
        if not aid or not add_skills:
            continue
        agent = None
        try:
            agent = _team_manager.get_agent(aid)
        except Exception:
            agent = team.get_agent(aid) if hasattr(team, "get_agent") else None
        if agent is None:
            continue
        skills = list(getattr(agent, "skills", None) or [])
        changed = False
        for s in add_skills:
            if s and s not in skills:
                skills.append(s)
                changed = True
        if changed:
            agent.skills = skills
            applied += 1
            audit.append({"agent_id": aid, "add_skills": add_skills, "reason": b.get("reason")})
    # 可选 router 反馈
    if req.feedback_router and applied:
        try:
            from agents.skill_router import get_skill_router
            router = get_skill_router()
            # 尽力调用；接口因版本而异
            fb = getattr(router, "submit_feedback", None) or getattr(router, "record_feedback", None)
            if callable(fb):
                fb(team_id=req.team_id, source="eco_drill", bindings=audit)
        except Exception as e:
            logger.debug("skill_router feedback skipped: %s", e)
    try:
        if hasattr(_team_manager, "save") or hasattr(_team_manager, "persist"):
            save = getattr(_team_manager, "save", None) or getattr(_team_manager, "persist", None)
            if callable(save):
                save()
    except Exception:
        pass
    return {"ok": True, "applied": applied, "audit": audit}


@router.post("/skill-integration/dispatch-winner", summary="按黄金适者创建溯源任务（可选）")
async def skill_integration_dispatch_winner(req: DispatchWinnerRequest) -> Dict[str, Any]:
    if not req.team_id:
        return {"ok": False, "error": "team_id required"}
    if not req.create_task:
        return {"ok": True, "task_id": "", "skipped": True}
    try:
        from agents.api import _submit_internal_task
    except Exception:
        _submit_internal_task = None
    title = f"物竞适者执行: {(req.topic or req.plan_id or req.team_id)[:48]}"
    desc = (
        f"由物竞天择适者构型生成。agent={req.agent_id} survival={req.survival_ticks} "
        f"skills={','.join(req.skill_genome[:12])} plan={req.plan_id} fp={req.fingerprint}"
    )
    metadata = {
        "source": "eco_drill",
        "plan_id": req.plan_id,
        "eco_fingerprint": req.fingerprint,
        "champion_agent_id": req.agent_id,
        "required_skills": list(req.skill_genome or []),
        "survival_ticks": req.survival_ticks,
    }
    if _submit_internal_task is None:
        return {
            "ok": True,
            "task_id": "",
            "draft": {"title": title, "description": desc, "metadata": metadata},
            "hint": "_submit_internal_task unavailable; draft only",
        }
    try:
        task = await _submit_internal_task(
            team_id=req.team_id,
            agent_id=req.agent_id or "",
            title=title,
            description=desc,
            priority=2,
            metadata=metadata,
            auto_start=False,
        )
        tid = getattr(task, "task_id", None) or (task.get("task_id") if isinstance(task, dict) else "")
        return {"ok": True, "task_id": tid or "", "title": title}
    except Exception as e:
        logger.warning("dispatch-winner failed: %s", e)
        return {
            "ok": True,
            "task_id": "",
            "draft": {"title": title, "description": desc, "metadata": metadata},
            "error": str(e),
            "hint": "task engine unavailable; returned draft only",
        }


class EcoAnalysisRequest(BaseModel):
    """锦标赛/演练结果分析请求。"""
    entries: List[Dict[str, Any]] = []     # 锦标赛各队摘要
    env: Dict[str, Any] = {}               # 环境参数
    single_result: Dict[str, Any] = {}     # 单场演练完整结果（非锦标赛时用）


def _build_drill_summary(req: EcoAnalysisRequest) -> str:
    """构建给 LLM 的结构化摘要：T_i 归因 / 基因池 / 协作 / 契约 / 环境。"""
    lines: List[str] = []
    env = req.env or {}
    r = req.single_result or {}

    if req.entries:
        lines.append("【赛制】多队对比 / 锦标赛")
        for i, e in enumerate(req.entries):
            champ = e.get("champ", {}) or {}
            lines.append(
                f"  #{i+1} 队={e.get('name','?')} 均T={e.get('avg',0)} 最长T={e.get('best',0)} "
                f"存活={e.get('alive',0)}/{e.get('total',0)} G={e.get('gens',0)} "
                f"适者={champ.get('agent_id','?')}(T={champ.get('survival_ticks',0)})"
            )
            cg = champ.get("collab_genome") or {}
            if cg:
                lines.append(
                    f"    collab share={cg.get('share_tendency','?')} "
                    f"signal={cg.get('signal_tendency','?')} follow={cg.get('follow_tendency','?')}"
                )
            sg = champ.get("skill_genome") or []
            if sg:
                lines.append(f"    skills={', '.join(str(s) for s in sg[:6])}")
            # 归因（若有）
            if champ.get("attr_skill_share") is not None:
                lines.append(
                    f"    T_i分解 skill={champ.get('attr_skill_share')} "
                    f"collab={champ.get('attr_collab_share')} residual={champ.get('attr_residual_share')} "
                    f"| {champ.get('attr_explain','')}"
                )
    else:
        gens = r.get("generations") or []
        ranking = (r.get("final_ranking") or [])[:8]
        pops = r.get("populations") or []
        race = (r.get("task_goal") or {}).get("race_mode") or env.get("race_mode") or "division"
        lines.append(f"【赛制】{race}  种群={pops or ['单队']}  代={len(gens)}  最长T={r.get('best_survival_ticks',0)}")
        for g in gens:
            drift = g.get("drift") or {}
            lines.append(
                f"  G{g.get('generation')}: living={g.get('living',0)} bestT={g.get('best_survival_ticks',0)} "
                f"avgT={g.get('avg_survival_ticks',0)} births={g.get('births',0)}"
                + (f" drift:{drift.get('removed')}→{drift.get('added')}" if drift else "")
                + (" ratchet↑" if g.get("ratchet_advanced") else "")
            )
        lines.append("【个体排行 · 含 T_i 分解】")
        att = r.get("survival_attribution") or {}
        for x in ranking:
            aid = x.get("agent_id", "?")
            a = att.get(aid) or {}
            sk = x.get("attr_skill_share", a.get("skill_share"))
            co = x.get("attr_collab_share", a.get("collab_share"))
            re = x.get("attr_residual_share", a.get("residual_share"))
            lines.append(
                f"  {aid}@{x.get('population','?')} T={x.get('survival_ticks',0)} "
                f"{'活' if x.get('alive') else '死'} "
                f"skill%={sk} collab%={co} residual%={re} "
                f"genome={','.join(str(s) for s in (x.get('skill_genome') or [])[:4])}"
            )
            if x.get("attr_explain") or a.get("explain"):
                lines.append(f"    判读: {x.get('attr_explain') or a.get('explain')}")

        gp = r.get("gene_pool") or {}
        dom = gp.get("dominant") or []
        dep = gp.get("deprecated") or []
        if dom or dep:
            lines.append("【基因池】")
            if dom:
                lines.append("  dominant: " + ", ".join(
                    f"{d.get('skill')}×{d.get('carriers')}" for d in dom[:8]
                ))
            if dep:
                lines.append("  deprecated: " + ", ".join(
                    str(d.get("skill") if isinstance(d, dict) else d) for d in dep[:8]
                ))

        means = (r.get("collab_profile") or {}).get("means") or {}
        if means:
            lines.append(
                "【幸存者协作均值】 "
                + " ".join(f"{k}={v}" for k, v in list(means.items())[:6])
            )

        integ = r.get("integration") or {}
        if integ:
            sug = integ.get("suggestions") or integ.get("suggest") or []
            if isinstance(sug, list) and sug:
                lines.append("【Skill集成线索】" + str(sug[:3])[:280])
            elif integ.get("summary"):
                lines.append("【Skill集成】" + str(integ.get("summary"))[:200])

        contract = r.get("contract") or {}
        niches = contract.get("niches") or []
        if niches:
            lines.append("【任务生境契约·生态位】")
            for n in niches[:6]:
                lines.append(
                    f"  · {(n.get('title') or '')[:36]} demand={n.get('demanded_skills') or []}"
                )

    # 环境语义
    lines.append(
        f"【客观环境】demand={env.get('demanded_skills', env.get('demand', '?'))} "
        f"丰饶(abundance/token松紧)={env.get('abundance','?')} "
        f"捕食(事故压)={env.get('predator_pressure','?')} "
        f"漂移(需求变更)={env.get('drift_prob','?')} "
        f"名额={env.get('niche_capacity','?')}"
    )
    note = r.get("survival_attribution_note") or ""
    if note:
        lines.append(f"【归因约定】{note[:240]}")
    return "\n".join(lines)


@router.post("/analyze", summary="LLM 分析演练结果，给出洞察型报告")
async def analyze_drill(req: EcoAnalysisRequest) -> Dict[str, Any]:
    """用 LLM 分析物竞天择演练结果，给出有洞察力的分析报告。"""
    summary = _build_drill_summary(req)

    prompt = (
        "你是 AgentsGroup 数字孪生实验室的进化分析师。用户已看到排行榜数字；"
        "你的任务是判断两件事并写可执行结论：\n"
        "A) 当前系统是否在让 **Skill 进化**（dominant/deprecated、skill% 归因、契约 demand 是否匹配 genome）？\n"
        "B) 当前系统是否在找到 **团队演化方式**（协作基因 share/signal/follow、多队对比、混合纪元）？\n\n"
        "硬约束：\n"
        "- 唯一适应度是生存时长 T_i，禁止发明第二评分。\n"
        "- 任务/契约是客观环境（同一考卷过滤），不是「天选任务」。\n"
        "- 分场=多队比个体 skill；对抗=比协作策略；混合=个体+团队。\n"
        "- 若 skill%≈0 且 residual 主导：明确指出「环境 demand 与 agent genome 未对齐」或「选择压力太弱」，并给下一步（补 required_skills / 对齐 agent 技能 / 提高步数世代）。\n"
        "- 若 dominant 技能与任务生态位一致：说明 Skill 进化闭环有效。\n"
        "- 若 collab% 高且幸存者 share/signal 偏移：说明团队协作方式被选择。\n\n"
        "输出结构（中文，400~700 字，禁止空话）：\n"
        "1. **因果**：谁赢了、因为 skill 还是协作还是苟活残差\n"
        "2. **Skill 进化判定**：能 / 弱 / 不能 + 证据（dominant/deprecated/归因）\n"
        "3. **团队演化判定**：能 / 弱 / 不能 + 证据（协作基因组、多队差距）\n"
        "4. **下一局旋钮**：改 abundance/predator/drift 或契约 skills 的 2~3 条具体建议\n"
        "5. **一句话**：这个环境在选择什么样的 Agent/团队\n\n"
        "=== 演练结构化数据 ===\n"
        + summary
    )

    # 无 LLM 时的确定性兜底分析（仍比旧「未连接」有用）
    def _fallback(reason: str) -> Dict[str, Any]:
        r = req.single_result or {}
        ranking = (r.get("final_ranking") or [])[:3]
        att = r.get("survival_attribution") or {}
        gp = r.get("gene_pool") or {}
        dom = [d.get("skill") for d in (gp.get("dominant") or [])[:5] if isinstance(d, dict)]
        skill_means = []
        collab_means = []
        for x in ranking:
            a = att.get(x.get("agent_id") or "") or {}
            sk = x.get("attr_skill_share", a.get("skill_share"))
            co = x.get("attr_collab_share", a.get("collab_share"))
            if sk is not None:
                skill_means.append(float(sk))
            if co is not None:
                collab_means.append(float(co))
        avg_sk = sum(skill_means) / len(skill_means) if skill_means else 0.0
        avg_co = sum(collab_means) / len(collab_means) if collab_means else 0.0
        if avg_sk >= 0.25 and dom:
            skill_verdict = "能（弱→中）：适者 skill 归因可见，且 gene_pool 出现 dominant"
        elif avg_sk >= 0.1 or dom:
            skill_verdict = "弱：有 dominant 或少量 skill 归因，但选择压力不足"
        else:
            skill_verdict = "弱/不能：T_i 主因偏 residual，demand 与 genome 可能未对齐"
        if avg_co >= 0.2:
            team_verdict = "能（弱→中）：协作归因占生存显著份额"
        elif req.entries and len(req.entries) >= 2:
            team_verdict = "弱：多队已对比，但需看均 T 差距与 collab 基因分化"
        else:
            team_verdict = "弱：单队或协作信号不足，需对抗/混合赛制加对比种群"
        text = (
            f"（结构化兜底 · {reason}）\n"
            f"1. 因果：Top 适者={(ranking[0].get('agent_id') if ranking else '?')}；"
            f"Top3 均 skill%≈{avg_sk:.0%} collab%≈{avg_co:.0%}；dominant={dom or '无'}\n"
            f"2. Skill 进化判定：{skill_verdict}\n"
            f"3. 团队演化判定：{team_verdict}\n"
            f"4. 下一局旋钮：① from-tasks 带 team_id 对齐 agent 技能；② 提高 max_steps/gens；"
            f"③ 扫描 abundance↓ + predator↑ 加压，观察 dominant 是否稳定\n"
            f"5. 一句话：环境在选择「能在当前 demand 下活得更久的 skill+协作组合」，"
            f"而非人工打分。\n\n--- 数据摘要 ---\n{summary[:1200]}"
        )
        return {"analysis": text, "ok": False, "fallback": True, "summary": summary}

    try:
        from .chat_harness import get_chat_harness
        harness = get_chat_harness()
        result = await asyncio.wait_for(harness.chat(prompt), timeout=90.0)
        text = ""
        if hasattr(result, "response"):
            text = (result.response or "").strip()
        elif isinstance(result, str):
            text = result.strip()
        if hasattr(result, "error") and result.error:
            fb = _fallback(f"LLM error: {result.error}")
            fb["analysis"] = f"（LLM 错误：{result.error}）\n\n" + fb["analysis"]
            return fb
        if text and "LLM 未连接" not in text and "收到您的消息" not in text:
            return {"analysis": text, "ok": True, "summary": summary}
        return _fallback("LLM 未连接或返回空")
    except asyncio.TimeoutError:
        return _fallback("LLM 超时 90s")
    except Exception as e:
        logger.warning("eco analyze failed: %s", e)
        return _fallback(str(e))
