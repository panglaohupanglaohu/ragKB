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
from typing import Any, Dict, List, Optional

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
    habitat: Dict[str, Any] = {}
    drill_economics: Dict[str, Any] = {}
    selection: Dict[str, Any] = {}
    mating: Dict[str, Any] = {}
    era: Dict[str, Any] = {}
    task_coupling: Dict[str, Any] = {}
    evolution_pressure: Dict[str, Any] = {}
    llm_analysis: Dict[str, Any] = {}


@router.get("/config", summary="获取仿生生态运行时全量参数")
def get_config() -> Dict[str, Any]:
    return get_eco_runtime_config().get_config()


@router.get("/defaults", summary="获取内置默认参数")
def get_defaults() -> Dict[str, Any]:
    return get_eco_runtime_config().get_defaults()


@router.put("/config", summary="部分更新仿生生态运行时参数")
def update_config(req: EcoRuntimeUpdateRequest) -> Dict[str, Any]:
    # 保留 0 / False；只跳过空 dict / None
    raw = req.model_dump(exclude_none=True)
    updates = {
        k: v for k, v in raw.items()
        if not (isinstance(v, dict) and len(v) == 0)
    }
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
    team_id: str = ""  # 可选：注入真身绑定 + 储备池，只推荐未绑定 skill


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


def _team_bound_and_reserve(team_id: str) -> Dict[str, Any]:
    """读取团队真身已绑定 skills + 分类储备池 + 团队技能库 id."""
    agent_bound: Dict[str, List[str]] = {}
    team_skill_ids: List[str] = []
    reserve_ids: List[str] = []
    try:
        from agents.api import _team_manager
        team = _team_manager.get_team(team_id) if _team_manager else None
        if team is not None:
            if getattr(team, "skills", None):
                team_skill_ids = list(team.skills.keys())
            agents = team.agents.values() if isinstance(team.agents, dict) else (team.agents or [])
            for a in agents:
                aid = str(getattr(a, "agent_id", "") or "")
                if not aid:
                    continue
                agent_bound[aid] = [str(s) for s in (getattr(a, "skills", None) or [])]
    except Exception as e:
        logger.debug("team bound load: %s", e)
    try:
        from agents.skill_classifier import get_classification_store
        view = get_classification_store().get_view(team_id) or {}
        pools = view.get("pools") if isinstance(view, dict) else {}
        reserve_list = (pools or {}).get("reserve") or []
        for item in reserve_list:
            if isinstance(item, dict):
                sid = item.get("skill_id") or item.get("id") or item.get("skill")
            else:
                sid = item
            if sid:
                reserve_ids.append(str(sid))
    except Exception as e:
        logger.debug("reserve pool load: %s", e)
    return {
        "agent_bound_skills": agent_bound,
        "team_skill_ids": team_skill_ids,
        "reserve_skill_ids": reserve_ids,
    }


@router.post("/skill-integration/suggest", summary="从演练结果生成 Skill 集成建议（只读）")
def skill_integration_suggest(req: SkillIntegrationSuggestRequest) -> Dict[str, Any]:
    from sandbox.skill_integration import build_integration_report
    kwargs: Dict[str, Any] = {}
    tid = (req.team_id or "").strip()
    if tid:
        kwargs.update(_team_bound_and_reserve(tid))
    report = build_integration_report(req.result or {}, req.contract or {}, **kwargs)
    return {"ok": True, "report": report, "enriched_with_team": bool(tid)}


