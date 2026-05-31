# -*- coding: utf-8 -*-
"""Cost monitoring data models — OpenCost integration & label-based aggregation.

Defines Pydantic models for cost allocation data, label-based filtering,
and dashboard query parameters.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ── Label Constants ──────────────────────────────────────

class CostLabel(str, Enum):
    """Standard cost allocation labels for K8s workloads."""
    APP = "app"
    SERVICE = "service"
    ENVIRONMENT = "environment"
    TEAM = "team"
    NAMESPACE = "namespace"
    CLUSTER = "cluster"
    COMPONENT = "component"


class CostAggregation(str, Enum):
    """Aggregation dimensions for cost queries."""
    SERVICE = "service"
    ENVIRONMENT = "environment"
    TEAM = "team"
    NAMESPACE = "namespace"
    CLUSTER = "cluster"
    POD = "pod"
    CONTAINER = "container"
    DAILY = "daily"
    HOURLY = "hourly"


class CostGranularity(str, Enum):
    HOUR = "hour"
    DAY = "day"
    WEEK = "week"
    MONTH = "month"


# ── Pydantic Models ──────────────────────────────────────

class PodCostItem(BaseModel):
    """Single pod-level cost allocation record."""
    pod: str
    namespace: str = ""
    container: str = ""
    cpu_cost: float = 0.0
    ram_cost: float = 0.0
    pv_cost: float = 0.0
    network_cost: float = 0.0
    gpu_cost: float = 0.0
    total_cost: float = 0.0
    cpu_core_hours: float = 0.0
    ram_gb_hours: float = 0.0
    labels: Dict[str, str] = Field(default_factory=dict)
    window_start: Optional[str] = None
    window_end: Optional[str] = None


class AggregatedCostItem(BaseModel):
    """Cost aggregated by a dimension (service/env/team)."""
    dimension: str = ""
    value: str = ""
    cpu_cost: float = 0.0
    ram_cost: float = 0.0
    pv_cost: float = 0.0
    network_cost: float = 0.0
    gpu_cost: float = 0.0
    total_cost: float = 0.0
    pod_count: int = 0
    container_count: int = 0
    percentage: float = 0.0


class CostTrendPoint(BaseModel):
    """Single data point in a cost trend series."""
    timestamp: str = ""
    total_cost: float = 0.0
    cpu_cost: float = 0.0
    ram_cost: float = 0.0


class CostTrendSeries(BaseModel):
    """Cost trend over time, grouped by a dimension."""
    dimension: str = ""
    value: str = ""
    points: List[CostTrendPoint] = Field(default_factory=list)
    total: float = 0.0
    avg_daily: float = 0.0


class CostSummary(BaseModel):
    """High-level cost summary for dashboard overview."""
    total_cost: float = 0.0
    cpu_cost: float = 0.0
    ram_cost: float = 0.0
    pv_cost: float = 0.0
    network_cost: float = 0.0
    gpu_cost: float = 0.0
    pod_count: int = 0
    container_count: int = 0
    service_count: int = 0
    environment_count: int = 0
    team_count: int = 0
    namespace_count: int = 0
    window_start: Optional[str] = None
    window_end: Optional[str] = None
    by_service: List[AggregatedCostItem] = Field(default_factory=list)
    by_environment: List[AggregatedCostItem] = Field(default_factory=list)
    by_team: List[AggregatedCostItem] = Field(default_factory=list)
    trends: List[CostTrendSeries] = Field(default_factory=list)


class CostQueryParams(BaseModel):
    """Parameters for cost data queries."""
    aggregation: str = Field(default="service", description="Aggregation dimension")
    granularity: str = Field(default="day", description="Time granularity: hour/day/week/month")
    window: str = Field(default="7d", description="Time window: 1d/7d/30d/90d")
    environment: Optional[str] = Field(default=None, description="Filter by environment")
    service: Optional[str] = Field(default=None, description="Filter by service")
    team: Optional[str] = Field(default=None, description="Filter by team")
    namespace: Optional[str] = Field(default=None, description="Filter by namespace")
    cluster: Optional[str] = Field(default=None, description="Filter by cluster")


class CostDashboardResponse(BaseModel):
    """Full dashboard response model."""
    summary: CostSummary
    query: CostQueryParams
    generated_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    opencost_status: str = "ok"
    data_freshness_seconds: int = 0


class CostLabelConfig(BaseModel):
    """Configuration for automatic cost label injection."""
    enabled: bool = True
    default_environment: str = "production"
    default_team: str = "platform"
    label_prefix: str = "cost.opencost.io"
    inject_labels: List[str] = Field(
        default_factory=lambda: ["app", "environment", "team", "component"]
    )
    webhook_port: int = 9443
    webhook_path: str = "/mutate-cost-labels"
