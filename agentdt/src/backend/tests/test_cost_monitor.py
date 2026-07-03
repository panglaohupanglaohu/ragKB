# -*- coding: utf-8 -*-
"""Cost monitoring tests — OpenCost integration, label injection, and dashboard API.

Tests cover:
  1. CostLabelConfig — default values, label injection targets
  2. K8s webhook label resolution and JSON Patch generation
  3. Cost aggregation by service/environment/team dimensions
  4. Cost routes health check (import-level)
  5. CostModels serialization / deserialization
"""

from __future__ import annotations

import pytest

from agents.cost_models import (
    AggregatedCostItem,
    CostDashboardResponse,
    CostGranularity,
    CostLabel,
    CostLabelConfig,
    CostQueryParams,
    CostSummary,
    CostTrendPoint,
    CostTrendSeries,
    PodCostItem,
)


# ── Fixtures ────────────────────────────────────────────


@pytest.fixture
def default_config() -> CostLabelConfig:
    return CostLabelConfig()


@pytest.fixture
def sample_pods() -> list[PodCostItem]:
    return [
        PodCostItem(
            pod="api-gateway-7d8f",
            namespace="default",
            cpu_cost=12.50,
            ram_cost=8.30,
            gpu_cost=0.0,
            pv_cost=2.10,
            network_cost=1.20,
            total_cost=24.10,
            labels={"service": "api-gateway", "environment": "production", "team": "platform"},
            window_start="2026-05-29T00:00:00Z",
            window_end="2026-05-30T00:00:00Z",
        ),
        PodCostItem(
            pod="worker-pool-3a2b",
            namespace="default",
            cpu_cost=45.00,
            ram_cost=22.00,
            gpu_cost=0.0,
            pv_cost=5.00,
            network_cost=3.00,
            total_cost=75.00,
            labels={"service": "worker", "environment": "production", "team": "backend"},
            window_start="2026-05-29T00:00:00Z",
            window_end="2026-05-30T00:00:00Z",
        ),
        PodCostItem(
            pod="dashboard-9c1e",
            namespace="staging",
            cpu_cost=3.20,
            ram_cost=1.80,
            gpu_cost=0.0,
            pv_cost=0.50,
            network_cost=0.30,
            total_cost=5.80,
            labels={"service": "dashboard", "environment": "staging", "team": "frontend"},
            window_start="2026-05-29T00:00:00Z",
            window_end="2026-05-30T00:00:00Z",
        ),
    ]


# ── Tests: CostLabelConfig ──────────────────────────────


class TestCostLabelConfig:
    def test_defaults(self, default_config):
        """Default configuration has standard cost labels."""
        assert default_config.label_prefix == "cost.opencost.io"
        assert "environment" in default_config.inject_labels
        assert "team" in default_config.inject_labels
        assert "service" in default_config.inject_labels
        assert "component" in default_config.inject_labels
        assert default_config.default_environment == "development"
        assert default_config.default_team == "platform"

    def test_custom_config(self):
        config = CostLabelConfig(
            label_prefix="opencost.k8s.io",
            inject_labels=["service", "environment"],
            default_environment="production",
            default_team="sre",
        )
        assert config.label_prefix == "opencost.k8s.io"
        assert config.inject_labels == ["service", "environment"]
        assert config.default_environment == "production"
        assert config.default_team == "sre"

    def test_cost_labels_standard_set(self):
        """Standard cost labels stay in the default injection set."""
        config = CostLabelConfig()
        assert CostLabel.ENVIRONMENT.value in config.inject_labels
        assert CostLabel.TEAM.value in config.inject_labels


# ── Tests: PodCostItem ──────────────────────────────────


class TestPodCostItem:
    def test_create_minimal(self):
        item = PodCostItem(
            pod="test-pod",
            namespace="default",
            cpu_cost=1.0,
            ram_cost=2.0,
            total_cost=3.0,
            labels={"service": "test-svc", "environment": "dev", "team": "qa"},
        )
        assert item.pod == "test-pod"
        assert item.total_cost == 3.0
        assert item.gpu_cost == 0.0  # default

    def test_model_dump(self):
        item = PodCostItem(
            pod="test-pod",
            namespace="default",
            cpu_cost=1.0,
            ram_cost=2.0,
            total_cost=3.0,
            labels={"service": "test", "environment": "dev", "team": "qa"},
        )
        d = item.model_dump()
        assert d["pod"] == "test-pod"
        assert d["cpu_cost"] == 1.0
        assert d["total_cost"] == 3.0


# ── Tests: AggregatedCostItem ──────────────────────────


