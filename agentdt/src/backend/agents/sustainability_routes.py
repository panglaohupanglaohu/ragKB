# -*- coding: utf-8 -*-
"""Sustainability API — Token 可持续性评估 (全局优化 G5-4)."""

from __future__ import annotations

import logging
from typing import Any, Dict, List

from fastapi import APIRouter
from pydantic import BaseModel, Field

from .sustainability import (
    TeamUsage,
    build_plaza_topics,
    collect_team_usage_async,
    evaluate_group,
    evaluate_team,
    list_known_team_ids,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/sustainability", tags=["sustainability"])


class EvaluateRequest(BaseModel):
    usages: List[Dict[str, Any]] = Field(default_factory=list)


class PlazaTopicsRequest(BaseModel):
    plaza_id: str = ""
    dry_run: bool = True
    max_topics: int = Field(default=3, ge=1, le=20)


def _advance_cost_ratchet(result: Dict[str, Any]) -> Dict[str, Any]:
    """评估完成尝试推进棘轮 cost_efficiency:{team_id} (G5-4)，cost 类容忍 2% 波动."""
    try:
        from .ratchet_ledger import get_ratchet_ledger
        ledger = get_ratchet_ledger()
        current = ledger.get(f"cost_efficiency:{result['team_id']}")
        tol = (current["value"] * 0.02) if current else 0.0
        return ledger.advance(
            f"cost_efficiency:{result['team_id']}",
            result["token_efficiency"],
            evidence={"sustainability_score": result["sustainability_score"],
                      "data_quality": result["data_quality"]},
            tolerance=tol,
        )
    except Exception as e:
        logger.warning(f"cost_efficiency 棘轮推进失败 (非致命): {e}")
        return {"advanced": False, "reason": f"error: {e}"}


@router.post("/evaluate")
async def evaluate(req: EvaluateRequest) -> Dict[str, Any]:
    """显式传入 usage 评估（单个或多个团队）."""
    usages = [TeamUsage.from_dict(u) for u in req.usages]
    if len(usages) == 1:
        result = evaluate_team(usages[0])
        result["ratchet"] = _advance_cost_ratchet(result)
        return result
    group = evaluate_group(usages)
    for r in group["teams"]:
        r["ratchet"] = _advance_cost_ratchet(r)
    return group


@router.get("/teams/{team_id}")
async def evaluate_single_team(team_id: str) -> Dict[str, Any]:
    """自动聚合该团队数据并评估."""
    usage = await collect_team_usage_async(team_id)
    result = evaluate_team(usage)
    result["ratchet"] = _advance_cost_ratchet(result)
    return result


@router.get("/group")
async def evaluate_all_teams() -> Dict[str, Any]:
    """全部已知团队的组评估（TeamManager/trial/proficiency/CostAggregator 汇总）.

    P8R.4: 每个 team 注入 lever_cost（两杠杆拆分）+ efficiency_formula。
    """
    team_ids = await list_known_team_ids()
    if not team_ids:
        return {"teams": [], "ranking": [], "group_sustainability": 0,
                "note": "暂无团队或 trial/cost 数据"}
    usages = [await collect_team_usage_async(tid) for tid in team_ids]
    result = evaluate_group(usages)
    # P8R.4: 注入两杠杆拆分 + 公式
    try:
        from .token_ledger import LEDGER
        for team in result.get("teams", []):
            tid = team.get("team_id", "")
            team["lever_cost"] = LEDGER.lever_split(tid, "7d")
            team["efficiency_formula"] = "token_efficiency = total_score / (tokens_consumed / 1000)"
    except Exception as e:
        logger.debug(f"lever_cost 注入失败: {e}")
    return result


@router.post("/weekly-plaza-topics")
async def create_weekly_plaza_topics(req: PlazaTopicsRequest) -> Dict[str, Any]:
    """G1-3: 由可持续性周报生成议事广场整改议题.

    dry_run=true 仅返回议题预览；dry_run=false 会在指定 Plaza 或首个 Plaza 中创建讨论。
    """
    team_ids = await list_known_team_ids()
    usages = [await collect_team_usage_async(tid) for tid in team_ids]
    group = evaluate_group(usages)
    topics = build_plaza_topics(group)[:req.max_topics]
    if req.dry_run or not topics:
        return {"dry_run": True, "topics": topics, "group": group}

    try:
        from .plaza_engine import get_plaza_engine
        engine = get_plaza_engine()
        plaza = engine.get_plaza(req.plaza_id) if req.plaza_id else None
        if plaza is None:
            plazas = engine.list_plazas()
            plaza = plazas[0] if plazas else engine.create_plaza(
                "可持续性整改议事厅",
                "由 sustainability 周报自动生成，用于讨论低效团队整改。",
            )
        created = []
        for topic in topics:
            disc = engine.create_discussion(plaza.id, topic["topic"], topic["description"], max_rounds=3)
            if disc:
                created.append(disc.to_dict())
        return {"dry_run": False, "plaza_id": plaza.id, "created": created,
                "topics": topics, "group": group}
    except Exception as e:
        logger.warning(f"创建可持续整改议题失败: {e}")
        return {"dry_run": False, "created": [], "topics": topics,
                "error": str(e), "group": group}
