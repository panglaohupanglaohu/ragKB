from __future__ import annotations

from agents.cost_aggregator import CostAggregator


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
