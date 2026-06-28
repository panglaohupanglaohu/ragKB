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
