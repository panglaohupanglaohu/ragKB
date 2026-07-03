# -*- coding: utf-8 -*-
"""自动诊断 — 识别最弱目标并触发优化.

照搬 Hermes Phase 5 Auto-Triage:
- 追踪 skill effectiveness + usage_count
- 排序: impact = (1 - effectiveness) × usage_count
- 识别退化趋势
- 触发优化建议
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

logger = logging.getLogger("evolution.auto_triage")


class TriageCandidate:
    """一个自动诊断出的优化候选."""

    def __init__(self, skill_id: str, skill_name: str, team_id: str):
        self.skill_id = skill_id
        self.skill_name = skill_name
        self.team_id = team_id
        self.effectiveness: float = 1.0
        self.usage_count: int = 0
        self.impact_score: float = 0.0
        self.reasons: List[str] = []
        self.priority: int = 99

    def to_dict(self) -> Dict[str, Any]:
        return {
            "skill_id": self.skill_id,
            "skill_name": self.skill_name,
            "team_id": self.team_id,
            "effectiveness": self.effectiveness,
            "usage_count": self.usage_count,
            "impact_score": round(self.impact_score, 2),
            "reasons": self.reasons,
            "priority": self.priority,
        }


def triage_skills(
    skills: List[Dict[str, Any]],
    effectiveness_threshold: float = 0.7,
    min_usage: int = 3,
    top_n: int = 5,
) -> List[TriageCandidate]:
    """自动诊断 — 找出最需要优化的技能.

    照搬 Hermes Auto-Triage logic:
    - Skills with declining success rates or high failure rates
    - Rank by (potential_improvement × usage_frequency)
    """
    candidates = []

    for s in skills:
        skill_id = s.get("skill_id", "")
        skill_name = s.get("name", "")
        team_id = s.get("team_id", "")
        effectiveness = s.get("effectiveness", 1.0)
        usage_count = s.get("usage_count", 0)

        # Skip unused skills
        if usage_count < min_usage:
            continue

        reasons = []
        priority = 99

        # Check effectiveness threshold
        if effectiveness < effectiveness_threshold:
            reasons.append(f"成功率低: {effectiveness * 100:.0f}% (阈值 {effectiveness_threshold * 100:.0f}%)")
            priority = min(priority, 1)

        # Check for very low effectiveness
        if effectiveness < 0.4:
            reasons.append("成功率极低 (< 40%)")
            priority = min(priority, 0)

        # Check high usage + mediocre performance
        if usage_count > 10 and effectiveness < 0.8:
            reasons.append(f"高频使用({usage_count}次) + 中等表现")
            priority = min(priority, 2)

        if not reasons:
            continue

        tc = TriageCandidate(skill_id, skill_name, team_id)
        tc.effectiveness = effectiveness
        tc.usage_count = usage_count
        tc.impact_score = (1.0 - effectiveness) * usage_count
        tc.reasons = reasons
        tc.priority = priority
        candidates.append(tc)

    # Sort by impact score descending
    candidates.sort(key=lambda c: (-c.priority == 0, -c.impact_score))
    return candidates[:top_n]


def compute_team_fitness_summary(skills: List[Dict[str, Any]]) -> Dict[str, Any]:
    """计算团队整体 fitness 摘要."""
    if not skills:
        return {
            "total_skills": 0,
            "mean_effectiveness": 0,
            "total_usage": 0,
            "at_risk": 0,
            "healthy": 0,
        }

    total = len(skills)
    eff_values = [s.get("effectiveness", 1.0) for s in skills]
    usage_values = [s.get("usage_count", 0) for s in skills]

    mean_eff = sum(eff_values) / total if total else 0
    at_risk = sum(1 for e in eff_values if e < 0.7)
    healthy = sum(1 for e in eff_values if e >= 0.8)

    return {
        "total_skills": total,
        "mean_effectiveness": round(mean_eff, 3),
        "total_usage": sum(usage_values),
        "at_risk": at_risk,
        "healthy": healthy,
        "at_risk_pct": round(at_risk / max(total, 1) * 100, 1),
    }


async def run_auto_triage(
    team_id: str,
    skill_library=None,
    top_n: int = 3,
) -> Dict[str, Any]:
    """运行自动诊断 — Phase 5 主入口.

    照搬 Hermes Continuous Loop:
    1. 收集所有技能的 effectiveness + usage
    2. 诊断
    3. 返回候选列表
    """
    if skill_library is None:
        from ..skill_library import get_skill_library
        skill_library = get_skill_library()

    # Get all skills for team via browse API
    all_skills = skill_library.browse(team_id=team_id) if skill_library else []
    skills_data = []
    for s in all_skills:
        skills_data.append({
            "skill_id": s.get("skill_id", ""),
            "name": s.get("name", ""),
            "team_id": team_id,
            "effectiveness": s.get("effectiveness", 1.0),
            "usage_count": s.get("usage_count", 0),
        })

    candidates = triage_skills(skills_data, top_n=top_n)
    summary = compute_team_fitness_summary(skills_data)

    return {
        "team_id": team_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "summary": summary,
        "candidates": [c.to_dict() for c in candidates],
        "recommendation": _build_recommendation(candidates),
    }


def _build_recommendation(candidates: List[TriageCandidate]) -> str:
    """生成诊断建议文本."""
    if not candidates:
        return "所有技能表现良好，暂无需优化的目标。"

    top = candidates[0]
    return (
        f"建议优先优化「{top.skill_name}」— "
        f"成功率 {top.effectiveness * 100:.0f}%, 使用 {top.usage_count} 次, "
        f"影响力分数 {top.impact_score:.1f}。"
        f"原因: {'; '.join(top.reasons)}"
    )
