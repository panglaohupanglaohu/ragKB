# -*- coding: utf-8 -*-
"""Skill Classification API — 技能三类分类 (全局优化 G2-4)."""

from __future__ import annotations

import logging
from typing import Any, Dict

from fastapi import APIRouter, HTTPException, Query

from .skill_classifier import get_classification_store

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/skill-classification", tags=["skill-classification"])


def _build_evidence_fn(team_id: str):
    """从 proficiency_store / trial 数据构造证据函数."""
    prof_by_skill: Dict[str, Dict[str, Any]] = {}
    try:
        from sandbox.proficiency_store import get_proficiency_store
        for p in get_proficiency_store().query(team_id):
            prof_by_skill.setdefault(p.get("skill_name", ""), p)
    except Exception as e:
        logger.debug(f"proficiency 数据不可用: {e}")

    def evidence_fn(skill: Dict[str, Any]):
        name = skill.get("name", "")
        prof = prof_by_skill.get(name, {})
        usage_ev = {"team_usage": {team_id: prof.get("total_uses", skill.get("usage_count", 0) or 0)}}
        trial_ev = {
            "meets_rubric": prof.get("success_rate", 0) >= 0.6,
            "gate_ok": str(skill.get("lifecycle_stage", "")) in ("verified", "published", "solidified"),
            "category_pass": {prof.get("scenario_category", "general"): prof.get("success_rate", 0) >= 0.6}
            if prof else {},
        }
        return usage_ev, trial_ev

    return evidence_fn


@router.get("/teams/{team_id}")
async def get_team_classification(team_id: str) -> Dict[str, Any]:
    """当前三池视图（特有/通用/储备）."""
    return get_classification_store().get_view(team_id)


@router.post("/teams/{team_id}/reclassify")
async def reclassify_team(team_id: str) -> Dict[str, Any]:
    """触发批量重算 (G2-3)，返回变更（毕业/降级事件）."""
    skills = []
    try:
        from .skill_library import get_skill_library
        skills = [s for s in get_skill_library().browse(team_id=team_id) if s.get("_is_own")]
    except Exception as e:
        logger.warning(f"技能库不可用: {e}")
    if not skills:
        return {"team_id": team_id, "total": 0, "pools": {}, "changes": [],
                "note": "团队无自有技能或技能库不可用"}
    return get_classification_store().reclassify_team(
        team_id, skills, evidence_fn=_build_evidence_fn(team_id))


@router.get("/teams/{team_id}/history")
async def get_classification_history(team_id: str, skill_id: str = Query(default="")) -> Dict[str, Any]:
    """分类变迁史."""
    return {"team_id": team_id,
            "history": get_classification_store().get_history(team_id, skill_id)}
