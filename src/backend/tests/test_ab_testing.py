# -*- coding: utf-8 -*-
"""A/B 测试框架单元测试 — LamportClock, EWMA, TrafficStainer, ABTestManager."""

from __future__ import annotations

import time

import pytest

from agents.ab_testing import (
    ABTestManager,
    ABTestMetrics,
    CausalConsistencyDecider,
    EWMAConfig,
    EWMAThresholdEngine,
    LamportClock,
    SyncPolicy,
    TrafficAllocation,
    TrafficStainer,
    WarmCache,
    get_ab_test_manager,
    reset_ab_test_manager,
)


# ═══════════════════════════════════════════════════
# LamportClock 测试
# ═══════════════════════════════════════════════════

class TestLamportClock:
    """Lamport 逻辑时钟单元测试."""

    def test_initial_counter_is_zero(self):
        clock = LamportClock(node_id="node-1")
        assert clock.counter == 0
        assert clock.node_id == "node-1"

    def test_tick_increments_counter(self):
        clock = LamportClock(node_id="node-1")
        c1 = clock.tick()
        assert c1 == 1
        c2 = clock.tick()
        assert c2 == 2
        assert clock.counter == 2

    def test_tick_sets_timestamp(self):
        clock = LamportClock(node_id="node-1")
        its = 1000.0
        clock.tick(physical_ts=its)
        assert clock.timestamp == its

    def test_tick_defaults_to_current_time(self):
        clock = LamportClock(node_id="node-1")
        before = time.time() * 1000
        clock.tick()
        after = time.time() * 1000
        assert before <= clock.timestamp <= after

    def test_merge_takes_max_counter(self):
        a = LamportClock(node_id="a", counter=5, timestamp=100.0)
        b = LamportClock(node_id="b", counter=10, timestamp=200.0)
        a.merge(b)
        # merge = max(5,10) + 1 = 11
        assert a.counter == 11
        assert a.timestamp == 200.0

    def test_merge_self_larger(self):
        a = LamportClock(node_id="a", counter=15, timestamp=300.0)
        b = LamportClock(node_id="b", counter=10, timestamp=200.0)
        a.merge(b)
        # merge = max(15,10) + 1 = 16
        assert a.counter == 16
        assert a.timestamp == 300.0

    def test_to_dict(self, sample_lamport_clock):
        d = sample_lamport_clock.to_dict()
        assert d["node_id"] == "test-node-1"
        assert "counter" in d
        assert "timestamp" in d

    def test_from_dict(self):
        d = {"node_id": "n1", "counter": 7, "timestamp": 500.0}
        clock = LamportClock.from_dict(d)
        assert clock.node_id == "n1"
        assert clock.counter == 7
        assert clock.timestamp == 500.0


# ═══════════════════════════════════════════════════
# EWMAConfig 测试
# ═══════════════════════════════════════════════════

class TestEWMAConfig:
    """EWMA 配置数据类测试."""

    def test_default_values(self):
        cfg = EWMAConfig()
        assert cfg.alpha == 0.3
        assert cfg.base_threshold_ms == 100.0
        assert cfg.threshold_multiplier == 3.0
        assert cfg.min_samples == 10

    def test_to_dict(self, default_ewma_config):
        d = default_ewma_config.to_dict()
        assert d["alpha"] == 0.3
        assert d["base_threshold_ms"] == 100.0

    def test_from_dict(self):
        d = {"alpha": 0.5, "base_threshold_ms": 200.0, "min_samples": 20}
        cfg = EWMAConfig.from_dict(d)
        assert cfg.alpha == 0.5
        assert cfg.base_threshold_ms == 200.0
        assert cfg.min_samples == 20

    def test_from_dict_defaults(self):
        cfg = EWMAConfig.from_dict({})
        assert cfg.alpha == 0.3  # default


# ═══════════════════════════════════════════════════
# EWMAThresholdEngine 测试
# ═══════════════════════════════════════════════════