class TestAggregatedCostItem:
    def test_create(self):
        item = AggregatedCostItem(
            dimension="service",
            value="api-gateway",
            total_cost=99.10,
            pod_count=4,
        )
        assert item.dimension == "service"
        assert item.value == "api-gateway"
        assert item.total_cost == 99.10
        assert item.pod_count == 4

    def test_serialize(self):
        item = AggregatedCostItem(
            dimension="service",
            value="worker",
            total_cost=75.00,
            pod_count=1,
        )
        d = item.model_dump()
        assert d["dimension"] == "service"
        assert d["total_cost"] == 75.00


# ── Tests: CostSummary ──────────────────────────────────


class TestCostSummary:
    def test_create(self, sample_pods):
        by_svc = [
            AggregatedCostItem(dimension="service", value="api-gateway", total_cost=24.10, pod_count=1),
            AggregatedCostItem(dimension="service", value="worker", total_cost=75.00, pod_count=1),
            AggregatedCostItem(dimension="service", value="dashboard", total_cost=5.80, pod_count=1),
        ]
        by_env = [
            AggregatedCostItem(dimension="environment", value="production", total_cost=99.10, pod_count=2),
            AggregatedCostItem(dimension="environment", value="staging", total_cost=5.80, pod_count=1),
        ]
        by_team = [
            AggregatedCostItem(dimension="team", value="platform", total_cost=24.10, pod_count=1),
            AggregatedCostItem(dimension="team", value="backend", total_cost=75.00, pod_count=1),
            AggregatedCostItem(dimension="team", value="frontend", total_cost=5.80, pod_count=1),
        ]

        summary = CostSummary(
            total_cost=104.90,
            pod_count=3,
            by_service=by_svc,
            by_environment=by_env,
            by_team=by_team,
        )
        assert summary.total_cost == 104.90
        assert summary.pod_count == 3
        assert len(summary.by_service) == 3
        assert len(summary.by_environment) == 2
        assert len(summary.by_team) == 3


# ── Tests: CostQueryParams ──────────────────────────────


class TestCostQueryParams:
    def test_defaults(self):
        params = CostQueryParams()
        assert params.aggregation == "service"
        assert params.window == "7d"
        assert params.granularity == "day"

    def test_custom_params(self):
        params = CostQueryParams(
            aggregation="environment",
            window="7d",
            service="api",
            environment="production",
            team="platform",
            granularity=CostGranularity.WEEK,
        )
        assert params.aggregation == "environment"
        assert params.window == "7d"
        assert params.service == "api"
        assert params.environment == "production"
        assert params.team == "platform"
        assert params.granularity == CostGranularity.WEEK

    def test_serialize(self):
        params = CostQueryParams(aggregation="team", window="30d")
        d = params.model_dump()
        assert d["aggregation"] == "team"
        assert d["window"] == "30d"


# ── Tests: CostTrendPoint / CostTrendSeries ─────────────


class TestCostTrends:
    def test_trend_point(self):
        point = CostTrendPoint(timestamp="2026-05-29T10:00:00Z", total_cost=42.50)
        d = point.model_dump()
        assert d["total_cost"] == 42.50
        assert d["timestamp"] == "2026-05-29T10:00:00Z"

    def test_trend_series(self):
        points = [
            CostTrendPoint(timestamp="2026-05-29T10:00:00Z", total_cost=10.0),
            CostTrendPoint(timestamp="2026-05-29T11:00:00Z", total_cost=12.0),
        ]
        series = CostTrendSeries(
            dimension="service",
            value="api-gateway",
            points=points,
            total=22.0,
        )
        assert series.dimension == "service"
        assert len(series.points) == 2
        assert series.total == 22.0


# ── Tests: CostDashboardResponse ─────────────────────────


class TestCostDashboardResponse:
    def test_create(self, sample_pods):
        summary = CostSummary(
            total_cost=104.90,
            pod_count=3,
            by_service=[],
            by_environment=[],
            by_team=[],
        )
        params = CostQueryParams(aggregation="service", window="7d")
        resp = CostDashboardResponse(
            summary=summary,
            query=params,
            generated_at="2026-05-29T12:00:00Z",
            opencost_status="ok",
            data_freshness_seconds=30,
        )
        assert resp.summary.total_cost == 104.90
        assert resp.data_freshness_seconds == 30
        assert resp.opencost_status == "ok"


# ── Tests: K8s Webhook Label Resolution ─────────────────


