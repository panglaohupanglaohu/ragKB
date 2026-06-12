# -*- coding: utf-8 -*-
"""Sustainability API — Token 可持续性评估 (全局优化 G5-4)."""

from __future__ import annotations

import logging
from typing import Any, Dict, List

from fastapi import APIRouter
from pydantic import BaseModel, Field

from .sustainability import TeamUsage, collect_team_usage, evaluate_group, evaluate_team

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/sustainability", tags=["sustainability"])


class EvaluateRequest(BaseModel):
    usages: List[Dict[str, Any]] = Field(default_factory=list)


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
    usage = collect_team_usage(team_id)
    result = evaluate_team(usage)
    result["ratchet"] = _advance_cost_ratchet(result)
    return result


@router.get("/group")
async def evaluate_all_teams() -> Dict[str, Any]:
    """全部已知团队的组评估（数据来自 trial 记录中的 team_id）."""
    team_ids = set()
    try:
        from sandbox.trial_api import _trials
        team_ids = {t.team_id for t in _trials.values() if t.team_id}
    except Exception:
        pass
    if not team_ids:
        return {"teams": [], "ranking": [], "group_sustainability": 0,
                "note": "暂无 trial 数据"}
    usages = [collect_team_usage(tid) for tid in sorted(team_ids)]
    return evaluate_group(usages)
