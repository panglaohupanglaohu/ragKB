# -*- coding: utf-8 -*-
"""A/B测试框架 — 基于EWMA和Lamport时钟的因果一致性升级策略.

核心功能:
1. EWMA (Exponentially Weighted Moving Average) 阈值计算
2. Lamport 时钟因果一致性追踪
3. 流量染色标签 (x-sync-policy: ewma) 解析与路由
4. 冷启动预热缓存 (预计算滑动窗口均值)
5. ConfigMap 热更新支持
6. 渐进式流量分配 (5% → 50% → 100%)
"""

from __future__ import annotations

import asyncio
import json
import logging
import math
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


# ══════════════════════════════════════════════════════════════════
# 枚举与数据模型
# ══════════════════════════════════════════════════════════════════


class SyncPolicy(str, Enum):
    """同步策略枚举 — 用于流量染色标签."""
    FIXED_THRESHOLD = "fixed_threshold"  # 对照组: 固定阈值
    EWMA_ADAPTIVE = "ewma_adaptive"      # 实验组: EWMA动态阈值
    EWMA = EWMA_ADAPTIVE
    LAMPORT_CLOCK = "lamport_clock"


class TrafficAllocation(float, Enum):
    """流量分配阶段."""
    PHASE_1_5PCT = 5.0
    PHASE_2_50PCT = 50.0
    PHASE_3_100PCT = 100.0
    CANARY_5PCT = PHASE_1_5PCT
    HALF_50PCT = PHASE_2_50PCT
    FULL_100PCT = PHASE_3_100PCT
    ROLLED_BACK = 0.0