def _resolve_team_agent(team_manager: Any, team: Any, team_id: str, aid: str) -> Any:
    """解析物竞 ranking 的 agent_id → 真身 AgentProfile.

    常见失败：get_agent 单参签名不匹配；繁衍后代 id 不在 teams 里。
    """
    agent = None
    try:
        agent = team_manager.get_agent(team_id, aid)
    except TypeError:
        try:
            agent = team_manager.get_agent(aid)  # type: ignore[misc]
        except Exception:
            agent = None
    except Exception:
        agent = None
    if agent is None and team is not None and hasattr(team, "get_agent"):
        try:
            agent = team.get_agent(aid)
        except Exception:
            agent = None
    if agent is not None:
        return agent
    # 模糊：前缀 / 名字 / 去掉孪生后缀
    try:
        agents = []
        if team is not None and hasattr(team, "agents"):
            ag = team.agents
            agents = list(ag.values()) if hasattr(ag, "values") else list(ag or [])
        aid_l = aid.lower()
        for a in agents:
            aa = str(getattr(a, "agent_id", "") or "")
            an = str(getattr(a, "name", "") or "")
            if not aa and not an:
                continue
            if (
                aa == aid
                or aid.startswith(aa)
                or aa.startswith(aid[:8])
                or aid_l == an.lower()
                or an.lower() in aid_l
                or aid_l in an.lower()
            ):
                return a
    except Exception:
        pass
    return None


