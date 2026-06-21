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
from typing import Any, Dict, List, Optional, Set

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
    cost_usd: float = 0.0
    data_sources: Dict[str, str] = field(default_factory=dict)

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
            cost_usd=float(d.get("cost_usd", 0) or 0),
            data_sources=d.get("data_sources", {}) or {},
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
        if total_score <= 0 and data_quality == "measured":
            # 有 token 消耗但无演练分数 → 标记为 "token_only"
            data_quality = "token_only"
            token_efficiency = 0.0
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

    # P4: 仅 token 数据（无演练分数）→ 中性评级，不按 D 处理
    if data_quality == "token_only":
        grade = "—"
        token_efficiency = 0.0

    # 无任何数据（0 token + 无演练）→ 中性评级
    if tokens <= 0 and not usage.trials:
        grade = "—"
        data_quality = "no_data"

    recommendations = _build_recommendations(usage, token_efficiency, headroom, tokens)

    # token_only 专项建议
    if data_quality == "token_only":
        recommendations = [{
            "type": "run_drill",
            "detail": f"团队有 {tokens:.0f} tokens 消耗但无演练评分数据。"
                      f"建议在数字孪生页面创建并运行试炼（确保 LLM 模式开启），"
                      f"完成后点击「评分」生成五维分数，效率视角将自动计算 score/1k tokens。",
        }] + recommendations

    # no_data 专项建议
    if data_quality == "no_data":
        recommendations = [{
            "type": "no_data",
            "detail": "团队暂无 token 消耗和演练数据。先在数字孪生页面运行试炼，"
                      "或在议事广场/技能萃取页面触发 LLM 调用以产生 token 归因数据。",
        }]

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
        "cost_usd": round(float(usage.cost_usd or 0), 4),
        "data_sources": dict(usage.data_sources or {}),
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


def build_plaza_topics(group_result: Dict[str, Any]) -> List[Dict[str, str]]:
    """G1-3: 从组评估结果生成议事广场整改议题（C/D 级团队）."""
    topics: List[Dict[str, str]] = []
    for team in group_result.get("teams", []):
        if team.get("grade") not in ("C", "D"):
            continue
        recs = "；".join(r["detail"] for r in team.get("recommendations", [])[:3])
        topics.append({
            "topic": f"[可持续性整改] {team['team_id']} 团队 token 效率 {team['token_efficiency']:.3f}（{team['grade']} 级）",
            "description": (
                f"评估数据（data_quality={team.get('data_quality')}）：\n"
                f"- token 效率: {team['token_efficiency']:.4f} score/1k tokens\n"
                f"- 可持续评分: {team['sustainability_score']:.3f}（{team['grade']} 级）\n"
                f"- 消耗: {team['tokens_consumed']:.0f} tokens / {team['trial_count']} 次试炼\n\n"
                f"系统建议：{recs}\n\n"
                f"请讨论：是否采纳上述配置调整？是否有更优方案？"
            ),
        })
    return topics


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
        if usage.trials:
            usage.data_sources["trials"] = "estimated"
    except Exception as e:
        logger.debug(f"trial 数据不可用: {e}")

    # 真实成本（消耗侧）— P4: 切换到 TokenLedger（直接从 usage.db 聚合）
    try:
        from .token_ledger import LEDGER
        by_team = LEDGER.by_team("7d")
        team_data = next((t for t in by_team if t.get("team_id") == team_id), None)
        if team_data and team_data.get("total", 0) > 0:
            usage.tokens_consumed = float(team_data["total"])
            usage.data_quality = "measured"
            usage.data_sources["token_ledger"] = "measured"
    except Exception as e:
        logger.debug(f"TokenLedger 不可用，回退估算: {e}")
        # 旧路径兜底
        try:
            from datetime import datetime, timedelta, timezone
            from .budget.store import get_usage_store
            store = get_usage_store()
            total = 0
            today = datetime.now(timezone.utc).date()
            for d in range(7):
                date_str = (today - timedelta(days=d)).isoformat()
                total += int(store.get_team_daily_total(team_id, date_str) or 0)
            if total > 0:
                usage.tokens_consumed = float(total)
                usage.data_quality = "measured"
                usage.data_sources["usage_store"] = "measured"
        except Exception as e2:
            logger.debug(f"budget UsageStore 也不可用: {e2}")

    # skill 统计
    try:
        from sandbox.proficiency_store import get_proficiency_store
        for p in get_proficiency_store().query(team_id):
            usage.skill_stats.append({"skill_name": p.get("skill_name"),
                                      "total_uses": p.get("total_uses", 0),
                                      "success_rate": p.get("success_rate", 0.5)})
        if usage.skill_stats:
            usage.data_sources["proficiency_store"] = "measured"
    except Exception:
        pass

    _enrich_team_profile(usage)

    # P10.4: derived score — 让纯任务团队也有非零效率
    total_score = sum(float(t.get("total_score", 0)) for t in usage.trials)
    if total_score <= 0:
        derived = 0.0
        try:
            from .cost_targets import get_target_store
            achieved = sum(1 for t in get_target_store().list_targets("achieved")
                           if t.scope == "team" and t.ref_id == team_id)
            derived = min(achieved * 1.0, 5.0)
        except Exception:
            pass
        if derived > 0:
            usage.trials.append({"trial_id": "_derived", "total_score": derived,
                                 "tokens": 0, "_derived": True})
            usage.data_sources["derived_score"] = "derived"

    return usage


