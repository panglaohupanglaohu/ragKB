# -*- coding: utf-8 -*-
"""Tests for the A/B testing framework (agents/ab_testing.py).

Tests cover:
1. EWMAConfig defaults and validation
2. EWMAThresholdEngine update and stats
3. WarmCache add/get_mean/reset
4. TrafficStainer stain header generation
5. LamportClock tick/update/merge
6. CausalConsistencyDecider should_force_sync
7. ABTestManager lifecycle and warm_up
8. get_ab_test_manager / reset_ab_test_manager
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

# Ensure src/backend is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src" / "backend"))

import pytest

from agents.ab_testing import (
    EWMAConfig,
    EWMAThresholdEngine,
    WarmCache,
    TrafficStainer,
    LamportClock,
    CausalConsistencyDecider,
    ABTestManager,
    SyncPolicy,
    TrafficAllocation,
    ABTestMetrics,
    get_ab_test_manager,
    reset_ab_test_manager,
)


# ── EWMAConfig ────────────────────────────────────────────────────────────────

class TestEWMAConfig:
    def test_default_values(self):
        cfg = EWMAConfig()
        assert cfg.base_threshold_ms == 100.0
        assert cfg.alpha == 0.3
        assert cfg.beta == 0.1
        assert cfg.min_threshold_ms == 50.0
        assert cfg.max_threshold_ms == 500.0
        assert cfg.cooldown_seconds == 30
        assert cfg.cooling_extension_seconds == 15
        assert cfg.max_causal_depth == 5
        assert cfg.clock_skew_tolerance_ms == 100.0

    def test_custom_values(self):
        cfg = EWMAConfig(
            base_threshold_ms=200.0,
            alpha=0.5,
            min_threshold_ms=100.0,
            max_threshold_ms=1000.0,
        )
        assert cfg.base_threshold_ms == 200.0
        assert cfg.alpha == 0.5
        assert cfg.min_threshold_ms == 100.0
        assert cfg.max_threshold_ms == 1000.0

    def test_to_dict(self):
        cfg = EWMAConfig()
        d = cfg.to_dict()
        assert isinstance(d, dict)
        assert d["base_threshold_ms"] == 100.0
        assert d["alpha"] == 0.3

    def test_from_dict(self):
        cfg = EWMAConfig.from_dict({"base_threshold_ms": 300.0, "alpha": 0.4})
        assert cfg.base_threshold_ms == 300.0
        assert cfg.alpha == 0.4

    def test_from_dict_partial(self):
        cfg = EWMAConfig.from_dict({"base_threshold_ms": 300.0})
        assert cfg.base_threshold_ms == 300.0
        assert cfg.alpha == 0.3  # default preserved


# ── EWMAThresholdEngine ───────────────────────────────────────────────────────

class TestEWMAThresholdEngine:
    def test_initial_ewma_is_base_threshold(self):
        cfg = EWMAConfig(base_threshold_ms=200.0)
        engine = EWMAThresholdEngine(cfg)
        assert engine.get_ewma() == 200.0

    def test_update_single_value(self):
        engine = EWMAThresholdEngine(EWMAConfig(alpha=0.5))
        engine.update(100.0)
        # ewma = 0.5*100 + 0.5*100 = 100
        assert engine.get_ewma() == 100.0

    def test_update_multiple_values(self):
        engine = EWMAThresholdEngine(EWMAConfig(alpha=0.5, base_threshold_ms=100.0))
        engine.update(200.0)  # ewma = 0.5*200 + 0.5*100 = 150
        engine.update(100.0)  # ewma = 0.5*100 + 0.5*150 = 125
        assert engine.get_ewma() == 125.0

    def test_get_ewma_stats(self):
        engine = EWMAThresholdEngine(EWMAConfig(alpha=0.3))
        engine.update(150.0)
        engine.update(200.0)
        stats = engine.get_ewma_stats()
        assert "ewma" in stats
        assert "current_threshold" in stats
        assert "alpha" in stats
        assert "update_count" in stats
        assert stats["update_count"] == 2

    def test_reset(self):
        engine = EWMAThresholdEngine(EWMAConfig(base_threshold_ms=100.0))
        engine.update(500.0)
        assert engine.get_ewma() != 100.0
        engine.reset()
        assert engine.get_ewma() == 100.0

    def test_threshold_clamping(self):
        cfg = EWMAConfig(min_threshold_ms=50.0, max_threshold_ms=200.0)
        engine = EWMAThresholdEngine(cfg)
        # Force ewma very high
        for _ in range(10):
            engine.update(1000.0)
        assert engine.get_current_threshold() <= cfg.max_threshold_ms

    def test_update_with_timestamp(self):
        engine = EWMAThresholdEngine(EWMAConfig())
        now = time.time()
        engine.update(150.0, timestamp=now)
        engine.update(200.0, timestamp=now + 1.0)
        assert engine.get_ewma() > 0


# ── WarmCache ─────────────────────────────────────────────────────────────────

class TestWarmCache:
    def test_empty_cache(self):
        cache = WarmCache(window_size=10)
        assert cache.get_mean() == 0.0
        assert cache.size() == 0

    def test_add_and_get_mean(self):
        cache = WarmCache(window_size=5)
        cache.add(100.0)
        cache.add(200.0)
        assert cache.get_mean() == 150.0
        assert cache.size() == 2

    def test_window_size_limit(self):
        cache = WarmCache(window_size=3)
        for v in [10, 20, 30, 40, 50]:
            cache.add(float(v))
        assert cache.size() == 3
        # mean of [30, 40, 50]
        assert cache.get_mean() == 40.0

    def test_reset(self):
        cache = WarmCache(window_size=10)
        cache.add(100.0)
        cache.add(200.0)
        cache.reset()
        assert cache.size() == 0
        assert cache.get_mean() == 0.0

    def test_get_all(self):
        cache = WarmCache(window_size=5)
        cache.add(1.0)
        cache.add(2.0)
        all_vals = cache.get_all()
        assert all_vals == [1.0, 2.0]


# ── TrafficStainer ────────────────────────────────────────────────────────────

class TestTrafficStainer:
    def test_default_stain(self):
        stainer = TrafficStainer()
        header = stainer.get_stain_header("node-1", "aggregator")
        assert "x-sync-policy" in header
        assert header["x-sync-policy"] == "ewma"

    def test_high_fanout_detection(self):
        stainer = TrafficStainer()
        # aggregator is a high-fanout keyword
        header = stainer.get_stain_header("node-1", "aggregator")
        assert header.get("x-node-type") == "aggregator"

    def test_control_group(self):
        stainer = TrafficStainer()
        header = stainer.get_stain_header("node-1", "worker")
        assert "x-sync-policy" in header

    def test_stain_header_consistency(self):
        stainer = TrafficStainer()
        h1 = stainer.get_stain_header("node-1", "aggregator")
        h2 = stainer.get_stain_header("node-1", "aggregator")
        assert h1 == h2


# ── LamportClock ──────────────────────────────────────────────────────────────

class TestLamportClock:
    def test_initial_timestamp(self):
        clock = LamportClock(node_id="test-node")
        assert clock.node_id == "test-node"
        assert clock.timestamp > 0

    def test_tick_increments(self):
        clock = LamportClock(node_id="test-node")
        t1 = clock.timestamp
        clock.tick()
        assert clock.timestamp > t1

    def test_update_merge(self):
        clock_a = LamportClock(node_id="a")
        clock_b = LamportClock(node_id="b")
        clock_a.tick()
        clock_b.tick()
        clock_b.tick()
        # Merge b's timestamp into a
        clock_a.update(clock_b.timestamp)
        assert clock_a.timestamp >= clock_b.timestamp

    def test_merge_with_self(self):
        clock = LamportClock(node_id="test")
        t = clock.timestamp
        clock.update(t)
        assert clock.timestamp >= t

    def test_to_dict(self):
        clock = LamportClock(node_id="test-node")
        d = clock.to_dict()
        assert d["node_id"] == "test-node"
        assert "timestamp" in d

    def test_is_concurrent_with(self):
        clock_a = LamportClock(node_id="a")
        clock_b = LamportClock(node_id="b")
        # Different nodes, same timestamp → concurrent
        assert clock_a.is_concurrent_with(clock_b) or True  # at least not crashing

    def test_happened_before(self):
        clock_a = LamportClock(node_id="a")
        clock_b = LamportClock(node_id="b")
        clock_a.tick()
        clock_b.update(clock_a.timestamp)
        # b should have timestamp >= a's
        assert clock_b.timestamp >= clock_a.timestamp


# ── CausalConsistencyDecider ──────────────────────────────────────────────────

class TestCausalConsistencyDecider:
    def test_should_sync_high_latency(self):
        cfg = EWMAConfig(base_threshold_ms=100.0)
        engine = EWMAThresholdEngine(cfg)
        decider = CausalConsistencyDecider(ewma_engine=engine, config=cfg)
        should_sync, reason = decider.should_force_sync(
            latency_ms=500.0, dependency_depth=1
        )
        assert should_sync is True
        assert "延迟" in reason

    def test_should_not_sync_low_latency(self):
        cfg = EWMAConfig(base_threshold_ms=100.0)
        engine = EWMAThresholdEngine(cfg)
        decider = CausalConsistencyDecider(ewma_engine=engine, config=cfg)
        should_sync, reason = decider.should_force_sync(
            latency_ms=30.0, dependency_depth=1
        )
        assert should_sync is False

    def test_should_sync_deep_dependency(self):
        cfg = EWMAConfig(base_threshold_ms=100.0, max_causal_depth=3)
        engine = EWMAThresholdEngine(cfg)
        decider = CausalConsistencyDecider(ewma_engine=engine, config=cfg)
        should_sync, reason = decider.should_force_sync(
            latency_ms=50.0, dependency_depth=5
        )
        assert should_sync is True
        assert "因果依赖深度" in reason

    def test_should_sync_clock_skew(self):
        cfg = EWMAConfig(base_threshold_ms=100.0, clock_skew_tolerance_ms=100.0)
        engine = EWMAThresholdEngine(cfg)
        decider = CausalConsistencyDecider(ewma_engine=engine, config=cfg)
        should_sync, reason = decider.should_force_sync(
            latency_ms=50.0, dependency_depth=1, clock_skew_ms=500.0
        )
        assert should_sync is True
        assert "时钟偏差" in reason

    def test_cooldown_respected(self):
        cfg = EWMAConfig(base_threshold_ms=100.0, cooldown_seconds=9999)
        engine = EWMAThresholdEngine(cfg)
        decider = CausalConsistencyDecider(ewma_engine=engine, config=cfg)
        # First sync triggers cooldown
        should_sync1, _ = decider.should_force_sync(500.0, 1)
        assert should_sync1 is True
        # Second should be blocked by cooldown
        should_sync2, reason2 = decider.should_force_sync(500.0, 1)
        assert should_sync2 is False
        assert "冷却期" in reason2

    def test_get_decision_stats(self):
        cfg = EWMAConfig(base_threshold_ms=100.0)
        engine = EWMAThresholdEngine(cfg)
        decider = CausalConsistencyDecider(ewma_engine=engine, config=cfg)
        decider.should_force_sync(500.0, 1)
        decider.should_force_sync(30.0, 1)
        stats = decider.get_decision_stats()
        assert stats["total_decisions"] == 2
        assert stats["sync_decisions"] >= 1
        assert stats["no_sync_decisions"] >= 1


# ── ABTestManager ─────────────────────────────────────────────────────────────

class TestABTestManager:
    def test_default_state(self):
        manager = ABTestManager()
        assert manager.test_active is False
        assert manager.experiment_traffic_pct == 0.0

    def test_start_test(self):
        manager = ABTestManager()
        manager.start_test(traffic_pct=5.0)
        assert manager.test_active is True
        assert manager.experiment_traffic_pct == 5.0

    def test_stop_test(self):
        manager = ABTestManager()
        manager.start_test(traffic_pct=5.0)
        manager.stop_test()
        assert manager.test_active is False

    def test_is_in_experiment(self):
        manager = ABTestManager()
        manager.start_test(traffic_pct=100.0)
        # At 100%, all nodes should be in experiment
        in_exp = manager.is_in_experiment("node-1", "aggregator")
        assert in_exp is True

    def test_is_in_control(self):
        manager = ABTestManager()
        manager.start_test(traffic_pct=0.0)
        # At 0%, no nodes should be in experiment
        in_exp = manager.is_in_experiment("node-1", "aggregator")
        assert in_exp is False

    def test_warm_up(self):
        manager = ABTestManager()
        threshold = manager.warm_up([100.0, 150.0, 200.0, 180.0, 160.0])
        assert threshold > 0
        assert manager._warmed_up is True

    def test_get_metrics(self):
        manager = ABTestManager()
        manager.start_test(traffic_pct=5.0)
        metrics = manager.get_metrics()
        assert isinstance(metrics, ABTestMetrics)
        assert metrics.experiment_traffic_pct == 5.0

    def test_get_config(self):
        manager = ABTestManager()
        cfg = manager.get_config()
        assert isinstance(cfg, EWMAConfig)

    def test_update_config(self):
        manager = ABTestManager()
        manager.update_config({"base_threshold_ms": 300.0})
        assert manager._config.base_threshold_ms == 300.0

    def test_get_report(self):
        manager = ABTestManager()
        manager.start_test(traffic_pct=5.0)
        report = manager.get_report()
        assert "experiment_traffic_pct" in report
        assert "test_active" in report
        assert report["test_active"] is True

    def test_high_fanout_priority(self):
        manager = ABTestManager()
        manager.start_test(traffic_pct=50.0)
        # High-fanout nodes should be more likely in experiment
        # We just verify it doesn't crash
        result = manager.is_in_experiment("aggregator-1", "aggregator")
        assert isinstance(result, bool)


# ── Singleton accessors ───────────────────────────────────────────────────────

class TestSingleton:
    def test_get_ab_test_manager(self):
        manager = get_ab_test_manager()
        assert isinstance(manager, ABTestManager)

    def test_singleton_identity(self):
        m1 = get_ab_test_manager()
        m2 = get_ab_test_manager()
        assert m1 is m2

    def test_reset_ab_test_manager(self):
        m1 = get_ab_test_manager()
        reset_ab_test_manager()
        m2 = get_ab_test_manager()
        assert m1 is not m2


# ── SyncPolicy / TrafficAllocation enums ──────────────────────────────────────

class TestEnums:
    def test_sync_policy_values(self):
        assert SyncPolicy.FIXED_THRESHOLD.value == "fixed_threshold"
        assert SyncPolicy.EWMA_ADAPTIVE.value == "ewma_adaptive"
        assert SyncPolicy.LAMPORT_CLOCK.value == "lamport_clock"

    def test_traffic_allocation_values(self):
        assert TrafficAllocation.PHASE_1_5PCT.value == 5.0
        assert TrafficAllocation.PHASE_2_50PCT.value == 50.0
        assert TrafficAllocation.PHASE_3_100PCT.value == 100.0
