# -*- coding: utf-8 -*-
"""Scenario API — 业务场景 REST 接口 (v4 B-1)."""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from .scenario_compiler import compile_scenario, match_team, generate_from_description
from .scenario_models import ScenarioSpec, validate_scenario
from .scenario_store import get_scenario_store

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/scenarios", tags=["scenarios"])


class CreateScenarioRequest(BaseModel):
    spec: Dict[str, Any] = Field(default_factory=dict)


class GenerateScenarioRequest(BaseModel):
    description: str = ""
    team_id: str = ""


def _best_score_map() -> Dict[str, float]:
    """每个 scenario 的历史最佳分（联查内存 trial 表）."""
    result: Dict[str, float] = {}
    try:
        from .trial_api import _trials
        for t in _trials.values():
            sid = getattr(t, "scenario_id", "")
            if sid and t.best_score is not None:
                result[sid] = max(result.get(sid, 0.0), float(t.best_score))
    except Exception:
        pass
    return result


@router.get("")
async def list_scenarios(
    category: str = Query(default=""),
    tag: str = Query(default=""),
    source: str = Query(default="", description="来源过滤: plan(讨论产出)|builtin(内置样例)|all|空=全部"),
    team_id: str = Query(default="", description="传入则按该团队角色/技能匹配度排序"),
) -> Dict[str, Any]:
    """B-1.1: 场景列表（含历史最佳分）。传 team_id 时附匹配度并按匹配度降序（闭环优化 C2′）。
    source 过滤（数字办公室闭环 M1-1）：plan=Plaza 讨论产出的执行计划场景，builtin=内置测试样例。"""
    store = get_scenario_store()
    best = _best_score_map()
    # 选团队时取一次团队快照，用于复用 match_team 算每个场景的匹配度
    team_snapshot = None
    if team_id:
        try:
            from agents.api import _tm
            team = _tm().get_team(team_id)
            if team:
                agents_list = team.agents
                if isinstance(agents_list, dict):
                    agents_list = list(agents_list.values())
                team_snapshot = {"agents": [
                    {"id": getattr(a, "agent_id", ""), "role": getattr(a, "role", ""),
                     "skills": getattr(a, "skills", []) or []}
                    for a in agents_list
                ]}
        except Exception as e:
            logger.warning(f"list_scenarios 团队快照失败: {e}")
    items = []
    for s in store.list(category=category, tag=tag, source=source):
        item = {
            "scenario_id": s.scenario_id, "name": s.name, "category": s.category,
            "description": s.description, "tags": s.tags, "difficulty": s.difficulty,
            "recommended_max_steps": s.recommended_max_steps, "source": s.source,
            "room_count": len(s.world.rooms), "task_count": len(s.taskflow),
            "chaos_phase_count": len(s.chaos_script),
            "best_score": best.get(s.scenario_id),
        }
        if team_snapshot is not None:
            try:
                m = match_team(s, team_snapshot)
                item["match"] = {
                    "skill_match_rate": m.get("skill_match_rate", 0),
                    "missing_skills": m.get("missing_skills", []),
                }
            except Exception:
                item["match"] = {"skill_match_rate": 0, "missing_skills": []}
        items.append(item)
    if team_snapshot is not None:
        items.sort(key=lambda x: -(x.get("match", {}).get("skill_match_rate", 0)))
    return {"scenarios": items, "total": len(items), "load_errors": store.load_errors}


@router.get("/{scenario_id}")
async def get_scenario(scenario_id: str) -> Dict[str, Any]:
    """B-1.2: 场景详情."""
    spec = get_scenario_store().get(scenario_id)
    if not spec:
        raise HTTPException(status_code=404, detail=f"Scenario {scenario_id} not found")
    return spec.to_dict()


@router.post("")
async def create_scenario(req: CreateScenarioRequest) -> Dict[str, Any]:
    """B-1.3: 上传自定义场景，schema 校验失败返回 422 + 字段级错误."""
    errors = validate_scenario(req.spec)
    if errors:
        raise HTTPException(status_code=422, detail={"message": "schema 校验失败", "errors": errors})
    spec = ScenarioSpec.from_dict(req.spec)
    if spec.source == "builtin":
        spec.source = "custom"
    result = get_scenario_store().save(spec)
    if not result.get("ok"):
        raise HTTPException(status_code=422, detail=result)
    return {"ok": True, "scenario_id": spec.scenario_id}


class AssignPlanRequest(BaseModel):
    plan: Dict[str, Any] = Field(default_factory=dict)


@router.post("/from-plan")
async def assign_plan_to_twin_endpoint(req: AssignPlanRequest) -> Dict[str, Any]:
    """M1-4: Plaza 讨论产出的 ExecutionPlan → 落地性审查 → 编译 → 落库为 source=plan 场景。

    审查不过返回 422 + 缺项 issues；成功返回 {ok, scenario_id}。
    这是「讨论→计划→孪生演练」闭环把计划送进孪生菜单的唯一入口。
    """
    from .plan_scenario_bridge import assign_plan_to_twin
    result = assign_plan_to_twin(req.plan or {})
    if not result.get("ok"):
        raise HTTPException(status_code=422, detail=result)
    return result


@router.post("/generate")
async def generate_scenario(req: GenerateScenarioRequest) -> Dict[str, Any]:
    """B-1.4: LLM 生成场景草稿（需用户确认后 POST 保存）."""
    if not req.description.strip():
        raise HTTPException(status_code=400, detail="description 必填")
    spec = await generate_from_description(req.description, req.team_id)
    if spec is None:
        raise HTTPException(status_code=502, detail="LLM 场景生成失败（重试 3 次后放弃），可手动编写 JSON 上传")
    return {"ok": True, "draft": spec.to_dict(), "note": "草稿未保存，确认后 POST /api/v1/scenarios 保存"}


@router.get("/{scenario_id}/match")
async def match_scenario_team(scenario_id: str, team_id: str = Query(default="")) -> Dict[str, Any]:
    """B-1.5: 团队与场景角色要求的匹配度."""
    spec = get_scenario_store().get(scenario_id)
    if not spec:
        raise HTTPException(status_code=404, detail=f"Scenario {scenario_id} not found")

    team_snapshot: Dict[str, Any] = {"agents": []}
    if team_id:
        try:
            from agents.api import _tm
            team = _tm().get_team(team_id)
            if team:
                agents_list = team.agents
                if isinstance(agents_list, dict):
                    agents_list = list(agents_list.values())
                team_snapshot["agents"] = [
                    {"id": getattr(a, "agent_id", ""), "role": getattr(a, "role", ""),
                     "skills": getattr(a, "skills", []) or []}
                    for a in agents_list
                ]
        except Exception as e:
            logger.warning(f"团队加载失败: {e}")

    return {"scenario_id": scenario_id, "team_id": team_id,
            **match_team(spec, team_snapshot)}


@router.delete("/{scenario_id}")
async def delete_scenario(scenario_id: str) -> Dict[str, Any]:
    """删除自定义场景 (builtin 不可删)."""
    result = get_scenario_store().delete(scenario_id)
    if not result.get("ok"):
        code = 404 if result.get("error") == "not_found" else 403
        raise HTTPException(status_code=code, detail=result.get("error"))
    return result