@dataclass
class LamportClock:
    """Lamport 逻辑时钟 — 追踪因果依赖关系.

    Attributes:
        node_id: 节点标识
        counter: 逻辑时钟计数器
        timestamp: 物理时间戳 (毫秒)
    """
    node_id: str
    counter: int = 0
    timestamp: float = 0.0  # 物理时间戳 (毫秒)

    def __post_init__(self) -> None:
        if self.timestamp <= 0:
            self.timestamp = time.time() * 1000

    def tick(self, physical_ts: Optional[float] = None) -> int:
        """时钟滴答 — 递增计数器.

        Args:
            physical_ts: 物理时间戳 (毫秒), 默认使用当前时间.

        Returns:
            递增后的计数器值.
        """
        self.counter += 1
        self.timestamp = physical_ts or (time.time() * 1000)
        return self.counter

    def merge(self, other: LamportClock) -> int:
        """合并另一个时钟 — 取 max(counter, other.counter) + 1.

        Args:
            other: 另一个 Lamport 时钟.

        Returns:
            合并后的计数器值.
        """
        self.counter = max(self.counter, other.counter) + 1
        self.timestamp = max(self.timestamp, other.timestamp)
        return self.counter

    def update(self, other_timestamp: float) -> float:
        """兼容旧 API: 用对端时间戳推进本地时钟."""
        self.counter += 1
        self.timestamp = max(self.timestamp, other_timestamp) + 1
        return self.timestamp

    def is_concurrent_with(self, other: LamportClock) -> bool:
        return self.node_id != other.node_id and self.timestamp == other.timestamp

    def happened_before(self, other: LamportClock) -> bool:
        return self.timestamp < other.timestamp

    def to_dict(self) -> Dict[str, Any]:
        return {
            "node_id": self.node_id,
            "counter": self.counter,
            "timestamp": self.timestamp,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> LamportClock:
        return cls(
            node_id=data["node_id"],
            counter=data.get("counter", 0),
            timestamp=data.get("timestamp", 0.0),
        )


@dataclass
class CausalDependency:
    """因果依赖关系 — 追踪事件之间的因果关系.

    Attributes:
        source_node: 源节点 ID
        target_node: 目标节点 ID
        clock: 依赖发生时的 Lamport 时钟
        depth: 依赖深度 (级联层数)
    """
    source_node: str
    target_node: str
    clock: LamportClock
    depth: int = 1


@dataclass
class EWMAConfig:
    """EWMA 策略配置 — 支持 ConfigMap 热更新.

    Attributes:
        alpha: EWMA 平滑因子 (0 < alpha <= 1), 默认 0.3
        base_threshold_ms: 基础阈值 (毫秒), 默认 100ms
        threshold_multiplier: 阈值乘数, 默认 3.0 (3-sigma)
        cooling_period_seconds: 冷却期 (秒), 默认 60s
        min_samples: 最小样本数, 默认 10
        max_dependency_depth: 最大因果依赖深度, 默认 3
        clock_skew_tolerance_ms: 时钟偏差容忍度 (毫秒), 默认 100ms
        enable_warm_cache: 是否启用预热缓存, 默认 True
        warm_cache_window_size: 预热缓存窗口大小, 默认 100
    """
    alpha: float = 0.3
    beta: float = 0.1
    base_threshold_ms: float = 100.0
    min_threshold_ms: float = 50.0
    max_threshold_ms: float = 500.0
    threshold_multiplier: float = 3.0
    cooldown_seconds: float = 30.0
    cooling_extension_seconds: float = 15.0
    min_samples: int = 10
    max_causal_depth: int = 5
    clock_skew_tolerance_ms: float = 100.0
    enable_warm_cache: bool = True
    warm_cache_window_size: int = 100

    @property
    def cooling_period_seconds(self) -> float:
        return self.cooldown_seconds

    @cooling_period_seconds.setter
    def cooling_period_seconds(self, value: float) -> None:
        self.cooldown_seconds = value

    @property
    def max_dependency_depth(self) -> int:
        return self.max_causal_depth

    @max_dependency_depth.setter
    def max_dependency_depth(self, value: int) -> None:
        self.max_causal_depth = value

    def to_dict(self) -> Dict[str, Any]:
        return {
            "alpha": self.alpha,
            "beta": self.beta,
            "base_threshold_ms": self.base_threshold_ms,
            "min_threshold_ms": self.min_threshold_ms,
            "max_threshold_ms": self.max_threshold_ms,
            "threshold_multiplier": self.threshold_multiplier,
            "cooldown_seconds": self.cooldown_seconds,
            "cooling_period_seconds": self.cooling_period_seconds,
            "cooling_extension_seconds": self.cooling_extension_seconds,
            "min_samples": self.min_samples,
            "max_causal_depth": self.max_causal_depth,
            "max_dependency_depth": self.max_dependency_depth,
            "clock_skew_tolerance_ms": self.clock_skew_tolerance_ms,
            "enable_warm_cache": self.enable_warm_cache,
            "warm_cache_window_size": self.warm_cache_window_size,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> EWMAConfig:
        return cls(
            alpha=data.get("alpha", 0.3),
            beta=data.get("beta", 0.1),
            base_threshold_ms=data.get("base_threshold_ms", 100.0),
            min_threshold_ms=data.get("min_threshold_ms", 50.0),
            max_threshold_ms=data.get("max_threshold_ms", 500.0),
            threshold_multiplier=data.get("threshold_multiplier", 3.0),
            cooldown_seconds=data.get(
                "cooldown_seconds",
                data.get("cooling_period_seconds", 30.0),
            ),
            cooling_extension_seconds=data.get("cooling_extension_seconds", 15.0),
            min_samples=data.get("min_samples", 10),
            max_causal_depth=data.get(
                "max_causal_depth",
                data.get("max_dependency_depth", 5),
            ),
            clock_skew_tolerance_ms=data.get("clock_skew_tolerance_ms", 100.0),
            enable_warm_cache=data.get("enable_warm_cache", True),
            warm_cache_window_size=data.get("warm_cache_window_size", 100),
        )


@dataclass
class ABTestMetrics:
    """A/B测试指标 — 核心验证指标 + 辅助监控指标.

    Attributes:
        false_upgrade_rate: 误升级率 (核心指标)
        resource_increase_pct: 资源增幅百分比 (核心指标)
        behavior_fingerprint_mutation_rate: 行为指纹变异率
        anomaly_propagation_depth: 异常传播深度
        prediction_error_rate: 预测误差率
        energy_increase_pct: 能耗增幅百分比
        temperature_slope: 温度斜率
        policy_evaluation_latency_ms: 策略评估延迟 (毫秒)
        evolution_stagnation_rate: 演化僵化率
    """
    false_upgrade_rate: float = 0.0
    resource_increase_pct: float = 0.0
    behavior_fingerprint_mutation_rate: float = 0.0
    anomaly_propagation_depth: float = 0.0
    prediction_error_rate: float = 0.0
    energy_increase_pct: float = 0.0
    temperature_slope: float = 0.0
    policy_evaluation_latency_ms: float = 0.0
    evolution_stagnation_rate: float = 0.0
    experiment_traffic_pct: float = 0.0

    def to_dict(self) -> Dict[str, float]:
        return {
            "false_upgrade_rate": self.false_upgrade_rate,
            "resource_increase_pct": self.resource_increase_pct,
            "behavior_fingerprint_mutation_rate": self.behavior_fingerprint_mutation_rate,
            "anomaly_propagation_depth": self.anomaly_propagation_depth,
            "prediction_error_rate": self.prediction_error_rate,
            "energy_increase_pct": self.energy_increase_pct,
            "temperature_slope": self.temperature_slope,
            "policy_evaluation_latency_ms": self.policy_evaluation_latency_ms,
            "evolution_stagnation_rate": self.evolution_stagnation_rate,
            "experiment_traffic_pct": self.experiment_traffic_pct,
        }


# ══════════════════════════════════════════════════════════════════
# EWMA 阈值计算引擎
# ══════════════════════════════════════════════════════════════════


class EWMAThresholdEngine:
    """EWMA 阈值计算引擎 — 动态计算强同步触发阈值.

    基于指数加权移动平均 (EWMA) 和标准差动态调整阈值，
    实现自适应因果一致性升级策略。

    Attributes:
        config: EWMA 策略配置
        _ewma: 当前 EWMA 值
        _ewmvar: 当前 EWMA 方差
        _sample_count: 样本计数
        _last_update_ts: 上次更新时间戳
        _cooling_until: 冷却期截止时间
    """

    def __init__(self, config: Optional[EWMAConfig] = None):
        self.config = config or EWMAConfig()
        self._ewma: float = self.config.base_threshold_ms
        self._ewmvar: float = 0.0
        self._sample_count: int = 0
        self._last_update_ts: float = 0.0
        self._cooling_until: float = 0.0
        self._warm_cache: WarmCache = WarmCache(
            window_size=self.config.warm_cache_window_size
        ) if self.config.enable_warm_cache else None

    def update(self, latency_ms: float, timestamp: Optional[float] = None) -> float:
        """更新 EWMA 统计量并返回当前阈值.

        Args:
            latency_ms: 本次同步延迟 (毫秒).

        Returns:
            当前动态阈值 (毫秒).
        """
        now = timestamp if timestamp is not None else time.time()

        # 检查冷却期
        if now < self._cooling_until:
            return self._compute_threshold()

        self._sample_count += 1
        alpha = self.config.alpha

        previous_ewma = self._ewma
        self._ewma = alpha * latency_ms + (1 - alpha) * self._ewma
        diff = latency_ms - previous_ewma
        self._ewmvar = (1 - alpha) * (self._ewmvar + alpha * diff * diff)

        self._last_update_ts = now

        # 更新预热缓存
        if self._warm_cache:
            self._warm_cache.add(latency_ms)

        return self._compute_threshold()

    def _compute_threshold(self) -> float:
        """计算当前动态阈值.

        Returns:
            阈值 (毫秒).
        """
        if self._sample_count < self.config.min_samples:
            threshold = max(self.config.base_threshold_ms, self._ewma)
            return min(self.config.max_threshold_ms, max(self.config.min_threshold_ms, threshold))

        std_dev = math.sqrt(self._ewmvar) if self._ewmvar > 0 else 0.0
        threshold = self._ewma + self.config.threshold_multiplier * std_dev
        threshold = max(threshold, self.config.base_threshold_ms)
        threshold = max(self.config.min_threshold_ms, threshold)
        threshold = min(self.config.max_threshold_ms, threshold)
        return threshold

    def get_ewma(self) -> float:
        return self._ewma

    def get_current_threshold(self) -> float:
        """获取当前阈值 (不更新统计量).

        Returns:
            当前阈值 (毫秒).
        """
        return self._compute_threshold()

    def get_ewma_stats(self) -> Dict[str, Any]:
        """获取 EWMA 统计信息.

        Returns:
            统计字典.
        """
        return {
            "ewma": self._ewma,
            "ewmvar": self._ewmvar,
            "std_dev": math.sqrt(self._ewmvar) if self._ewmvar > 0 else 0.0,
            "sample_count": self._sample_count,
            "update_count": self._sample_count,
            "alpha": self.config.alpha,
            "current_threshold": self._compute_threshold(),
            "cooling_active": time.time() < self._cooling_until,
            "cooling_remaining_seconds": max(0, self._cooling_until - time.time()),
        }

    def enter_cooling(self, reason: str = "") -> None:
        """进入冷却期 — 暂停策略切换.

        Args:
            reason: 冷却原因.
        """
        self._cooling_until = time.time() + self.config.cooldown_seconds
        logger.warning(f"❄️ EWMA 进入冷却期 {self.config.cooldown_seconds}s: {reason}")

    def is_cooling(self) -> bool:
        """是否处于冷却期.

        Returns:
            True 如果处于冷却期.
        """
        return time.time() < self._cooling_until

    def reset(self) -> None:
        """重置所有统计量."""
        self._ewma = self.config.base_threshold_ms
        self._ewmvar = 0.0
        self._sample_count = 0
        self._last_update_ts = 0.0
        self._cooling_until = 0.0
        if self._warm_cache:
            self._warm_cache.reset()
        logger.info("🔄 EWMA 引擎已重置")

    def warm_up(self, precomputed_values: Optional[List[float]] = None) -> float:
        """预热 — 使用预计算值初始化 EWMA 统计量.

        确保首次计算延迟 < 1秒.

        Args:
            precomputed_values: 预计算的延迟样本列表.

        Returns:
            预热后的阈值 (毫秒).
        """
        if not precomputed_values:
            # 使用预热缓存中的数据
            if self._warm_cache and self._warm_cache.size() > 0:
                precomputed_values = self._warm_cache.get_all()
            else:
                # 使用默认预估值
                precomputed_values = [self.config.base_threshold_ms] * 5

        for val in precomputed_values:
            self.update(val)

        threshold = self._compute_threshold()
        logger.info(f"🔥 EWMA 预热完成: {len(precomputed_values)} 样本, 阈值={threshold:.1f}ms")
        return threshold


# ══════════════════════════════════════════════════════════════════
# 预热缓存
# ══════════════════════════════════════════════════════════════════


class WarmCache:
    """预热缓存 — 预计算滑动窗口均值，确保冷启动 < 1秒.

    维护一个固定大小的滑动窗口，存储最近的延迟样本，
    用于快速初始化 EWMA 统计量。
    """

    def __init__(self, window_size: int = 100):
        self._window_size = window_size
        self._samples: List[float] = []
        self._sum: float = 0.0

    def add(self, value: float) -> None:
        """添加一个样本到缓存.

        Args:
            value: 延迟值 (毫秒).
        """
        self._samples.append(value)
        self._sum += value
        if len(self._samples) > self._window_size:
            removed = self._samples.pop(0)
            self._sum -= removed

    def get_mean(self) -> float:
        """获取缓存中样本的均值.

        Returns:
            均值 (毫秒), 如果缓存为空返回 0.
        """
        if not self._samples:
            return 0.0
        return self._sum / len(self._samples)

    def get_all(self) -> List[float]:
        """获取所有缓存的样本.

        Returns:
            样本列表.
        """
        return list(self._samples)

    def size(self) -> int:
        """获取缓存中的样本数.

        Returns:
            样本数.
        """
        return len(self._samples)

    def reset(self) -> None:
        """清空缓存."""
        self._samples.clear()
        self._sum = 0.0


# ══════════════════════════════════════════════════════════════════
# 流量染色与路由
# ══════════════════════════════════════════════════════════════════


class TrafficStainer:
    """流量染色器 — 管理 x-sync-policy 标签的解析与路由.

    根据节点类型 (高扇出节点优先) 和流量分配比例，
    决定是否将请求染色为实验组 (ewma) 或对照组 (fixed)。
    """

    # 高扇出节点关键词 — 这些节点优先进入实验组
    HIGH_FANOUT_KEYWORDS = [
        "aggregator", "coordinator", "router", "gateway",
        "orchestrator", "dispatcher", "broker", "hub",
        "collector", "merger", "distributor",
    ]

    def __init__(
        self,
        allocation: TrafficAllocation = TrafficAllocation.CANARY_5PCT,
        high_fanout_first: bool = True,
    ):
        self._allocation = allocation
        self._high_fanout_first = high_fanout_first
        self._experiment_nodes: Dict[str, bool] = {}  # node_id → is_experiment
        self._control_nodes: Dict[str, bool] = {}     # node_id → is_control
        self._total_requests: int = 0
        self._experiment_requests: int = 0

    def set_allocation(self, allocation: TrafficAllocation) -> None:
        """设置流量分配阶段.

        Args:
            allocation: 流量分配阶段.
        """
        old = self._allocation
        self._allocation = allocation
        logger.info(f"📊 流量分配变更: {old.value} → {allocation.value}")

    def get_allocation(self) -> TrafficAllocation:
        """获取当前流量分配阶段.

        Returns:
            当前分配阶段.
        """
        return self._allocation

    def should_stain_experiment(self, node_id: str, node_type: str = "") -> bool:
        """判断是否应将请求染色为实验组.

        Args:
            node_id: 节点 ID.
            node_type: 节点类型描述.

        Returns:
            True 表示染色为实验组 (ewma), False 为对照组 (fixed).
        """
        self._total_requests += 1

        if self._allocation == TrafficAllocation.ROLLED_BACK:
            return False

        if self._allocation == TrafficAllocation.FULL_100PCT:
            self._experiment_requests += 1
            return True

        # 检查是否已分配
        if node_id in self._experiment_nodes:
            self._experiment_requests += 1
            return True
        if node_id in self._control_nodes:
            return False

        # 高扇出节点优先进入实验组
        is_high_fanout = any(
            kw in node_type.lower() or kw in node_id.lower()
            for kw in self.HIGH_FANOUT_KEYWORDS
        )

        # 根据分配比例决定
        ratio = self._get_ratio()
        if is_high_fanout and self._high_fanout_first:
            # 高扇出节点优先进入实验组
            is_experiment = True
        else:
            # 按比例随机分配
            is_experiment = (hash(node_id) % 100) < (ratio * 100)

        if is_experiment:
            self._experiment_nodes[node_id] = True
            self._experiment_requests += 1
        else:
            self._control_nodes[node_id] = True

        return is_experiment

    def _get_ratio(self) -> float:
        """获取当前流量分配比例.

        Returns:
            实验组流量比例 (0.0 ~ 1.0).
        """
        mapping = {
            TrafficAllocation.CANARY_5PCT: 0.05,
            TrafficAllocation.HALF_50PCT: 0.50,
            TrafficAllocation.FULL_100PCT: 1.0,
            TrafficAllocation.ROLLED_BACK: 0.0,
        }
        return mapping.get(self._allocation, 0.05)

    def get_stain_header(self, node_id: str, node_type: str = "") -> Dict[str, str]:
        """获取流量染色 HTTP 头.

        Args:
            node_id: 节点 ID.
            node_type: 节点类型描述.

        Returns:
            包含 x-sync-policy 头的字典.
        """
        is_experiment = self.should_stain_experiment(node_id, node_type)
        headers = {"x-sync-policy": "ewma" if is_experiment else "fixed"}
        if node_type:
            headers["x-node-type"] = node_type
        return headers

    def parse_stain_header(self, headers: Dict[str, str]) -> SyncPolicy:
        """解析流量染色头.

        Args:
            headers: HTTP 头字典.

        Returns:
            解析出的同步策略.
        """
        policy_str = headers.get("x-sync-policy", "").strip().lower()
        if policy_str in {"ewma", SyncPolicy.EWMA.value, SyncPolicy.EWMA_ADAPTIVE.value}:
            return SyncPolicy.EWMA
        return SyncPolicy.FIXED_THRESHOLD

    def get_stats(self) -> Dict[str, Any]:
        """获取流量染色统计.

        Returns:
            统计字典.
        """
        return {
            "allocation": self._allocation.value,
            "total_requests": self._total_requests,
            "experiment_requests": self._experiment_requests,
            "experiment_ratio": round(
                self._experiment_requests / max(self._total_requests, 1), 4
            ),
            "experiment_nodes": len(self._experiment_nodes),
            "control_nodes": len(self._control_nodes),
        }


# ══════════════════════════════════════════════════════════════════
# 因果一致性决策器
# ══════════════════════════════════════════════════════════════════


class CausalConsistencyDecider:
    """因果一致性决策器 — 基于 EWMA 阈值和 Lamport 时钟判断是否需要强同步.

    核心逻辑:
    1. 检查因果依赖深度是否超过阈值
    2. 检查时钟偏差是否超过容忍度
    3. 使用 EWMA 动态阈值判断是否需要触发强同步
    """

    def __init__(
        self,
        ewma_engine: EWMAThresholdEngine,
        config: Optional[EWMAConfig] = None,
    ):
        self._ewma = ewma_engine
        self._config = config or EWMAConfig()
        self._local_clock = LamportClock(node_id="local")
        self._peer_clocks: Dict[str, LamportClock] = {}
        self._decisions: List[Dict[str, Any]] = []
        self._false_upgrades: int = 0
        self._total_decisions: int = 0

    def should_force_sync(
        self,
        latency_ms: float,
        dependency_depth: int = 1,
        peer_clock: Optional[LamportClock] = None,
        peer_node_id: str = "",
        clock_skew_ms: Optional[float] = None,
    ) -> Tuple[bool, str]:
        """判断是否需要触发强同步.

        Args:
            latency_ms: 本次同步延迟 (毫秒).
            peer_clock: 对端 Lamport 时钟.
            dependency_depth: 因果依赖深度.
            peer_node_id: 对端节点 ID.

        Returns:
            (should_sync, reason) 元组.
        """
        self._total_decisions += 1

        if isinstance(dependency_depth, LamportClock) and peer_clock is None:
            peer_clock = dependency_depth
            dependency_depth = 1

        # 1. 更新 EWMA 统计量
        threshold = self._ewma.update(latency_ms)

        # 2. 检查冷却期
        if self._ewma.is_cooling():
            reason = f"冷却期: 跳过决策"
            self._record_decision(False, reason, latency_ms, threshold)
            return False, reason

        # 3. 检查因果依赖深度
        if dependency_depth >= self._config.max_causal_depth:
            reason = (
                f"因果依赖深度 {dependency_depth} > "
                f"最大深度 {self._config.max_causal_depth}: 触发强同步"
            )
            self._ewma.enter_cooling(reason)
            self._record_decision(True, reason, latency_ms, threshold)
            return True, reason

        # 4. 检查时钟偏差
        if clock_skew_ms is None and peer_clock and peer_node_id:
            self._peer_clocks[peer_node_id] = peer_clock
            self._local_clock.merge(peer_clock)
            clock_skew_ms = abs(self._local_clock.timestamp - peer_clock.timestamp)

        if clock_skew_ms is not None and clock_skew_ms > self._config.clock_skew_tolerance_ms:
            reason = (
                f"时钟偏差 {clock_skew_ms:.1f}ms > "
                f"容忍度 {self._config.clock_skew_tolerance_ms}ms: 触发强同步"
            )
            self._ewma.enter_cooling(reason)
            self._record_decision(True, reason, latency_ms, threshold)
            return True, reason

        # 5. 使用 EWMA 动态阈值判断
        if latency_ms >= threshold:
            reason = (
                f"延迟 {latency_ms:.1f}ms >= "
                f"动态阈值 {threshold:.1f}ms: 触发强同步"
            )
            self._ewma.enter_cooling(reason)
            self._record_decision(True, reason, latency_ms, threshold)
            return True, reason

        reason = (
            f"延迟 {latency_ms:.1f}ms ≤ 阈值 {threshold:.1f}ms: "
            f"无需强同步"
        )
        self._record_decision(False, reason, latency_ms, threshold)
        return False, reason

    def record_false_upgrade(self) -> None:
        """记录一次误升级."""
        self._false_upgrades += 1

    def get_false_upgrade_rate(self) -> float:
        """获取误升级率.

        Returns:
            误升级率 (0.0 ~ 1.0).
        """
        if self._total_decisions == 0:
            return 0.0
        return self._false_upgrades / self._total_decisions

    def _record_decision(
        self, should_sync: bool, reason: str,
        latency_ms: float, threshold: float,
    ) -> None:
        """记录一次决策."""
        self._decisions.append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "should_sync": should_sync,
            "reason": reason,
            "latency_ms": round(latency_ms, 2),
            "threshold": round(threshold, 2),
        })
        # 只保留最近 1000 条决策记录
        if len(self._decisions) > 1000:
            self._decisions = self._decisions[-1000:]

    def get_decisions(self, limit: int = 100) -> List[Dict[str, Any]]:
        """获取最近的决策记录.

        Args:
            limit: 返回条数上限.

        Returns:
            决策记录列表.
        """
        return self._decisions[-limit:]

    def get_stats(self) -> Dict[str, Any]:
        """获取决策统计.

        Returns:
            统计字典.
        """
        return {
            "total_decisions": self._total_decisions,
            "false_upgrades": self._false_upgrades,
            "false_upgrade_rate": round(self.get_false_upgrade_rate(), 4),
            "ewma_stats": self._ewma.get_ewma_stats(),
            "local_clock": self._local_clock.to_dict(),
            "peer_clocks": {
                k: v.to_dict() for k, v in self._peer_clocks.items()
            },
        }

    def get_decision_stats(self) -> Dict[str, Any]:
        sync_decisions = sum(1 for item in self._decisions if item["should_sync"])
        no_sync_decisions = self._total_decisions - sync_decisions
        return {
            "total_decisions": self._total_decisions,
            "sync_decisions": sync_decisions,
            "no_sync_decisions": no_sync_decisions,
        }

    def reset(self) -> None:
        """重置决策器."""
        self._ewma.reset()
        self._local_clock = LamportClock(node_id="local")
        self._peer_clocks.clear()
        self._decisions.clear()
        self._false_upgrades = 0
        self._total_decisions = 0