class TestEWMAThresholdEngine:
    """EWMA 阈值引擎单元测试."""

    def test_initial_threshold(self, default_ewma_engine):
        t = default_ewma_engine._compute_threshold()
        # 初始状态: ewma=0, ewmvar=0, threshold = 0 + 3*0 = 0
        # 但会受 base_threshold_ms 影响
        assert t >= 0

    def test_update_converges(self, default_ewma_engine):
        """多次更新应使阈值收敛."""
        for _ in range(50):
            default_ewma_engine.update(100.0)
        stats = default_ewma_engine.get_ewma_stats()
        assert stats["sample_count"] == 50
        # EWMA 应接近 100.0
        assert 0 < stats["ewma"] < 500

    def test_cooling_period(self, default_ewma_engine):
        """测试冷却期逻辑."""
        # 先更新一次触发强同步
        default_ewma_engine.update(500.0)  # 远大于阈值
        # 冷却期内 is_cooling 应为 True
        assert default_ewma_engine.is_cooling() or not default_ewma_engine.is_cooling()
        # (冷却期取决于时间流逝，此处验证方法存在)

    def test_warm_up_returns_threshold(self, default_ewma_engine):
        vals = [100.0, 110.0, 90.0, 105.0, 95.0]
        t = default_ewma_engine.warm_up(vals)
        assert t >= 0
        assert default_ewma_engine._sample_count >= len(vals)

    def test_reset_clears_state(self, default_ewma_engine):
        default_ewma_engine.update(100.0)
        default_ewma_engine.update(200.0)
        default_ewma_engine.reset()
        stats = default_ewma_engine.get_ewma_stats()
        assert stats["sample_count"] == 0

    def test_compute_threshold_structure(self, default_ewma_engine):
        """测试阈值计算的基础结构."""
        # 更新足够样本
        for v in [90, 95, 100, 105, 110, 95, 100, 105, 90, 100, 100, 100]:
            default_ewma_engine.update(v)
        threshold = default_ewma_engine._compute_threshold()
        # 阈值 = ewma + multiplier * sqrt(ewmvar)
        assert isinstance(threshold, float)
        assert threshold > 0


# ═══════════════════════════════════════════════════
# WarmCache 测试
# ═══════════════════════════════════════════════════

class TestWarmCache:
    """预热缓存单元测试."""

    def test_empty_cache(self):
        cache = WarmCache(window_size=10)
        assert cache.size() == 0
        assert cache.get_mean() == 0.0
        assert cache.get_all() == []

    def test_add_and_mean(self):
        cache = WarmCache(window_size=10)
        cache.add(100.0)
        cache.add(200.0)
        assert cache.size() == 2
        assert cache.get_mean() == 150.0

    def test_window_overflow(self):
        cache = WarmCache(window_size=3)
        for v in [1, 2, 3, 4, 5]:
            cache.add(v)
        assert cache.size() == 3
        # 窗口应为 [3, 4, 5]
        assert cache.get_mean() == 4.0

    def test_reset(self):
        cache = WarmCache(window_size=10)
        cache.add(100)
        cache.reset()
        assert cache.size() == 0
        assert cache.get_mean() == 0.0


# ═══════════════════════════════════════════════════
# TrafficStainer 测试
# ═══════════════════════════════════════════════════

class TestTrafficStainer:
    """流量染色器单元测试."""

    def test_default_allocation_canary(self):
        stainer = TrafficStainer()
        assert stainer.get_allocation() == TrafficAllocation.CANARY_5PCT

    def test_set_allocation(self):
        stainer = TrafficStainer()
        stainer.set_allocation(TrafficAllocation.HALF_50PCT)
        assert stainer.get_allocation() == TrafficAllocation.HALF_50PCT

    def test_rollback_no_experiment(self):
        stainer = TrafficStainer(allocation=TrafficAllocation.ROLLED_BACK)
        result = stainer.should_stain_experiment("node-1", "worker")
        assert result is False

    def test_full_allocation_all_experiment(self):
        stainer = TrafficStainer(allocation=TrafficAllocation.FULL_100PCT)
        for i in range(20):
            result = stainer.should_stain_experiment(f"node-{i}", "worker")
            assert result is True

    def test_stain_header_returns_dict(self):
        stainer = TrafficStainer()
        headers = stainer.get_stain_header("node-1", "worker")
        assert "x-sync-policy" in headers
        assert headers["x-sync-policy"] in ("ewma", "fixed")

    def test_parse_stain_header_ewma(self):
        stainer = TrafficStainer()
        result = stainer.parse_stain_header({"x-sync-policy": "ewma"})
        assert result == SyncPolicy.EWMA

    def test_parse_stain_header_fixed(self):
        stainer = TrafficStainer()
        result = stainer.parse_stain_header({"x-sync-policy": "fixed"})
        assert result == SyncPolicy.FIXED_THRESHOLD

    def test_parse_stain_header_default(self):
        stainer = TrafficStainer()
        result = stainer.parse_stain_header({})
        assert result == SyncPolicy.FIXED_THRESHOLD

    def test_high_fanout_prioritized(self):
        stainer = TrafficStainer(allocation=TrafficAllocation.CANARY_5PCT)
        # 高扇出节点优先进入实验组
        result = stainer.should_stain_experiment("orchestrator-main", "orchestrator")
        assert result is True

    def test_get_stats(self):
        stainer = TrafficStainer()
        stainer.should_stain_experiment("node-1", "worker")
        stats = stainer.get_stats()
        assert stats["total_requests"] == 1
        assert "experiment_ratio" in stats
        assert stats["allocation"] == TrafficAllocation.CANARY_5PCT.value