class TestK8sWebhookLabels:
    """Test the label resolution and patch generation logic.

    These tests validate the core webhook logic from k8s_webhook_handler.py
    by importing the pure functions (no FastAPI dependency needed).
    """

    def test_resolve_labels_from_pod_metadata(self):
        """Labels are resolved from Pod metadata labels."""
        from agents.k8s_webhook_handler import _resolve_labels

        config = CostLabelConfig()
        pod_meta = {"name": "my-app-7f8d", "labels": {"app": "my-app"}}
        ns_annot = {"cost.opencost.io/environment": "production"}

        resolved = _resolve_labels(pod_meta, ns_annot, config)

        assert resolved["environment"] == "production"
        assert resolved["service"] == "my-app"  # from app label
        assert resolved["team"] == "platform"  # default
        assert resolved["component"] == "application"  # default

    def test_resolve_labels_existing_take_priority(self):
        """Existing Pod labels have highest priority."""
        from agents.k8s_webhook_handler import _resolve_labels

        config = CostLabelConfig()
        pod_meta = {
            "name": "worker-abc",
            "labels": {
                "environment": "staging",
                "team": "backend",
                "service": "worker-svc",
                "component": "worker",
            },
        }
        ns_annot = {"cost.opencost.io/environment": "production"}  # should be ignored

        resolved = _resolve_labels(pod_meta, ns_annot, config)

        assert resolved["environment"] == "staging"  # existing label wins
        assert resolved["team"] == "backend"
        assert resolved["service"] == "worker-svc"
        assert resolved["component"] == "worker"

    def test_resolve_labels_from_k8s_recommended_labels(self):
        """Kubernetes recommended labels (app.kubernetes.io/*) are recognized."""
        from agents.k8s_webhook_handler import _resolve_labels

        config = CostLabelConfig()
        pod_meta = {
            "name": "my-app-7f8d",
            "labels": {
                "app.kubernetes.io/name": "backend-api",
                "app.kubernetes.io/component": "server",
            },
        }

        resolved = _resolve_labels(pod_meta, {}, config)

        assert resolved["service"] == "backend-api"  # from k8s recommended label
        assert resolved["component"] == "server"

    def test_resolve_labels_fallback_to_pod_name(self):
        """When no service label is present, fallback to pod name."""
        from agents.k8s_webhook_handler import _resolve_labels

        config = CostLabelConfig()
        pod_meta = {"name": "mystery-pod-12345"}

        resolved = _resolve_labels(pod_meta, {}, config)

        assert resolved["service"] == "mystery-pod-12345"

    def test_build_patch_adds_new_labels(self):
        """JSON Patch is generated for labels that don't already exist."""
        from agents.k8s_webhook_handler import _build_json_patch

        config = CostLabelConfig()
        existing = {"app": "backend"}
        resolved = {
            "environment": "production",
            "team": "sre",
            "service": "backend",
            "component": "api",
        }

        patches = _build_json_patch("backend-abc", existing, resolved, config)

        assert len(patches) == 1
        assert patches[0]["op"] == "add"
        assert patches[0]["path"] == "/metadata/labels"
        add_labels = patches[0]["value"]
        # All four cost labels + their prefixed versions should be added
        assert "environment" in add_labels
        assert "team" in add_labels
        assert "service" in add_labels
        assert "component" in add_labels
        assert f"{config.label_prefix}/environment" in add_labels

    def test_build_patch_noop_when_all_labels_exist(self):
        """No patch generated when all labels are already present."""
        from agents.k8s_webhook_handler import _build_json_patch

        config = CostLabelConfig()
        existing_all = {
            "environment": "prod", "team": "sre", "service": "proxy", "component": "gateway",
            f"{config.label_prefix}/environment": "prod",
            f"{config.label_prefix}/team": "sre",
            f"{config.label_prefix}/service": "proxy",
            f"{config.label_prefix}/component": "gateway",
        }
        resolved = {"environment": "prod", "team": "sre", "service": "proxy", "component": "gateway"}

        patches = _build_json_patch("proxy-abc", existing_all, resolved, config)

        assert len(patches) == 0


# ── Tests: Cost API Routes (import-level) ───────────────


class TestCostRoutes:
    def test_router_exists(self):
        """Cost routes router can be imported."""
        from agents.cost_routes import router as cost_router
        assert cost_router is not None
        routes = [r.path for r in cost_router.routes]
        assert "/cost/summary" in routes
        assert "/cost/by-service" in routes
        assert "/cost/by-environment" in routes
        assert "/cost/by-team" in routes
        assert "/cost/trends" in routes
        assert "/cost/pods" in routes
        assert "/cost/health" in routes

    def test_webhook_router_exists(self):
        """K8s webhook router can be imported."""
        from agents.k8s_webhook_handler import webhook_router
        assert webhook_router is not None
        routes = [r.path for r in webhook_router.routes]
        assert "/webhook/mutate-cost-labels" in routes
        assert "/webhook/mutate-cost-labels/health" in routes
        assert "/webhook/mutate-cost-labels/dry-run" in routes