# ══════════════════════════════════════════════════════════════════
# A/B 测试管理器
# ══════════════════════════════════════════════════════════════════


class ABTestManager:
    """A/B 测试管理器 — 管理整个 A/B 测试生命周期.

    职责:
    1. 管理流量分配阶段 (5% → 50% → 100%)
    2. 维护实验组和对照组的 EWMA 引擎
    3. 监控核心指标 (误升级率、资源增幅)
    4. 自动回滚决策
    5. 提供统一的状态查询接口
    """

    # 核心指标阈值
    MAX_FALSE_UPGRADE_RATE = 0.05   # 误升级率 ≤ 5%
    MAX_RESOURCE_INCREASE_PCT = 20.0  # 资源增幅 < 20%

    def __init__(self, config: Optional[EWMAConfig] = None):
        self._config = config or EWMAConfig()
        self.test_active: bool = False
        self.experiment_traffic_pct: float = 0.0
        self._warmed_up: bool = False

        # 实验组: EWMA 策略
        self._experiment_ewma = EWMAThresholdEngine(config=self._config)
        self._experiment_decider = CausalConsistencyDecider(
            ewma_engine=self._experiment_ewma, config=self._config
        )

        # 对照组: 固定阈值策略 (使用基础阈值)
        self._control_ewma = EWMAThresholdEngine(config=EWMAConfig(
            alpha=0.0,  # 不使用 EWMA
            base_threshold_ms=self._config.base_threshold_ms,
            threshold_multiplier=0.0,
        ))

        # 流量染色器
        self._stainer = TrafficStainer()

        # 测试指标
        self._metrics = ABTestMetrics()
        self._started_at: Optional[str] = None
        self._rolled_back_at: Optional[str] = None
        self._rollback_reason: str = ""

    # ── 生命周期管理 ──────────────────────────────────────

    def start_test(
        self,
        allocation: TrafficAllocation = TrafficAllocation.CANARY_5PCT,
        traffic_pct: Optional[float] = None,
    ) -> None:
        """启动 A/B 测试.

        Args:
            allocation: 初始流量分配阶段.
        """
        if traffic_pct is not None:
            allocation = self._allocation_from_pct(traffic_pct)

        self._started_at = datetime.now(timezone.utc).isoformat()
        self.test_active = True
        self.experiment_traffic_pct = float(allocation.value)
        self._stainer.set_allocation(allocation)
        logger.info(f"🚀 A/B测试启动: 分配={allocation.value}")

    def stop_test(self) -> None:
        self.test_active = False
        self.experiment_traffic_pct = 0.0

    def advance_allocation(self) -> TrafficAllocation:
        """推进到下一个流量分配阶段.

        Returns:
            新的分配阶段.

        Raises:
            RuntimeError: 如果当前已是全量或已回滚.
        """
        current = self._stainer.get_allocation()
        mapping = {
            TrafficAllocation.CANARY_5PCT: TrafficAllocation.HALF_50PCT,
            TrafficAllocation.HALF_50PCT: TrafficAllocation.FULL_100PCT,
        }
        next_alloc = mapping.get(current)
        if next_alloc is None:
            raise RuntimeError(f"无法从 {current.value} 推进: 已是最终阶段或已回滚")

        self._stainer.set_allocation(next_alloc)
        self.experiment_traffic_pct = float(next_alloc.value)
        logger.info(f"📈 流量分配推进: {current.value} → {next_alloc.value}")
        return next_alloc

    def rollback(self, reason: str = "") -> None:
        """回滚到固定阈值对照组.

        Args:
            reason: 回滚原因.
        """
        self._stainer.set_allocation(TrafficAllocation.ROLLED_BACK)
        self.test_active = False
        self.experiment_traffic_pct = 0.0
        self._rolled_back_at = datetime.now(timezone.utc).isoformat()
        self._rollback_reason = reason
        logger.warning(f"⏪ A/B测试回滚: {reason}")

    def is_in_experiment(self, node_id: str, node_type: str = "") -> bool:
        return self._stainer.should_stain_experiment(node_id, node_type)

    def is_rolled_back(self) -> bool:
        """是否已回滚.

        Returns:
            True 如果已回滚.
        """
        return self._stainer.get_allocation() == TrafficAllocation.ROLLED_BACK

    # ── 核心决策 ──────────────────────────────────────────

    def decide_sync(
        self,
        latency_ms: float,
        policy: SyncPolicy,
        peer_clock: Optional[LamportClock] = None,
        dependency_depth: int = 1,
        peer_node_id: str = "",
    ) -> Tuple[bool, str]:
        """根据策略做出同步决策.

        Args:
            latency_ms: 同步延迟 (毫秒).
            policy: 同步策略 (ewma 或 fixed).
            peer_clock: 对端 Lamport 时钟.
            dependency_depth: 因果依赖深度.
            peer_node_id: 对端节点 ID.

        Returns:
            (should_sync, reason) 元组.
        """
        if policy == SyncPolicy.EWMA:
            return self._experiment_decider.should_force_sync(
                latency_ms=latency_ms,
                peer_clock=peer_clock,
                dependency_depth=dependency_depth,
                peer_node_id=peer_node_id,
            )
        else:
            if dependency_depth >= self._config.max_causal_depth:
                return True, (
                    f"因果依赖深度 {dependency_depth} > "
                    f"最大深度 {self._config.max_causal_depth}: 触发强同步"
                )

            if peer_clock is not None:
                clock_skew_ms = abs((peer_clock.timestamp or 0.0) - (time.time() * 1000))
                if clock_skew_ms > self._config.clock_skew_tolerance_ms:
                    return True, (
                        f"时钟偏差 {clock_skew_ms:.1f}ms > "
                        f"容忍度 {self._config.clock_skew_tolerance_ms}ms: 触发强同步"
                    )

            # 对照组: 固定阈值
            should_sync = latency_ms > self._config.base_threshold_ms
            reason = (
                f"固定阈值: 延迟 {latency_ms:.1f}ms "
                f"{'>' if should_sync else '<='} "
                f"{self._config.base_threshold_ms:.1f}ms"
            )
            return should_sync, reason

    # ── 指标更新 ──────────────────────────────────────────

    def update_metrics(self, metrics: ABTestMetrics) -> None:
        """更新测试指标并检查是否需要回滚.

        Args:
            metrics: 最新指标数据.
        """
        self._metrics = metrics

        # 检查核心指标
        if metrics.false_upgrade_rate > self.MAX_FALSE_UPGRADE_RATE:
            self.rollback(
                f"误升级率 {metrics.false_upgrade_rate:.2%} > "
                f"阈值 {self.MAX_FALSE_UPGRADE_RATE:.0%}"
            )
            return

        if metrics.resource_increase_pct >= self.MAX_RESOURCE_INCREASE_PCT:
            self.rollback(
                f"资源增幅 {metrics.resource_increase_pct:.1f}% ≥ "
                f"阈值 {self.MAX_RESOURCE_INCREASE_PCT:.0f}%"
            )
            return

    # ── 预热 ──────────────────────────────────────────────

    def warm_up(self, precomputed_values: Optional[List[float]] = None) -> float:
        """预热实验组 EWMA 引擎.

        Args:
            precomputed_values: 预计算的延迟样本.

        Returns:
            预热后的阈值 (毫秒).
        """
        start = time.time()
        threshold = self._experiment_ewma.warm_up(precomputed_values)
        self._warmed_up = True
        elapsed = (time.time() - start) * 1000  # 转换为毫秒

        if elapsed > 1000:
            logger.warning(
                f"⚠️ 冷启动耗时 {elapsed:.1f}ms > 1s 阈值, "
                f"建议增大预热缓存窗口"
            )
        else:
            logger.info(f"✅ 冷启动耗时 {elapsed:.1f}ms < 1s")

        return threshold

    # ── 状态查询 ──────────────────────────────────────────

    def get_status(self) -> Dict[str, Any]:
        """获取 A/B 测试完整状态.

        Returns:
            状态字典.
        """
        return {
            "started_at": self._started_at,
            "rolled_back_at": self._rolled_back_at,
            "rollback_reason": self._rollback_reason,
            "allocation": self._stainer.get_allocation().value,
            "test_active": self.test_active,
            "experiment_traffic_pct": self.experiment_traffic_pct,
            "traffic_stats": self._stainer.get_stats(),
            "experiment": self._experiment_decider.get_stats(),
            "metrics": self._metrics.to_dict(),
            "config": self._config.to_dict(),
        }

    def get_config(self) -> EWMAConfig:
        """获取当前配置.

        Returns:
            当前配置.
        """
        return self._config

    def update_config(self, config: EWMAConfig | Dict[str, Any]) -> None:
        """热更新配置.

        Args:
            config: 新配置.
        """
        if isinstance(config, dict):
            config = EWMAConfig.from_dict({**self._config.to_dict(), **config})

        old_alpha = self._config.alpha
        self._config = config
        self._experiment_ewma.config = config
        self._experiment_decider._config = config
        self._control_ewma.config = EWMAConfig(
            alpha=0.0,
            base_threshold_ms=self._config.base_threshold_ms,
            min_threshold_ms=self._config.min_threshold_ms,
            max_threshold_ms=self._config.max_threshold_ms,
            threshold_multiplier=0.0,
        )
        logger.info(
            f"♻️ ConfigMap 热更新: alpha={old_alpha} → {config.alpha}"
        )

    def get_metrics(self) -> ABTestMetrics:
        self._metrics.experiment_traffic_pct = self.experiment_traffic_pct
        return self._metrics

    def get_report(self) -> Dict[str, Any]:
        return {
            **self.get_status(),
            "test_active": self.test_active,
            "experiment_traffic_pct": self.experiment_traffic_pct,
        }

    def _allocation_from_pct(self, traffic_pct: float) -> TrafficAllocation:
        if traffic_pct <= 0:
            return TrafficAllocation.ROLLED_BACK
        if traffic_pct <= 5:
            return TrafficAllocation.PHASE_1_5PCT
        if traffic_pct <= 50:
            return TrafficAllocation.PHASE_2_50PCT
        return TrafficAllocation.PHASE_3_100PCT


# ══════════════════════════════════════════════════════════════════
# 全局单例
# ══════════════════════════════════════════════════════════════════

_default_ab_test_manager: Optional[ABTestManager] = None


def get_ab_test_manager() -> ABTestManager:
    """获取全局 A/B 测试管理器单例.

    Returns:
        ABTestManager 实例.
    """
    global _default_ab_test_manager
    if _default_ab_test_manager is None:
        _default_ab_test_manager = ABTestManager()
    return _default_ab_test_manager


def reset_ab_test_manager() -> None:
    """重置全局 A/B 测试管理器."""
    global _default_ab_test_manager
    _default_ab_test_manager = None