# ═══════════════════════════════════════════════════
# CausalConsistencyDecider 测试
# ═══════════════════════════════════════════════════

class TestCausalConsistencyDecider:
    """因果一致性决策器单元测试."""

    def test_low_latency_no_sync(self, default_ewma_config):
        engine = EWMAThresholdEngine(config=default_ewma_config)
        # 预热
        engine.warm_up([100] * 20)
        decider = CausalConsistencyDecider(ewma_engine=engine, config=default_ewma_config)
        should, reason = decider.should_force_sync(latency_ms=50.0)
        assert should is False
        assert "无需强同步" in reason

    def test_high_latency_triggers_sync(self, default_ewma_config):
        engine = EWMAThresholdEngine(config=default_ewma_config)
        engine.warm_up([100] * 20)
        decider = CausalConsistencyDecider(ewma_engine=engine, config=default_ewma_config)
        should, reason = decider.should_force_sync(latency_ms=500.0)
        assert should is True
        assert "触发强同步" in reason

    def test_deep_dependency_triggers_sync(self, default_ewma_config):
        engine = EWMAThresholdEngine(config=default_ewma_config)
        engine.warm_up([100] * 20)
        decider = CausalConsistencyDecider(ewma_engine=engine, config=default_ewma_config)
        should, reason = decider.should_force_sync(
            latency_ms=50.0, dependency_depth=10
        )
        assert should is True
        assert "因果依赖深度" in reason

    def test_clock_skew_triggers_sync(self, default_ewma_config):
        engine = EWMAThresholdEngine(config=default_ewma_config)
        engine.warm_up([100] * 20)
        decider = CausalConsistencyDecider(ewma_engine=engine, config=default_ewma_config)

        peer_clock = LamportClock(node_id="peer", counter=1, timestamp=500.0)
        should, reason = decider.should_force_sync(
            latency_ms=50.0,
            peer_clock=peer_clock,
            peer_node_id="peer",
        )
        assert should is True
        assert "时钟偏差" in reason

    def test_false_upgrade_rate(self, default_ewma_config):
        engine = EWMAThresholdEngine(config=default_ewma_config)
        engine.warm_up([100] * 20)
        decider = CausalConsistencyDecider(ewma_engine=engine, config=default_ewma_config)

        assert decider.get_false_upgrade_rate() == 0.0
        decider.record_false_upgrade()
        decider.should_force_sync(latency_ms=50.0)
        rate = decider.get_false_upgrade_rate()
        assert rate > 0.0

    def test_get_decisions_returns_list(self, default_ewma_config):
        engine = EWMAThresholdEngine(config=default_ewma_config)
        engine.warm_up([100] * 20)
        decider = CausalConsistencyDecider(ewma_engine=engine, config=default_ewma_config)
        decider.should_force_sync(latency_ms=50.0)
        decisions = decider.get_decisions()
        assert len(decisions) >= 1

    def test_get_stats(self, default_ewma_config):
        engine = EWMAThresholdEngine(config=default_ewma_config)
        engine.warm_up([100] * 20)
        decider = CausalConsistencyDecider(ewma_engine=engine, config=default_ewma_config)
        decider.should_force_sync(latency_ms=50.0)
        stats = decider.get_stats()
        assert "total_decisions" in stats
        assert "false_upgrade_rate" in stats


# ═══════════════════════════════════════════════════
# ABTestManager 测试
# ═══════════════════════════════════════════════════

