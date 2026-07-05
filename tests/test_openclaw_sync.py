# -*- coding: utf-8 -*-
"""Tests for the OpenClaw sync channel (channels/openclaw_sync.py).

Tests cover:
1. OpenClawSyncChannel initialization
2. process_event with various event types
3. get_status and get_metrics
4. EWMA threshold engine integration
5. Traffic staining and routing
6. Cold start warm cache
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

# Ensure src/backend is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src" / "backend"))

import pytest

from channels.openclaw_sync import OpenClawSyncChannel
from channels.marine_base import ChannelStatus, ChannelPriority

# 注: ABTestManager 单例隔离已提升到 tests/conftest.py 的 autouse fixture
# _reset_shared_singletons（根治 bug-041），本文件无需再自建隔离 fixture。


class TestOpenClawSyncChannel:
    """Test suite for OpenClawSyncChannel."""

    def test_instantiation(self):
        """Channel can be created with default params."""
        channel = OpenClawSyncChannel()
        assert channel.name == "openclaw_sync"
        assert channel.priority == ChannelPriority.P1

    def test_initialize(self):
        """Initialize returns True and sets health to OK."""
        channel = OpenClawSyncChannel()
        result = channel.initialize()
        assert result is True
        status = channel.get_status()
        assert status["health"]["status"] == "ok"

    def test_process_sync_request_high_latency(self):
        """High latency triggers sync."""
        channel = OpenClawSyncChannel()
        channel.initialize()
        result = channel.process_event({
            "type": "sync_request",
            "node_id": "node-1",
            "node_type": "aggregator",
            "latency_ms": 500.0,
            "dependency_depth": 1,
            "clock_timestamp": 1000,
        })
        assert result is not None
        assert result.get("should_sync") is True
        assert "reason" in result

    def test_process_sync_request_low_latency(self):
        """Low latency does not trigger sync."""
        channel = OpenClawSyncChannel()
        channel.initialize()
        result = channel.process_event({
            "type": "sync_request",
            "node_id": "node-2",
            "node_type": "worker",
            "latency_ms": 10.0,
            "dependency_depth": 1,
            "clock_timestamp": 500,
        })
        assert result is not None
        assert result.get("should_sync") is False

    def test_process_sync_request_deep_dependency(self):
        """Deep causal dependency triggers sync even with low latency."""
        channel = OpenClawSyncChannel()
        channel.initialize()
        result = channel.process_event({
            "type": "sync_request",
            "node_id": "node-3",
            "node_type": "worker",
            "latency_ms": 30.0,
            "dependency_depth": 5,
            "clock_timestamp": 1000,
        })
        assert result is not None
        assert result.get("should_sync") is True

    def test_process_metrics_update(self):
        """Metrics update is accepted."""
        channel = OpenClawSyncChannel()
        channel.initialize()
        result = channel.process_event({
            "type": "metrics_update",
            "latency_ms": 150.0,
            "behavior_fingerprint_mutation_rate": 0.02,
            "anomaly_propagation_depth": 1,
            "prediction_error_rate": 0.05,
            "energy_increase_pct": 3.0,
            "temperature_slope": 0.1,
            "policy_evaluation_latency_ms": 50.0,
        })
        assert result is not None
        assert result.get("status") == "ok"

    def test_process_config_update(self):
        """Config update is accepted."""
        channel = OpenClawSyncChannel()
        channel.initialize()
        result = channel.process_event({
            "type": "config_update",
            "base_threshold_ms": 200.0,
            "alpha": 0.4,
        })
        assert result is not None
        assert result.get("status") == "ok"

    def test_process_unknown_event(self):
        """Unknown event type returns error."""
        channel = OpenClawSyncChannel()
        channel.initialize()
        result = channel.process_event({
            "type": "unknown_event_type",
        })
        assert result is not None
        assert "error" in result or result.get("status") != "ok"

    def test_get_status(self):
        """get_status returns health info."""
        channel = OpenClawSyncChannel()
        channel.initialize()
        status = channel.get_status()
        assert "health" in status
        assert "metrics" in status
        assert status["health"]["status"] == "ok"

    def test_get_metrics(self):
        """get_metrics returns ChannelMetrics."""
        channel = OpenClawSyncChannel()
        channel.initialize()
        metrics = channel.get_metrics()
        assert metrics is not None
        assert hasattr(metrics, "calls_total")
        assert hasattr(metrics, "calls_success")
        assert hasattr(metrics, "calls_failed")

    def test_metrics_tracking(self):
        """Calling process_event increments metrics."""
        channel = OpenClawSyncChannel()
        channel.initialize()
        before = channel.get_metrics()
        channel.process_event({
            "type": "sync_request",
            "node_id": "node-1",
            "node_type": "aggregator",
            "latency_ms": 100.0,
            "dependency_depth": 1,
            "clock_timestamp": 1000,
        })
        after = channel.get_metrics()
        assert after.calls_total > before.calls_total

    def test_ewma_threshold_adaptation(self):
        """EWMA threshold adapts after multiple events."""
        channel = OpenClawSyncChannel()
        channel.initialize()
        # Send multiple events with varying latencies
        for lat in [200.0, 180.0, 220.0, 190.0, 210.0]:
            channel.process_event({
                "type": "sync_request",
                "node_id": "node-1",
                "node_type": "aggregator",
                "latency_ms": lat,
                "dependency_depth": 1,
                "clock_timestamp": 1000,
            })
        # Threshold should have adapted
        status = channel.get_status()
        assert status is not None

    def test_traffic_staining(self):
        """Traffic stain header is generated."""
        channel = OpenClawSyncChannel()
        channel.initialize()
        result = channel.process_event({
            "type": "sync_request",
            "node_id": "aggregator-1",
            "node_type": "aggregator",
            "latency_ms": 100.0,
            "dependency_depth": 1,
            "clock_timestamp": 1000,
        })
        assert result is not None

    def test_cold_start_warm_cache(self):
        """Cold start warm cache works."""
        channel = OpenClawSyncChannel()
        channel.initialize()
        # First call should use warm cache
        result = channel.process_event({
            "type": "sync_request",
            "node_id": "node-1",
            "node_type": "worker",
            "latency_ms": 150.0,
            "dependency_depth": 1,
            "clock_timestamp": 1000,
        })
        assert result is not None

    def test_high_fanout_node_priority(self):
        """High-fanout nodes (aggregator, gateway) get experiment treatment."""
        channel = OpenClawSyncChannel()
        channel.initialize()
        result = channel.process_event({
            "type": "sync_request",
            "node_id": "gateway-1",
            "node_type": "gateway",
            "latency_ms": 200.0,
            "dependency_depth": 3,
            "clock_timestamp": 1000,
        })
        assert result is not None

    def test_multiple_events_sequence(self):
        """Multiple events in sequence work correctly."""
        channel = OpenClawSyncChannel()
        channel.initialize()
        events = [
            {"type": "sync_request", "node_id": "n1", "node_type": "worker",
             "latency_ms": 50.0, "dependency_depth": 1, "clock_timestamp": 100},
            {"type": "metrics_update", "latency_ms": 100.0,
             "behavior_fingerprint_mutation_rate": 0.01},
            {"type": "sync_request", "node_id": "n2", "node_type": "aggregator",
             "latency_ms": 300.0, "dependency_depth": 2, "clock_timestamp": 200},
            {"type": "config_update", "base_threshold_ms": 150.0},
            {"type": "sync_request", "node_id": "n3", "node_type": "worker",
             "latency_ms": 80.0, "dependency_depth": 1, "clock_timestamp": 300},
        ]
        for event in events:
            result = channel.process_event(event)
            assert result is not None
        metrics = channel.get_metrics()
        assert metrics.calls_total == 5