@router.post("/skill-integration/apply", summary="写回技能绑定（需 confirm=true）")
def skill_integration_apply(req: SkillIntegrationApplyRequest) -> Dict[str, Any]:
    """默认 suggest_only：confirm=false 只返回 will apply 计数；true 才改 agent.skills.

    返回字段：
    - applied: 实际发生技能变更的 **agent 数**
    - skills_added: 新增 skill 条数合计
    - audit: 每条绑定的结果（applied / already_present / agent_not_found）
    """
    bindings = list((req.report or {}).get("recommended_bindings") or [])
    if not req.team_id:
        return {"ok": False, "error": "team_id required"}
    if not bindings:
        return {"ok": False, "error": "no recommended_bindings"}
    if not req.confirm:
        skill_n = sum(len(b.get("add_skills") or []) for b in bindings)
        return {
            "ok": True,
            "applied": 0,
            "would_apply": len(bindings),
            "would_add_skills": skill_n,
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
    skills_added = 0
    audit: List[Dict[str, Any]] = []
    for b in bindings:
        aid = str(b.get("agent_id") or "")
        add_skills = [s for s in (b.get("add_skills") or []) if s]
        if not aid or not add_skills:
            audit.append({"agent_id": aid, "status": "empty", "add_skills": add_skills})
            continue
        agent = _resolve_team_agent(_team_manager, team, req.team_id, aid)
        if agent is None:
            audit.append({
                "agent_id": aid,
                "status": "agent_not_found",
                "add_skills": add_skills,
                "hint": "孪生后代 id 或未匹配真身；请选初代适者（原团队 agent_id）",
            })
            continue
        skills = list(getattr(agent, "skills", None) or [])
        skill_set = set(str(x) for x in skills)
        newly: List[str] = []
        for s in add_skills:
            ss = str(s)
            if ss not in skill_set:
                skills.append(ss)
                skill_set.add(ss)
                newly.append(ss)
        if newly:
            agent.skills = skills
            applied += 1
            skills_added += len(newly)
            audit.append({
                "agent_id": getattr(agent, "agent_id", aid),
                "status": "applied",
                "added": newly,
                "skipped_already": [s for s in add_skills if str(s) not in newly],
                "reason": b.get("reason"),
            })
        else:
            audit.append({
                "agent_id": getattr(agent, "agent_id", aid),
                "status": "already_present",
                "add_skills": add_skills,
                "hint": "所选 skill 均已在 agent.skills 中，无需重复写入",
            })
    # 可选 router 反馈
    if req.feedback_router and applied:
        try:
            from agents.skill_router import get_skill_router
            router = get_skill_router()
            fb = getattr(router, "submit_feedback", None) or getattr(router, "record_feedback", None)
            if callable(fb):
                fb(team_id=req.team_id, source="eco_drill", bindings=audit)
        except Exception as e:
            logger.debug("skill_router feedback skipped: %s", e)
    try:
        if hasattr(_team_manager, "_persist") and callable(getattr(_team_manager, "_persist")):
            _team_manager._persist()
        else:
            save = getattr(_team_manager, "save", None) or getattr(_team_manager, "persist", None)
            if callable(save):
                save()
    except Exception:
        pass
    hint = ""
    if applied == 0 and audit:
        statuses = [a.get("status") for a in audit]
        if all(s == "already_present" for s in statuses if s):
            hint = "所选 skill 均已绑定，applied=0 属正常"
        elif any(s == "agent_not_found" for s in statuses):
            hint = "未能匹配真身 agent（常见于繁衍后代 id）；请勾选初代成员"
        else:
            hint = "无技能变更；见 audit"
    return {
        "ok": True,
        "applied": applied,
        "skills_added": skills_added,
        "audit": audit,
        "hint": hint,
    }


class CollabIntegrationSuggestRequest(BaseModel):
    result: Dict[str, Any] = {}
    top_k: int = 12
    default_strategy: str = "blend"


class CollabIntegrationApplyRequest(BaseModel):
    team_id: str = ""
    confirm: bool = False
    suggestions: List[Dict[str, Any]] = []
    fingerprint: str = ""
    strategy: str = ""  # 可选全局覆盖：overwrite|blend|snapshot


@router.post("/collab-integration/suggest", summary="从演练结果生成协作模式建议（只读）")
def collab_integration_suggest(req: CollabIntegrationSuggestRequest) -> Dict[str, Any]:
    from sandbox.collab_integration import build_collab_suggestions
    report = build_collab_suggestions(
        req.result or {},
        top_k=int(req.top_k or 12),
        default_strategy=req.default_strategy or "blend",
    )
    return {"ok": True, "report": report}


@router.post("/collab-integration/apply", summary="写回协作模式到 agent.metadata.eco_collab（需 confirm=true）")
def collab_integration_apply(req: CollabIntegrationApplyRequest) -> Dict[str, Any]:
    """confirm=false 仅预览；true 写入 AgentProfile.metadata.eco_collab 并持久化."""
    from sandbox.collab_integration import materialize_collab_payload

    suggestions = list(req.suggestions or [])
    if not req.team_id:
        return {"ok": False, "error": "team_id required"}
    if not suggestions:
        return {"ok": False, "error": "no suggestions"}
    if not req.confirm:
        return {
            "ok": True,
            "applied": 0,
            "would_apply": len(suggestions),
            "hint": "pass confirm=true to write metadata.eco_collab",
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

    def _resolve_agent(aid: str):
        agent = None
        try:
            agent = _team_manager.get_agent(req.team_id, aid)
        except TypeError:
            try:
                agent = _team_manager.get_agent(aid)  # type: ignore[misc]
            except Exception:
                agent = None
        except Exception:
            agent = None
        if agent is None and hasattr(team, "get_agent"):
            agent = team.get_agent(aid)
        if agent is None:
            # 孪生 id / 名前缀模糊匹配
            try:
                agents = list(team.agents.values()) if hasattr(team, "agents") and hasattr(team.agents, "values") else []
                for a in agents:
                    aa = str(getattr(a, "agent_id", "") or "")
                    an = str(getattr(a, "name", "") or "")
                    if aa == aid or aid.startswith(aa) or aa.startswith(aid[:8]) or aid in an or an in aid:
                        return a
            except Exception:
                pass
        return agent

    applied = 0
    audit: List[Dict[str, Any]] = []
    global_strategy = (req.strategy or "").strip()
    for s in suggestions:
        aid = str(s.get("agent_id") or "")
        if not aid:
            continue
        agent = _resolve_agent(aid)
        if agent is None:
            audit.append({"agent_id": aid, "error": "agent_not_found"})
            continue
        meta = dict(getattr(agent, "metadata", None) or {})
        payload = materialize_collab_payload(
            s,
            existing_meta=meta,
            fingerprint=req.fingerprint or "",
            strategy_override=global_strategy or None,
        )
        meta["eco_collab"] = payload
        agent.metadata = meta
        applied += 1
        real_aid = str(getattr(agent, "agent_id", aid) or aid)
        audit.append({"agent_id": real_aid, "eco_collab": payload})
        # 拟生记忆：物竞存活写回 → EventBus → fitness/拓扑漂移
        try:
            from agents.agent_memory_runtime import emit_eco_survival

            surv = payload.get("survival_ticks")
            if surv is None and isinstance(payload.get("survival_attribution"), dict):
                surv = payload["survival_attribution"].get("survival_ticks")
            emit_eco_survival(
                req.team_id,
                real_aid,
                survival_ticks=float(surv or 0),
                metadata={"eco_fp": payload.get("eco_fp") or payload.get("fingerprint") or ""},
            )
        except Exception as e:
            logger.debug("eco survival emit skip: %s", e)

    try:
        if hasattr(_team_manager, "_persist") and callable(getattr(_team_manager, "_persist")):
            _team_manager._persist()
        elif hasattr(_team_manager, "save") and callable(getattr(_team_manager, "save")):
            _team_manager.save()
    except Exception as e:
        logger.debug("collab apply persist: %s", e)

    return {"ok": True, "applied": applied, "audit": audit}


class ChannelIntegrationSuggestRequest(BaseModel):
    result: Dict[str, Any] = {}
    timeline: Optional[Dict[str, Any]] = None
    team_id: str = ""
    top_k: int = 12
    bus_name: str = ""


class ChannelIntegrationApplyRequest(BaseModel):
    team_id: str = ""
    confirm: bool = False
    suggestions: List[Dict[str, Any]] = []
    fingerprint: str = ""


@router.post("/channel-integration/suggest", summary="从演练结果生成通道绑定建议（只读）")
def channel_integration_suggest(req: ChannelIntegrationSuggestRequest) -> Dict[str, Any]:
    from sandbox.channel_integration import build_channel_suggestions

    agent_channels: Dict[str, List[Dict[str, Any]]] = {}
    if req.team_id:
        try:
            from agents.api import _team_manager
            team = _team_manager.get_team(req.team_id) if _team_manager else None
            if team is not None and hasattr(team, "agents"):
                agents = team.agents.values() if hasattr(team.agents, "values") else []
                for a in agents:
                    aid = str(getattr(a, "agent_id", "") or "")
                    chs = []
                    for c in getattr(a, "channels", None) or []:
                        if hasattr(c, "to_dict"):
                            chs.append(c.to_dict())
                        elif isinstance(c, dict):
                            chs.append(c)
                    if aid:
                        agent_channels[aid] = chs
        except Exception as e:
            logger.debug("channel suggest load agents: %s", e)

    report = build_channel_suggestions(
        req.result or {},
        team_id=req.team_id or "",
        timeline=req.timeline,
        agent_channels=agent_channels,
        top_k=int(req.top_k or 12),
        bus_name=req.bus_name or "",
    )
    return {"ok": True, "report": report}


@router.post("/channel-integration/apply", summary="合并写回 agent.channels（需 confirm=true）")
def channel_integration_apply(req: ChannelIntegrationApplyRequest) -> Dict[str, Any]:
    """confirm=false 仅预览；true 合并 diff 并 _persist。"""
    from agents.agent_channel_bus import apply_bindings_to_agent, list_channel_bindings, merge_channel_bindings

    suggestions = list(req.suggestions or [])
    if not req.team_id:
        return {"ok": False, "error": "team_id required"}
    if not suggestions:
        return {"ok": False, "error": "no suggestions"}
    if not req.confirm:
        n_diff = sum(len(s.get("channel_diffs") or []) for s in suggestions)
        return {
            "ok": True,
            "applied": 0,
            "would_apply": len(suggestions),
            "would_diff": n_diff,
            "hint": "pass confirm=true to merge agent.channels",
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

    def _resolve_agent(aid: str):
        agent = None
        try:
            agent = _team_manager.get_agent(req.team_id, aid)
        except TypeError:
            try:
                agent = _team_manager.get_agent(aid)  # type: ignore[misc]
            except Exception:
                agent = None
        except Exception:
            agent = None
        if agent is None and hasattr(team, "get_agent"):
            agent = team.get_agent(aid)
        if agent is None:
            try:
                agents = list(team.agents.values()) if hasattr(team, "agents") and hasattr(team.agents, "values") else []
                for a in agents:
                    aa = str(getattr(a, "agent_id", "") or "")
                    an = str(getattr(a, "name", "") or "")
                    if aa == aid or aid.startswith(aa) or aa.startswith(aid[:8]) or aid in an or an in aid:
                        return a
            except Exception:
                pass
        return agent

    applied = 0
    audit: List[Dict[str, Any]] = []
    for s in suggestions:
        aid = str(s.get("agent_id") or "")
        diffs = list(s.get("channel_diffs") or [])
        if not aid or not diffs:
            continue
        # 标记物竞来源
        for d in diffs:
            if isinstance(d, dict):
                d.setdefault("source", "eco_drill")
                if req.fingerprint:
                    d["note"] = (str(d.get("note") or "") + f" fp:{req.fingerprint[:12]}").strip()
        agent = _resolve_agent(aid)
        if agent is None:
            audit.append({"agent_id": aid, "error": "agent_not_found"})
            continue
        existing = list_channel_bindings(agent)
        merged = merge_channel_bindings(existing, diffs)
        apply_bindings_to_agent(agent, merged)
        applied += 1
        audit.append({
            "agent_id": getattr(agent, "agent_id", aid),
            "channels": merged,
            "status": "applied",
        })

    try:
        if hasattr(_team_manager, "_persist") and callable(getattr(_team_manager, "_persist")):
            _team_manager._persist()
        elif hasattr(_team_manager, "save") and callable(getattr(_team_manager, "save")):
            _team_manager.save()
    except Exception as e:
        logger.debug("channel apply persist: %s", e)

    return {"ok": True, "applied": applied, "audit": audit}


class RelationIntegrationSuggestRequest(BaseModel):
    result: Dict[str, Any] = {}
    timeline: Optional[Dict[str, Any]] = None
    team_id: str = ""
    top_k: int = 24
    min_weight: float = 1.0
    bidirectional_share: bool = True


class RelationIntegrationApplyRequest(BaseModel):
    team_id: str = ""
    confirm: bool = False
    suggestions: List[Dict[str, Any]] = []
    fingerprint: str = ""


@router.post("/relation-integration/suggest", summary="从演练结果生成关系边建议（只读）")
def relation_integration_suggest(req: RelationIntegrationSuggestRequest) -> Dict[str, Any]:
    from sandbox.relation_integration import build_relation_suggestions

    existing_edges: List[Dict[str, Any]] = []
    agent_channels: Dict[str, List[Dict[str, Any]]] = {}
    agent_ids: List[str] = []
    if req.team_id:
        try:
            from agents.agent_relationships import get_relationship_store
            store = get_relationship_store()
            existing_edges = [r.to_dict() for r in store.list_team(req.team_id)]
        except Exception as e:
            logger.debug("relation suggest load edges: %s", e)
        # 加载通道绑定 + 队员 id → Before 软边（aws-ops 全员 aws_ops_bus 即此来源）
        try:
            from agents.api import _team_manager
            team = _team_manager.get_team(req.team_id) if _team_manager else None
            if team is not None and hasattr(team, "agents"):
                agents = team.agents.values() if hasattr(team.agents, "values") else []
                for a in agents:
                    aid = str(getattr(a, "agent_id", "") or "")
                    if not aid:
                        continue
                    agent_ids.append(aid)
                    chs: List[Dict[str, Any]] = []
                    for c in getattr(a, "channels", None) or []:
                        if hasattr(c, "to_dict"):
                            chs.append(c.to_dict())
                        elif isinstance(c, dict):
                            chs.append(c)
                    agent_channels[aid] = chs
        except Exception as e:
            logger.debug("relation suggest load agents/channels: %s", e)

    report = build_relation_suggestions(
        req.result or {},
        team_id=req.team_id or "",
        timeline=req.timeline,
        existing_edges=existing_edges,
        agent_channels=agent_channels,
        agent_ids=agent_ids,
        top_k=int(req.top_k or 24),
        min_weight=float(req.min_weight if req.min_weight is not None else 1.0),
        bidirectional_share=bool(req.bidirectional_share),
    )
    return {"ok": True, "report": report}


@router.post("/relation-integration/apply", summary="写入关系边（需 confirm=true）")
def relation_integration_apply(req: RelationIntegrationApplyRequest) -> Dict[str, Any]:
    """confirm=false 仅预览；true 才 RelationshipStore.add。

    关系只能由人工确认建立（created_by=human_via_eco_feedback）；mate 不进此接口。
    """
    from agents.agent_relationships import AgentRelationship, get_relationship_store
    from sandbox.relation_integration import materialize_relation

    suggestions = list(req.suggestions or [])
    if not req.team_id:
        return {"ok": False, "error": "team_id required"}
    if not suggestions:
        return {"ok": False, "error": "no suggestions"}
    if not req.confirm:
        return {
            "ok": True,
            "applied": 0,
            "would_apply": len(suggestions),
            "hint": "pass confirm=true to write RelationshipStore",
        }

    store = get_relationship_store()
    applied = 0
    skipped_dup = 0
    audit: List[Dict[str, Any]] = []
    for s in suggestions:
        payload = materialize_relation(
            s if isinstance(s, dict) else {},
            team_id=req.team_id,
            fingerprint=req.fingerprint or "",
        )
        if not payload.get("source_agent_id") or not payload.get("target_id"):
            audit.append({"error": "missing_source_or_target", "raw": s})
            continue
        rel = AgentRelationship(
            team_id=payload["team_id"],
            kind=payload["kind"],
            source_agent_id=payload["source_agent_id"],
            target_id=payload["target_id"],
            rel_type=payload["rel_type"],
            note=payload["note"],
            created_by=payload["created_by"],
        )
        result = store.add(rel)
        if result.get("ok"):
            applied += 1
            audit.append({
                "rel_id": result.get("rel_id") or rel.rel_id,
                "source_agent_id": rel.source_agent_id,
                "target_id": rel.target_id,
                "status": "applied",
            })
        elif result.get("error") == "duplicate":
            skipped_dup += 1
            audit.append({
                "source_agent_id": rel.source_agent_id,
                "target_id": rel.target_id,
                "status": "already_exists",
                "existing_rel_id": result.get("existing_rel_id"),
            })
        else:
            audit.append({
                "source_agent_id": rel.source_agent_id,
                "target_id": rel.target_id,
                "status": "error",
                "error": result.get("error"),
            })

    return {
        "ok": True,
        "applied": applied,
        "skipped_dup": skipped_dup,
        "audit": audit,
    }


# ── BidCandidate：物竞 × 成本竞标（先适者后省钱）────────────────

class BidCandidateCreateRequest(BaseModel):
    team_id: str = ""
    result: Dict[str, Any] = {}
    feedback: Dict[str, Any] = {}
    task_id: str = ""
    plan_id: str = ""
    race_mode: str = ""
    allow_without_task: bool = False  # 仅调试；默认拒绝无 task 推送


class BidCandidatePatchRequest(BaseModel):
    tokens_baseline: Optional[float] = None
    tokens_candidate: Optional[float] = None
    token_efficiency: Optional[float] = None
    cost_gate: str = ""
    ratchet_state: str = ""
    feedback_status: str = ""
    skip_reason: str = ""
    skill_applied: Optional[bool] = None
    collab_applied: Optional[bool] = None
    channel_applied: Optional[bool] = None
    relation_applied: Optional[bool] = None
    task_id: str = ""
    plan_id: str = ""
    note: str = ""


class BidCandidateQualityRequest(BaseModel):
    thresholds: Dict[str, Any] = {}


@router.post("/bid-candidates", summary="从物竞结果+反馈创建成本竞标候选")
def bid_candidate_create(req: BidCandidateCreateRequest) -> Dict[str, Any]:
    """Q1 默认要求 task_id；Q2 要求 feedback done|skipped。"""
    from sandbox.bid_candidate import build_candidate_from_result, save_candidate

    team_id = (req.team_id or "").strip()
    if not team_id:
        return {"ok": False, "error": "team_id required"}
    feedback = dict(req.feedback or {})
    task_id = (req.task_id or feedback.get("task_id") or "").strip()
    # 尝试从 result.contract 取 task
    contract = (req.result or {}).get("contract") or {}
    if not task_id:
        task_id = str(contract.get("task_id") or "").strip()
    if not task_id and not req.allow_without_task:
        return {
            "ok": False,
            "error": "task_id required",
            "hint": "任务主闭环：须挂接业务场景实例后再推送成本竞标（空跑不可静默进成本）",
        }
    fb_status = feedback.get("feedback") or feedback.get("status") or ""
    if not fb_status:
        if feedback.get("skipped"):
            fb_status = "skipped"
        elif any(feedback.get(k) for k in (
            "skill_applied", "collab_applied", "channel_applied", "relation_applied",
        )):
            fb_status = "done"
    if fb_status not in ("done", "skipped"):
        return {
            "ok": False,
            "error": "feedback required",
            "hint": "请先在 ③ 完成写回或显式跳过并填原因",
        }
    if fb_status == "skipped" and not str(feedback.get("reason") or feedback.get("skip_reason") or "").strip():
        return {"ok": False, "error": "skip_reason required", "hint": "跳过写回须填写原因"}

    feedback["feedback"] = fb_status
    doc = build_candidate_from_result(
        team_id=team_id,
        result=req.result or {},
        feedback=feedback,
        task_id=task_id,
        plan_id=req.plan_id or "",
        race_mode=req.race_mode or "",
    )
    save_candidate(doc)
    return {
        "ok": True,
        "candidate": doc,
        "quality_status": doc.get("quality_status"),
        "quality_reasons": doc.get("quality_reasons") or [],
    }


@router.get("/bid-candidates", summary="列出物竞成本竞标候选")
def bid_candidate_list(
    team_id: str = "",
    task_id: str = "",
    limit: int = 50,
) -> Dict[str, Any]:
    from sandbox.bid_candidate import list_candidates

    items = list_candidates(team_id=team_id, task_id=task_id, limit=int(limit or 50))
    return {"ok": True, "candidates": items, "count": len(items)}


@router.get("/bid-candidates/{candidate_id}", summary="获取单个候选")
def bid_candidate_get(candidate_id: str, team_id: str = "") -> Dict[str, Any]:
    from sandbox.bid_candidate import list_candidates, load_candidate

    if team_id:
        doc = load_candidate(team_id, candidate_id)
    else:
        doc = None
        for c in list_candidates(limit=200):
            if c.get("candidate_id") == candidate_id:
                doc = c
                break
    if not doc:
        return {"ok": False, "error": "not_found"}
    return {"ok": True, "candidate": doc}


@router.patch("/bid-candidates/{candidate_id}", summary="更新候选 token/棘轮字段")
def bid_candidate_patch(candidate_id: str, req: BidCandidatePatchRequest, team_id: str = "") -> Dict[str, Any]:
    from sandbox.bid_candidate import list_candidates, patch_candidate

    tid = (team_id or "").strip()
    if not tid:
        for c in list_candidates(limit=200):
            if c.get("candidate_id") == candidate_id:
                tid = str(c.get("team_id") or "")
                break
    if not tid:
        return {"ok": False, "error": "team_id required or candidate not found"}
    raw = req.model_dump(exclude_none=True)
    updates = {k: v for k, v in raw.items() if v != "" and v is not None}
    doc = patch_candidate(tid, candidate_id, updates)
    if not doc:
        return {"ok": False, "error": "not_found"}
    return {"ok": True, "candidate": doc}


@router.post("/bid-candidates/{candidate_id}/quality-check", summary="重算质量门 Q1–Q5")
def bid_candidate_quality(
    candidate_id: str,
    req: BidCandidateQualityRequest,
    team_id: str = "",
) -> Dict[str, Any]:
    from sandbox.bid_candidate import apply_quality_check, list_candidates, load_candidate, save_candidate

    tid = (team_id or "").strip()
    doc = load_candidate(tid, candidate_id) if tid else None
    if not doc:
        for c in list_candidates(limit=200):
            if c.get("candidate_id") == candidate_id:
                doc = c
                tid = str(c.get("team_id") or "")
                break
    if not doc:
        return {"ok": False, "error": "not_found"}
    doc = apply_quality_check(doc, thresholds=req.thresholds or {})
    save_candidate(doc)
    return {
        "ok": True,
        "candidate": doc,
        "quality_status": doc.get("quality_status"),
        "quality_checks": doc.get("quality_checks"),
        "quality_reasons": doc.get("quality_reasons"),
    }


@router.post("/bid-candidates/{candidate_id}/lock", summary="成本棘轮锁定（须 quality_passed）")
def bid_candidate_lock(candidate_id: str, team_id: str = "") -> Dict[str, Any]:
    from sandbox.bid_candidate import list_candidates, try_lock_candidate

    tid = (team_id or "").strip()
    if not tid:
        for c in list_candidates(limit=200):
            if c.get("candidate_id") == candidate_id:
                tid = str(c.get("team_id") or "")
                break
    if not tid:
        return {"ok": False, "error": "team_id required or candidate not found"}
    return try_lock_candidate(tid, candidate_id)


@router.get("/bid-candidates-locked", summary="生产用：读取 team/task 下 locked 候选")
def bid_candidates_locked(team_id: str = "", task_id: str = "", limit: int = 10) -> Dict[str, Any]:
    """XC-4.4 生产路径查询入口。"""
    from sandbox.bid_candidate import list_locked_candidates, resolve_production_config

    if not (team_id or "").strip():
        return {"ok": False, "error": "team_id required"}
    items = list_locked_candidates(team_id, task_id=task_id or "", limit=int(limit or 10))
    cfg = resolve_production_config(team_id, task_id=task_id or "")
    return {
        "ok": True,
        "locked": items,
        "count": len(items),
        "production": cfg,
        "policy": "先适者后省钱：仅 ratchet_state=locked 进入生产默认构型",
    }


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


def _compose_analysis_prompt(summary: str) -> tuple[str, Dict[str, Any]]:
    """从 eco_runtime_config.llm_analysis 组装提示词（pet-config 可编辑）。"""
    cfg = get_eco_runtime_config().get_section("llm_analysis")
    preamble = str(cfg.get("system_preamble") or "").strip()
    constraints = str(cfg.get("hard_constraints") or "").strip()
    structure = str(cfg.get("output_structure") or "").strip()
    header = str(cfg.get("data_header") or "=== 演练结构化数据 ===").strip()
    parts = [p for p in (preamble, constraints, structure, header) if p]
    prompt = "\n\n".join(parts) + "\n" + summary
    meta = {
        "timeout_s": int(cfg.get("timeout_s") or 90),
        "max_chars": int(cfg.get("max_chars") or 900),
    }
    return prompt, meta


@router.post("/analyze", summary="LLM 分析演练结果，给出洞察型报告")
async def analyze_drill(req: EcoAnalysisRequest) -> Dict[str, Any]:
    """用 LLM 分析物竞天择演练结果，给出有洞察力的分析报告。"""
    summary = _build_drill_summary(req)
    prompt, prompt_meta = _compose_analysis_prompt(summary)
    timeout_s = float(prompt_meta.get("timeout_s") or 90)
    max_chars = int(prompt_meta.get("max_chars") or 900)

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
        result = await asyncio.wait_for(harness.chat(prompt), timeout=timeout_s)
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
            if max_chars > 0 and len(text) > max_chars:
                text = text[:max_chars].rstrip() + "…"
            return {
                "analysis": text,
                "ok": True,
                "summary": summary,
                "prompt_meta": prompt_meta,
            }
        return _fallback("LLM 未连接或返回空")
    except asyncio.TimeoutError:
        return _fallback(f"LLM 超时 {int(timeout_s)}s")
    except Exception as e:
        logger.warning("eco analyze failed: %s", e)
        return _fallback(str(e))