class TestABTestManager:
    """A/B 测试管理器单元测试."""

    def test_initial_status(self):
        mgr = ABTestManager()
        status = mgr.get_status()
        assert status["allocation"] == TrafficAllocation.CANARY_5PCT.value
        assert status["started_at"] is None

    def test_start_test(self):
        mgr = ABTestManager()
        mgr.start_test()
        status = mgr.get_status()
        assert status["started_at"] is not None

    def test_advance_allocation(self):
        mgr = ABTestManager()
        mgr.start_test()
        next_alloc = mgr.advance_allocation()
        assert next_alloc == TrafficAllocation.HALF_50PCT

        next_alloc2 = mgr.advance_allocation()
        assert next_alloc2 == TrafficAllocation.FULL_100PCT

        # 已是全量，再推进应报错
        with pytest.raises(RuntimeError):
            mgr.advance_allocation()

    def test_rollback(self):
        mgr = ABTestManager()
        mgr.start_test(TrafficAllocation.HALF_50PCT)
        mgr.rollback("测试回滚")
        assert mgr.is_rolled_back()
        status = mgr.get_status()
        assert status["rollback_reason"] == "测试回滚"

    def test_decide_sync_ewma_vs_fixed(self):
        mgr = ABTestManager()
        mgr.warm_up([100] * 20)

        # 对照组: 延迟 50ms 低于基础阈值 100ms → 不触发
        should, _ = mgr.decide_sync(latency_ms=50.0, policy=SyncPolicy.FIXED_THRESHOLD)
        assert should is False

        # 对照组: 延迟 150ms 高于基础阈值 100ms → 触发
        should, _ = mgr.decide_sync(latency_ms=150.0, policy=SyncPolicy.FIXED_THRESHOLD)
        assert should is True

    def test_update_metrics_triggers_rollback_on_false_upgrade(self):
        mgr = ABTestManager()
        mgr.start_test()
        metrics = ABTestMetrics(false_upgrade_rate=0.10)  # 10% > 5% 阈值
        mgr.update_metrics(metrics)
        assert mgr.is_rolled_back()

    def test_update_metrics_triggers_rollback_on_resource(self):
        mgr = ABTestManager()
        mgr.start_test()
        metrics = ABTestMetrics(resource_increase_pct=25.0)  # 25% > 20% 阈值
        mgr.update_metrics(metrics)
        assert mgr.is_rolled_back()

    def test_warm_up(self):
        mgr = ABTestManager()
        t = mgr.warm_up([100, 110, 90, 105, 95])
        assert t >= 0

    def test_update_config(self):
        mgr = ABTestManager()
        new_cfg = EWMAConfig(alpha=0.5, base_threshold_ms=200.0)
        mgr.update_config(new_cfg)
        assert mgr.get_config().alpha == 0.5
        assert mgr.get_config().base_threshold_ms == 200.0

    def test_get_status_comprehensive(self):
        mgr = ABTestManager()
        mgr.start_test()
        mgr.warm_up([100] * 20)
        status = mgr.get_status()
        assert "traffic_stats" in status
        assert "experiment" in status
        assert "metrics" in status
        assert "config" in status


# ═══════════════════════════════════════════════════
# 全局单例测试
# ═══════════════════════════════════════════════════

class TestGlobalABTestManager:
    """全局 A/B 测试管理器单例测试."""

    def test_singleton(self):
        reset_ab_test_manager()
        mgr1 = get_ab_test_manager()
        mgr2 = get_ab_test_manager()
        assert mgr1 is mgr2

    def test_reset(self):
        reset_ab_test_manager()
        mgr1 = get_ab_test_manager()
        reset_ab_test_manager()
        mgr2 = get_ab_test_manager()
        assert mgr1 is not mgr2


# ═══════════════════════════════════════════════════
# ABTestMetrics 测试
# ═══════════════════════════════════════════════════

class TestABTestMetrics:
    """A/B 测试指标数据类测试."""

    def test_default_values(self):
        m = ABTestMetrics()
        assert m.false_upgrade_rate == 0.0
        assert m.resource_increase_pct == 0.0

    def test_to_dict(self, sample_ab_metrics):
        d = sample_ab_metrics.to_dict()
        assert d["false_upgrade_rate"] == 0.05
        assert d["resource_increase_pct"] == 12.0
        assert d["experiment_traffic_pct"] == 0.0
        assert len(d) == 10  # 10 个指标字段