def _enrich_team_profile(usage: TeamUsage) -> None:
    """从真实 TeamManager 补齐团队规模和默认模型层级（失败不影响评估）."""
    try:
        from .api import _team_manager
        if not _team_manager:
            return
        team = _team_manager.get_team(usage.team_id)
        if not team:
            return
        if not usage.agent_count:
            usage.agent_count = len(getattr(team, "agents", {}) or {})
        if usage.model_tier == "standard":
            model_names = [
                str(getattr(m, "name", "") or getattr(m, "model_id", "")).lower()
                for m in (getattr(team, "models", {}) or {}).values()
            ]
            usage.model_tier = _infer_model_tier(model_names)
        metadata = getattr(team, "metadata", {}) or {}
        if not usage.budget_tokens and metadata.get("budget_tokens"):
            usage.budget_tokens = float(metadata.get("budget_tokens") or 0)
        usage.data_sources["team_manager"] = "measured"
    except Exception as e:
        logger.debug(f"team_manager 数据不可用: {e}")


def _infer_model_tier(model_names: List[str]) -> str:
    joined = " ".join(model_names)
    if any(k in joined for k in ("opus", "gpt-4", "gpt4", "large", "premium")):
        return "premium"
    if any(k in joined for k in ("sonnet", "gpt-4o", "medium")):
        return "standard"
    if any(k in joined for k in ("mini", "haiku", "small", "lite")):
        return "small"
    return "standard"


async def collect_team_usage_async(team_id: str) -> TeamUsage:
    """异步适配层: 同步 token/trial 证据 + 真实 CostAggregator 团队成本."""
    usage = collect_team_usage(team_id)
    await _enrich_cost_aggregator(usage)
    return usage


async def _enrich_cost_aggregator(usage: TeamUsage) -> None:
    try:
        from .cost_aggregator import get_cost_aggregator
        from .cost_models import CostQueryParams
        summary = await get_cost_aggregator().get_summary(
            CostQueryParams(aggregation="team", window="7d"))
        for item in getattr(summary, "by_team", []) or []:
            value = getattr(item, "value", "") or ""
            if value != usage.team_id:
                continue
            usage.cost_usd = float(getattr(item, "total_cost", 0) or 0)
            usage.data_sources["cost_aggregator"] = "measured"
            break
    except Exception as e:
        logger.debug(f"cost_aggregator 数据不可用: {e}")


async def list_known_team_ids() -> List[str]:
    """从 TeamManager、trial、proficiency 与 CostAggregator 汇总已知团队."""
    teams: Set[str] = set()
    try:
        from .api import _team_manager
        if _team_manager:
            teams.update(t.team_id for t in _team_manager.list_teams() if getattr(t, "team_id", ""))
    except Exception as e:
        logger.debug(f"team_manager 团队列表不可用: {e}")
    try:
        from sandbox.trial_api import _trials
        teams.update(t.team_id for t in _trials.values() if getattr(t, "team_id", ""))
    except Exception:
        pass
    try:
        from pathlib import Path
        root = Path(__file__).resolve().parents[3]
        prof_dir = root / "storage" / "skill_proficiency"
        if prof_dir.exists():
            teams.update(p.stem for p in prof_dir.glob("*.json"))
    except Exception:
        pass
    try:
        from .cost_aggregator import get_cost_aggregator
        from .cost_models import CostQueryParams
        summary = await get_cost_aggregator().get_summary(
            CostQueryParams(aggregation="team", window="7d"))
        teams.update(
            getattr(item, "value", "")
            for item in getattr(summary, "by_team", []) or []
            if getattr(item, "value", "") and getattr(item, "value", "") != "(unknown)"
        )
    except Exception as e:
        logger.debug(f"cost_aggregator 团队列表不可用: {e}")
    # P4: 从 TokenLedger 补全有 token 消耗的团队
    try:
        from .token_ledger import LEDGER
        for item in LEDGER.by_team("7d"):
            tid = (item.get("team_id") or "").strip()
            if tid:  # 过滤空 team_id（旧调用未归因）
                teams.add(tid)
    except Exception:
        pass
    return sorted(teams)
