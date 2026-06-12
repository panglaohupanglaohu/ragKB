# -*- coding: utf-8 -*-
"""Sustainability Evaluator — Token 可持续性评估器 (全局优化 G-5).

把消耗侧 (cost_aggregator/估算) 与产出侧 (trial 评分) 连起来:
  token_efficiency = Σscore / (Σtokens/1000)
  sustainability_score = 0.5*效率归一 + 0.3*趋势 + 0.2*预算余量
输出团队等级 (A-D) 与配置优化建议。
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# ── 调参常量 ──
EFFICIENCY_NORM_REF = 0.5     # 效率归一参考值: score/1k tokens 达到此值记满分
BUDGET_LOW_HEADROOM = 0.2     # 预算余量告警线
LOW_EFFICIENCY = 0.1          # 低效线 (score per 1k tokens)
GRADE_BOUNDS = [(0.75, "A"), (0.55, "B"), (0.35, "C"), (0.0, "D")]
EXPENSIVE_TIERS = {"opus", "gpt-4", "premium", "large"}
STEP_TOKEN_ESTIMATE = 800     # 无实测时: 每仿真步估算 token

# 模型降档建议映射
TIER_DOWNGRADE = {"opus": "sonnet", "gpt-4": "gpt-4o-mini", "premium": "standard", "large": "medium"}


@dataclass
class TeamUsage:
    """评估输入 (G5-1). data_quality: measured | estimated."""
    team_id: str = ""
    tokens_consumed: float = 0.0
    trials: List[Dict[str, Any]] = field(default_factory=list)
    # trial: {trial_id, scenario_id, total_score, tokens, steps?}
    model_tier: str = "standard"
    agent_count: int = 0
    scenario_role_demand: int = 0   # 场景要求的角色数（缩编判断）
    budget_tokens: float = 0.0
    previous_efficiency: Optional[float] = None  # 上周期效率（趋势）
    skill_stats: List[Dict[str, Any]] = field(default_factory=list)
    # skill_stats: {skill_name, total_uses, success_rate}
    data_quality: str = "measured"

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "TeamUsage":
        return cls(
            team_id=d.get("team_id", ""),
            tokens_consumed=float(d.get("tokens_consumed", 0)),
            trials=d.get("trials", []),
            model_tier=d.get("model_tier", "standard"),
            agent_count=int(d.get("agent_count", 0)),
            scenario_role_demand=int(d.get("scenario_role_demand", 0)),
            budget_tokens=float(d.get("budget_tokens", 0)),
            previous_efficiency=d.get("previous_efficiency"),
            skill_stats=d.get("skill_stats", []),
            data_quality=d.get("data_quality", "measured"),
        )


def estimate_tokens(usage: TeamUsage) -> float:
    """G5-3: 无实测消耗时按 trial 数据估算."""
    total = 0.0
    for t in usage.trials:
        if t.get("tokens"):
            total += float(t["tokens"])
        elif t.get("steps"):
            total += float(t["steps"]) * STEP_TOKEN_ESTIMATE
    return total


def evaluate_team(usage: TeamUsage) -> Dict[str, Any]:
    """单团队可持续性评估 (G5-1)."""
    tokens = usage.tokens_consumed
    data_quality = usage.data_quality
    if tokens <= 0:
        tokens = estimate_tokens(usage)
        data_quality = "estimated"
    total_score = sum(float(t.get("total_score", 0)) for t in usage.trials)

    # 核心指标
    if tokens > 0:
        token_efficiency = total_score / (tokens / 1000.0)
    else:
        token_efficiency = 0.0

    efficiency_norm = min(token_efficiency / EFFICIENCY_NORM_REF, 1.0)

    # 趋势 (0~1, 0.5=持平)
    if usage.previous_efficiency is not None and usage.previous_efficiency > 0:
        ratio = token_efficiency / usage.previous_efficiency
        trend = max(0.0, min(1.0, 0.5 + (ratio - 1.0)))
    else:
        trend = 0.5

    # 预算余量
    if usage.budget_tokens > 0:
        headroom = max(0.0, min(1.0, (usage.budget_tokens - tokens) / usage.budget_tokens))
    else:
        headroom = 0.5  # 未设预算 → 中性

    sustainability_score = round(0.5 * efficiency_norm + 0.3 * trend + 0.2 * headroom, 4)
    grade = next(g for bound, g in GRADE_BOUNDS if sustainability_score >= bound)

    recommendations = _build_recommendations(usage, token_efficiency, headroom, tokens)

    return {
        "team_id": usage.team_id,
        "token_efficiency": round(token_efficiency, 4),
        "efficiency_norm": round(efficiency_norm, 4),
        "trend": round(trend, 4),
        "budget_headroom": round(headroom, 4),
        "sustainability_score": sustainability_score,
        "grade": grade,
        "tokens_consumed": round(tokens, 1),
        "total_score": round(total_score, 4),
        "trial_count": len(usage.trials),
        "data_quality": data_quality,
        "recommendations": recommendations,
    }


def _build_recommendations(usage: TeamUsage, efficiency: float,
                           headroom: float, tokens: float) -> List[Dict[str, str]]:
    """配置建议引擎（规则版, G5-1）."""
    recs: List[Dict[str, str]] = []

    # 规则1: 低效 × 高档模型 → 降档
    if efficiency < LOW_EFFICIENCY and usage.model_tier.lower() in EXPENSIVE_TIERS:
        target = TIER_DOWNGRADE.get(usage.model_tier.lower(), "standard")
        recs.append({"type": "model_downgrade",
                     "detail": f"token 效率 {efficiency:.3f} 低于 {LOW_EFFICIENCY} 且使用高档模型 "
                               f"{usage.model_tier}，建议降档至 {target} 后对比评分"})

    # 规则2: 团队人数超出场景角色需求 → 缩编/转储备
    if usage.scenario_role_demand > 0 and usage.agent_count > usage.scenario_role_demand:
        surplus = usage.agent_count - usage.scenario_role_demand
        recs.append({"type": "team_downsize",
                     "detail": f"团队 {usage.agent_count} 人超出场景角色需求 "
                               f"{usage.scenario_role_demand} 人，建议 {surplus} 人转入储备或支援其他团队"})

    # 规则3: 预算余量不足 → 降演练频率
    if usage.budget_tokens > 0 and headroom < BUDGET_LOW_HEADROOM:
        recs.append({"type": "reduce_drills",
                     "detail": f"预算余量 {headroom:.0%} < {BUDGET_LOW_HEADROOM:.0%}，"
                               f"建议降低演练频率或将 max_steps 减半"})

    # 规则4: 高调用低成功率 skill → 路由/进化
    for s in usage.skill_stats:
        if s.get("total_uses", 0) >= 10 and s.get("success_rate", 1.0) < 0.5:
            recs.append({"type": "skill_route_or_evolve",
                         "detail": f"技能 {s.get('skill_name')} 调用 {s['total_uses']} 次但成功率 "
                                   f"{s['success_rate']:.0%}，建议路由至高熟练度 Agent 或发起进化 "
                                   f"(POST /api/v1/twin-evolution/runs)"})

    if not recs:
        recs.append({"type": "healthy", "detail": "当前配置可持续，维持现状并继续按场景演练积累数据"})
    return recs


def evaluate_group(usages: List[TeamUsage]) -> Dict[str, Any]:
    """团队组评估 + 资源再分配建议 (G5-2)."""
    results = [evaluate_team(u) for u in usages]
    results.sort(key=lambda r: r["sustainability_score"], reverse=True)

    total_tokens = sum(r["tokens_consumed"] for r in results)
    avg_score = (sum(r["sustainability_score"] for r in results) / len(results)) if results else 0

    # 资源再分配: 把低效团队 (D) 的 20% 预算挪给最高效团队 (A/B)
    reallocations: List[Dict[str, Any]] = []
    donors = [r for r in results if r["grade"] == "D" and r["tokens_consumed"] > 0]
    receivers = [r for r in results if r["grade"] in ("A", "B")]
    if donors and receivers:
        for d in donors:
            amount = round(d["tokens_consumed"] * 0.2, 0)
            target = receivers[0]
            reallocations.append({
                "from_team": d["team_id"], "to_team": target["team_id"],
                "tokens": amount,
                "rationale": f"{d['team_id']} 效率 {d['token_efficiency']:.3f} (D级) → "
                             f"{target['team_id']} 效率 {target['token_efficiency']:.3f} ({target['grade']}级)",
            })

    return {
        "teams": results,
        "ranking": [r["team_id"] for r in results],
        "group_sustainability": round(avg_score, 4),
        "total_tokens": round(total_tokens, 1),
        "reallocations": reallocations,
    }


def collect_team_usage(team_id: str) -> TeamUsage:
    """G5-3 数据适配层: 优先真实来源，缺失则估算（标注 data_quality）."""
    usage = TeamUsage(team_id=team_id, data_quality="estimated")

    # trial 评分与步数（产出侧）
    try:
        from sandbox.trial_api import _trials
        for t in _trials.values():
            if t.team_id != team_id:
                continue
            score = (t.evaluation or {}).get("total_score", t.best_score) or 0
            usage.trials.append({"trial_id": t.id,
                                 "scenario_id": getattr(t, "scenario_id", ""),
                                 "total_score": float(score),
                                 "steps": t.total_steps})
    except Exception as e:
        logger.debug(f"trial 数据不可用: {e}")

    # 真实成本（消耗侧）
    try:
        from .cost_aggregator import get_cost_aggregator  # 若存在
        agg = get_cost_aggregator()
        team_cost = agg.get_team_tokens(team_id)  # 接口若不同则落入 except
        if team_cost:
            usage.tokens_consumed = float(team_cost)
            usage.data_quality = "measured"
    except Exception:
        pass

    # skill 统计
    try:
        from sandbox.proficiency_store import get_proficiency_store
        for p in get_proficiency_store().query(team_id):
            usage.skill_stats.append({"skill_name": p.get("skill_name"),
                                      "total_uses": p.get("total_uses", 0),
                                      "success_rate": p.get("success_rate", 0.5)})
    except Exception:
        pass

    return usage
