# -*- coding: utf-8 -*-
"""Cost monitoring REST API — OpenCost data query, aggregation, and dashboard endpoints.

Provides:
  - GET  /cost/summary          — full dashboard summary
  - GET  /cost/by-service       — cost breakdown by service
  - GET  /cost/by-environment   — cost breakdown by environment
  - GET  /cost/by-team          — cost breakdown by team
  - GET  /cost/trends           — cost trend data for charts
  - GET  /cost/health           — aggregator health & freshness
  - POST /cost/labels/generate  — generate label injection patch (webhook simulation)
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query, status

from .cost_aggregator import get_cost_aggregator
from .cost_models import (
    AggregatedCostItem,
    CostDashboardResponse,
    CostLabelConfig,
    CostQueryParams,
    CostSummary,
    CostTrendSeries,
    PodCostItem,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/cost", tags=["Cost Monitoring"])


# ── Helpers ──────────────────────────────────────────────

def _build_query_params(
    aggregation: str = "service",
    granularity: str = "day",
    window: str = "7d",
    environment: Optional[str] = None,
    service: Optional[str] = None,
    team: Optional[str] = None,
    namespace: Optional[str] = None,
    cluster: Optional[str] = None,
) -> CostQueryParams:
    return CostQueryParams(
        aggregation=aggregation,
        granularity=granularity,
        window=window,
        environment=environment,
        service=service,
        team=team,
        namespace=namespace,
        cluster=cluster,
    )


# ── Dashboard Endpoints ─────────────────────────────────

@router.get("/summary")
async def get_cost_summary(
    aggregation: str = Query(default="service", description="Aggregation dimension"),
    granularity: str = Query(default="day", description="Time granularity"),
    window: str = Query(default="7d", description="Time window (1d/7d/30d/90d)"),
    environment: Optional[str] = Query(default=None, description="Filter by environment"),
    service: Optional[str] = Query(default=None, description="Filter by service"),
    team: Optional[str] = Query(default=None, description="Filter by team"),
    namespace: Optional[str] = Query(default=None, description="Filter by namespace"),
    source: str = Query(default="token", description="Data source: token (TokenLedger, default) | infra (OpenCost)"),
):
    """Get full cost dashboard summary.

    P1.5: source 参数控制数据源:
    - source=token (默认): 返回 Token 维度聚合（北极星）。无 token 数据时返回空列表 + degraded=true。
    - source=infra: 返回 OpenCost 聚合（legacy）。OpenCost 无数据时返回空 + degraded=true，不抛错。
    """
    if source == "infra":
        agg = get_cost_aggregator()
        params = _build_query_params(
            aggregation=aggregation, granularity=granularity, window=window,
            environment=environment, service=service, team=team, namespace=namespace,
        )
        summary = await agg.get_summary(params)
        return {
            "source": "infra",
            "degraded": not agg.opencost_healthy,
            "summary": summary.model_dump() if hasattr(summary, "model_dump") else summary,
            "query": params.model_dump() if hasattr(params, "model_dump") else params,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "opencost_status": "ok" if agg.opencost_healthy else "degraded",
            "data_freshness_seconds": agg.cache_age_seconds,
        }
    # 默认 token 源
    group_by = aggregation if aggregation in ("team", "skill", "phase") else "team"
    if group_by == "team":
        items = LEDGER.by_team(window)
    elif group_by == "skill":
        items = LEDGER.by_skill(window)
    else:
        items = LEDGER.by_phase(window)
    total_tokens = sum(int(i.get("total", 0)) for i in items) if isinstance(items, list) else sum(int(v.get("total", 0)) for v in items.values())
    return {
        "source": "token",
        "degraded": total_tokens == 0,
        "window": window,
        "group_by": group_by,
        "items": items,
        "totals": {"total_tokens": total_tokens},
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/by-service", response_model=List[AggregatedCostItem])
async def get_cost_by_service(
    window: str = Query(default="7d", description="Time window"),
    environment: Optional[str] = Query(default=None, description="Filter by environment"),
):
    """Get cost breakdown aggregated by service."""
    agg = get_cost_aggregator()
    params = _build_query_params(
        aggregation="service", window=window, environment=environment,
    )
    summary = await agg.get_summary(params)
    return summary.by_service


@router.get("/by-environment", response_model=List[AggregatedCostItem])
async def get_cost_by_environment(
    window: str = Query(default="7d", description="Time window"),
    service: Optional[str] = Query(default=None, description="Filter by service"),
):
    """Get cost breakdown aggregated by environment."""
    agg = get_cost_aggregator()
    params = _build_query_params(
        aggregation="environment", window=window, service=service,
    )
    summary = await agg.get_summary(params)
    return summary.by_environment


@router.get("/by-team", response_model=List[AggregatedCostItem])
async def get_cost_by_team(
    window: str = Query(default="7d", description="Time window"),
):
    """Get cost breakdown aggregated by team."""
    agg = get_cost_aggregator()
    params = _build_query_params(aggregation="team", window=window)
    summary = await agg.get_summary(params)
    return summary.by_team


@router.get("/trends", response_model=List[CostTrendSeries])
async def get_cost_trends(
    aggregation: str = Query(default="service", description="Aggregation dimension"),
    window: str = Query(default="7d", description="Time window"),
    granularity: str = Query(default="day", description="Time granularity"),
):
    """Get cost trend series for chart visualization."""
    agg = get_cost_aggregator()
    params = _build_query_params(
        aggregation=aggregation, window=window, granularity=granularity,
    )
    summary = await agg.get_summary(params)
    return summary.trends


@router.get("/health")
async def get_cost_health() -> Dict[str, Any]:
    """Get aggregator health status and data freshness."""
    agg = get_cost_aggregator()
    return {
        "status": "ok" if agg.opencost_healthy else "degraded",
        "opencost_healthy": agg.opencost_healthy,
        "last_error": agg.last_error,
        "data_age_seconds": agg.cache_age_seconds,
        "checked_at": datetime.now(timezone.utc).isoformat(),
    }


# ── Label Injection (Webhook Simulation) ────────────────

@router.get("/labels/config", response_model=CostLabelConfig)
async def get_label_config():
    """Get current cost label injection configuration."""
    return CostLabelConfig()


@router.post("/labels/generate")
async def generate_label_patch(
    pod_name: str = Query(..., description="Pod name"),
    namespace: str = Query(default="default", description="Kubernetes namespace"),
    service: str = Query(default="", description="Service name for label"),
    environment: str = Query(default="production", description="Environment label"),
    team: str = Query(default="platform", description="Team label"),
) -> Dict[str, Any]:
    """Generate a Kubernetes MutatingAdmissionWebhook patch for cost labels.

    This simulates what a webhook would produce when a Pod is created.
    Use this to test/validate label injection rules before deploying the webhook.
    """
    agg = get_cost_aggregator()
    return agg.generate_label_patch(
        pod_name=pod_name,
        namespace=namespace,
        service=service,
        environment=environment,
        team=team,
    )


# ── Pod-level query ─────────────────────────────────────

@router.get("/pods", response_model=List[PodCostItem])
async def get_pod_costs(
    service: Optional[str] = Query(default=None, description="Filter by service label"),
    environment: Optional[str] = Query(default=None, description="Filter by environment label"),
    team: Optional[str] = Query(default=None, description="Filter by team label"),
    namespace: Optional[str] = Query(default=None, description="Filter by namespace"),
    limit: int = Query(default=100, ge=1, le=1000, description="Max items to return"),
):
    """Get individual pod cost records, optionally filtered by labels."""
    agg = get_cost_aggregator()
    pods, _, _ = agg._cache.get_all()

    # Apply filters
    if service:
        pods = [p for p in pods if p.labels.get("service", "") == service or p.labels.get("app", "") == service]
    if environment:
        pods = [p for p in pods if p.labels.get("environment", "") == environment]
    if team:
        pods = [p for p in pods if p.labels.get("team", "") == team]
    if namespace:
        pods = [p for p in pods if p.namespace == namespace]

    return pods[:limit]


# ══════════════════════════════════════════════════════════════════
# Token 成本路由（P1 新增 — 北极星数据源）
# ══════════════════════════════════════════════════════════════════

from .token_ledger import LEDGER


@router.get("/tokens/summary")
async def tokens_summary(
    window: str = Query(default="24h", description="Time window (24h/7d/30d/all)"),
    group_by: str = Query(default="team", description="Group by: team/skill/phase"),
):
    """Token 成本汇总 — 按团队/技能/阶段聚合。"""
    if group_by == "skill":
        items = LEDGER.by_skill(window)
    elif group_by == "phase":
        items = LEDGER.by_phase(window)
    else:
        items = LEDGER.by_team(window)
    return {"source": "token", "window": window, "group_by": group_by, "items": items}


@router.get("/tokens/by-team")
async def tokens_by_team(
    window: str = Query(default="24h", description="Time window"),
):
    """按团队聚合 Token 成本。"""
    return LEDGER.by_team(window)


@router.get("/tokens/by-skill")
async def tokens_by_skill(
    window: str = Query(default="24h", description="Time window"),
):
    """按技能聚合 Token 成本。"""
    return LEDGER.by_skill(window)


@router.get("/tokens/by-task")
async def tokens_by_task(
    window: str = Query(default="24h", description="Time window"),
    team_id: str = Query(default="", description="Optional team filter"),
    limit: int = Query(default=50, ge=1, le=200),
):
    """按任务维聚合 Token（scenario_id / run_id）— 任务 Token 治理北极星."""
    items = LEDGER.by_task(window=window, team_id=team_id or "", limit=limit)
    return {"ok": True, "source": "token", "window": window, "items": items, "count": len(items)}


@router.get("/tokens/run/{run_id}")
async def tokens_by_run(run_id: str):
    """按 run_id 聚合 Token 成本（归因查询）。"""
    return LEDGER.run(run_id)


@router.get("/tokens/overview")
async def tokens_overview(
    window: str = Query(default="24h", description="Time window"),
):
    """Token 全局概览（总消耗 + by_team + by_phase）。"""
    return {
        "source": "token",
        "window": window,
        "summary": LEDGER.summary(window),
        "by_team": LEDGER.by_team(window),
        "by_phase": LEDGER.by_phase(window),
        "by_skill": LEDGER.by_skill(window),
    }


# ══════════════════════════════════════════════════════════════════
# Token 优化目标路由（P5）
# ══════════════════════════════════════════════════════════════════

from .cost_targets import get_target_store
from pydantic import BaseModel


class CreateTargetRequest(BaseModel):
    scope: str = "team"
    ref_id: str = ""
    metric: str = "score_per_1k"
    target: float = 0.0
    lever: str = "skill_extraction"
    baseline: Optional[float] = None


@router.post("/targets")
async def create_target(req: CreateTargetRequest):
    """创建 Token 优化目标。baseline 不提供时自动取 LEDGER 当前值。"""
    store = get_target_store()
    t = store.create(
        scope=req.scope, ref_id=req.ref_id, metric=req.metric,
        target=req.target, lever=req.lever, baseline=req.baseline,
    )
    return t.to_dict()


@router.get("/targets")
async def list_targets(status: str = Query(default="")):
    """列出 Token 优化目标。"""
    store = get_target_store()
    return [t.to_dict() for t in store.list_targets(status)]


@router.get("/targets/{tid}/progress")
async def get_target_progress(tid: str):
    """获取目标进度。"""
    store = get_target_store()
    return store.get_progress(tid)


@router.delete("/targets/{tid}")
async def delete_target(tid: str):
    """删除目标。"""
    store = get_target_store()
    ok = store.delete(tid)
    return {"deleted": ok}


@router.get("/targets/changed")
async def targets_changed(since: str = Query(default="")):
    """P10.5: 轮询检测目标进度是否有变化（轻量替代 SSE）。

    返回所有 active/achieved 目标的最新进度快照，前端比对 client-side timestamp 判断是否刷新。
    """
    store = get_target_store()
    items = []
    for t in store.list_targets():
        p = store.get_progress(t.id)
        items.append({"id": t.id, "status": p.get("status"), "progress": p.get("progress"),
                       "current": p.get("current"), "updated_at": t.updated_at})
    return {"items": items, "count": len(items)}


# ══════════════════════════════════════════════════════════════════
# 成本报告（P5.3）
# ══════════════════════════════════════════════════════════════════


@router.get("/report")
async def cost_report(
    window: str = Query(default="24h", description="Time window"),
    team: Optional[str] = Query(default=None, description="Filter by team"),
):
    """生成 Token 成本报告（汇总消耗 + 优化对比 + 棘轮锁定）。

    报告只读聚合，不落新表；可选快照存到 storage/cost_reports/。
    """
    from .cost_report import generate_cost_report
    return generate_cost_report(window=window, team=team)


# ══════════════════════════════════════════════════════════════════
# Phase 8: 成本构成 / 趋势 / 明细 / 杠杆 / 棘轮 路由
# ══════════════════════════════════════════════════════════════════


@router.get("/tokens/breakdown")
async def tokens_breakdown(
    window: str = Query(default="24h"),
    dim: str = Query(default="team", description="Dimension: team|skill|phase"),
    team_id: str = Query(default="", description="Filter by team"),
):
    """Token 成本构成（柱状图数据源）。P10.1: team_id 可选过滤。"""
    dim = dim if dim in ("team", "skill", "phase") else "team"
    return LEDGER.breakdown(window, dim, team_id)


@router.get("/tokens/trend")
async def tokens_trend(
    window: str = Query(default="7d"),
    bucket: str = Query(default="day", description="Bucket: day|hour"),
    dim: str = Query(default="", description="Filter dimension: team|skill|phase"),
    key: str = Query(default="", description="Filter key (team_id/skill_id/phase)"),
    team_id: str = Query(default="", description="Filter by team"),
):
    """Token 成本趋势（折线图数据源）。P10.1: team_id 可选过滤。"""
    return LEDGER.trend(window, bucket, dim, key, team_id)


@router.get("/tokens/detail")
async def tokens_detail(
    window: str = Query(default="24h"),
    group: str = Query(default="run", description="Group: run|call"),
    limit: int = Query(default=100, ge=1, le=500),
    team_id: str = Query(default="", description="Filter by team"),
):
    """Token 消耗明细（按 run 或按调用）。P10.1: team_id 可选过滤。"""
    if group == "call":
        return LEDGER.recent_calls(window, limit, team_id)
    return LEDGER.recent_runs(window, limit, team_id)


@router.get("/tokens/lever-split")
async def tokens_lever_split(
    window: str = Query(default="7d"),
    team_id: str = Query(default=""),
):
    """Skill 杠杆 vs 协作杠杆 token 拆分。"""
    return LEDGER.lever_split(team_id, window)


# ── Phase 8.5: 成本棘轮触发 ──


@router.post("/tokens/ratchet/advance")
async def advance_cost_ratchet(body: Dict[str, Any] = {}):
    """成本页触发：用本窗口实测 token_efficiency 尝试推进 cost_efficiency:{team}（只进不退）。

    body: {team_id, window?='7d', tolerance?=0.02}
    """
    from .ratchet_ledger import get_ratchet_ledger
    from .sustainability import collect_team_usage, evaluate_team

    team_id = body.get("team_id", "")
    if not team_id:
        raise HTTPException(status_code=400, detail="team_id required")
    window = body.get("window", "7d")
    ev = evaluate_team(collect_team_usage(team_id))
    eff = float(ev.get("token_efficiency", 0) or 0)
    if eff <= 0:
        return {"advanced": False, "reason": "no_efficiency",
                "hint": "该团队本窗口无演练评分，先跑一次 drill 评分再锁定",
                "efficiency": eff, "data_quality": ev.get("data_quality")}
    ledger = get_ratchet_ledger()
    res = ledger.advance(
        f"cost_efficiency:{team_id}", eff,
        evidence={"source": "cost_dashboard", "window": window,
                  "tokens": ev.get("tokens_consumed"),
                  "score": ev.get("total_score")},
        tolerance=float(body.get("tolerance", 0.02)),
    )
    return {**res, "metric_key": f"cost_efficiency:{team_id}",
            "efficiency": eff, "data_quality": ev.get("data_quality")}


@router.get("/tokens/ratchet")
async def cost_ratchet_metrics():
    """成本页读出：所有 cost_efficiency:* 当前代数与值。"""
    from .ratchet_ledger import get_ratchet_ledger
    m = get_ratchet_ledger().list_metrics("cost_efficiency:")
    return {"metrics": m, "total": len(m)}
