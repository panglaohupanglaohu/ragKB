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

@router.get("/summary", response_model=CostDashboardResponse)
async def get_cost_summary(
    aggregation: str = Query(default="service", description="Aggregation dimension"),
    granularity: str = Query(default="day", description="Time granularity"),
    window: str = Query(default="7d", description="Time window (1d/7d/30d/90d)"),
    environment: Optional[str] = Query(default=None, description="Filter by environment"),
    service: Optional[str] = Query(default=None, description="Filter by service"),
    team: Optional[str] = Query(default=None, description="Filter by team"),
    namespace: Optional[str] = Query(default=None, description="Filter by namespace"),
):
    """Get full cost dashboard summary with aggregations and trends."""
    agg = get_cost_aggregator()
    params = _build_query_params(
        aggregation=aggregation, granularity=granularity, window=window,
        environment=environment, service=service, team=team, namespace=namespace,
    )
    summary = await agg.get_summary(params)

    return CostDashboardResponse(
        summary=summary,
        query=params,
        generated_at=datetime.now(timezone.utc).isoformat(),
        opencost_status="ok" if agg.opencost_healthy else "error",
        data_freshness_seconds=agg.cache_age_seconds,
    )


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
