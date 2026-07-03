from __future__ import annotations

import asyncio

from agents.cost_aggregator import CostAggregator
from agents.cost_models import CostQueryParams


def _allocation(name: str, total: float, service: str = "svc"):
    return {
        "name": name,
        "properties": {
            "pod": name,
            "namespace": "agentsgroup",
            "container": "app",
            "labels": {"service": service, "team": "platform", "environment": "prod"},
        },
        "totalCost": total,
        "cpuCost": total,
    }


def _pod(aggregator: CostAggregator, name: str, total: float, service: str = "svc"):
    pod = aggregator._pod_from_entry(_allocation(name, total, service=service))
    assert pod is not None
    return pod


def test_parse_allocation_response_accepts_direct_list_and_sorts_by_cost():
    aggregator = CostAggregator()

    pods = aggregator._parse_allocation_response(
        [
            _allocation("pod-low", 1.5),
            "invalid",
            _allocation("pod-high", 3.0),
        ]
    )

    assert [pod.pod for pod in pods] == ["pod-high", "pod-low"]
    assert [pod.total_cost for pod in pods] == [3.0, 1.5]


def test_parse_allocation_response_accepts_data_dict_values():
    aggregator = CostAggregator()

    pods = aggregator._parse_allocation_response(
        {
            "data": {
                "pod-a": _allocation("pod-a", 2.0),
                "pod-b": _allocation("pod-b", 1.0),
            }
        }
    )

    assert [pod.pod for pod in pods] == ["pod-a", "pod-b"]


def test_parse_allocation_response_unwraps_multi_pod_entries():
    aggregator = CostAggregator()

    pods = aggregator._parse_allocation_response(
        {
            "data": [
                {
                    "pod-a": _allocation("pod-a", 2.0, service="api"),
                    "pod-b": _allocation("pod-b", 1.0, service="worker"),
                }
            ]
        }
    )

    assert [pod.pod for pod in pods] == ["pod-a", "pod-b"]
    assert [pod.labels["service"] for pod in pods] == ["api", "worker"]


def test_pod_from_entry_applies_namespace_and_team_fallbacks():
    aggregator = CostAggregator()

    pod = aggregator._pod_from_entry(
        {
            "name": "cluster/agentsgroup-build-system-abc123",
            "properties": {
                "pod": "agentsgroup-build-system-abc123",
                "namespace": "agentsgroup",
                "labels": {},
            },
            "cpuCost": 1.0,
            "ramCost": 2.0,
        }
    )

    assert pod is not None
    assert pod.total_cost == 3.0
    assert pod.labels["service"] == "agentsgroup-backend"
    assert pod.labels["environment"] == "production"
    assert pod.labels["team"] == "build_system"


def test_pod_from_entry_converts_ram_byte_hours_and_window():
    aggregator = CostAggregator()

    pod = aggregator._pod_from_entry(
        {
            "name": "pod-window",
            "properties": {
                "namespace": "opencost",
                "container": "collector",
                "ramByteHours": 2 * 1024 ** 3,
            },
            "totalCost": 5.0,
            "window": {"start": "2026-01-01T00:00:00Z", "end": "2026-01-02T00:00:00Z"},
        }
    )

    assert pod is not None
    assert pod.ram_gb_hours == 2.0
    assert pod.labels["service"] == "opencost"
    assert pod.window_start == "2026-01-01T00:00:00Z"
    assert pod.window_end == "2026-01-02T00:00:00Z"


def test_aggregate_groups_by_dimension_and_calculates_percentages():
    aggregator = CostAggregator()
    pods = [
        _pod(aggregator, "pod-api-a", 6.0, service="api"),
        _pod(aggregator, "pod-api-b", 2.0, service="api"),
        _pod(aggregator, "pod-worker", 2.0, service="worker"),
    ]

    items = aggregator._aggregate(pods, "service", total=10.0)

    assert [item.value for item in items] == ["api", "worker"]
    assert items[0].total_cost == 8.0
    assert items[0].cpu_cost == 8.0
    assert items[0].pod_count == 2
    assert items[0].container_count == 1
    assert items[0].percentage == 80.0
    assert items[1].percentage == 20.0


def test_get_summary_builds_totals_counts_and_top_aggregations():
    aggregator = CostAggregator()
    pods = [
        _pod(aggregator, "pod-api", 5.0, service="api"),
        _pod(aggregator, "pod-worker", 3.0, service="worker"),
        _pod(aggregator, "pod-api-2", 2.0, service="api"),
    ]
    aggregator._cache.update(pods, window_start="7d", window_end="now")

    summary = asyncio.run(aggregator.get_summary(CostQueryParams(window="7d")))

    assert summary.total_cost == 10.0
    assert summary.cpu_cost == 10.0
    assert summary.pod_count == 3
    assert summary.container_count == 3
    assert summary.service_count == 2
    assert summary.environment_count == 1
    assert summary.team_count == 1
    assert summary.namespace_count == 1
    assert [item.value for item in summary.by_service] == ["api", "worker"]
    assert [item.total_cost for item in summary.by_service] == [7.0, 3.0]
    assert summary.window_start == "7d"
    assert summary.window_end == "now"


def test_compute_trends_preserves_window_point_count_and_totals():
    aggregator = CostAggregator()
    pods = [
        _pod(aggregator, "pod-api", 7.0, service="api"),
        _pod(aggregator, "pod-worker", 3.0, service="worker"),
    ]

    trends = aggregator._compute_trends(
        pods,
        aggregation="service",
        granularity="daily",
        window="7d",
    )

    assert [trend.value for trend in trends] == ["api", "worker"]
    assert trends[0].total == 7.0
    assert trends[0].avg_daily == 1.0
    assert len(trends[0].points) == 8
    assert all(point.total_cost == 1.0 for point in trends[0].points)
