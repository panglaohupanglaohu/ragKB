# -*- coding: utf-8 -*-
"""
Chaos Engineering Engine — 混沌工程稳定性测试引擎

模拟以下混沌场景，验证 SLO 达标情况：
- Spot 实例中断与回收 (AWS EC2 Spot Instance Interruption)
- 缓存降级 (缓存击穿/穿透/雪崩、热点 Key 过期)
- 数据分层退化 (热/温/冷分层降级)
- 网络延迟注入、CPU 压力模拟

架构:
  ChaosScenario → ChaosInjector → SystemUnderTest → SLOMetrics
                                              → ChaosTestReport
"""

from __future__ import annotations

import random
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple


# ────────────────────────────────────────────────────────────────
# 枚举 & 数据类
# ────────────────────────────────────────────────────────────────


class ChaosScenarioType(str, Enum):
    """混沌场景类型."""
    SPOT_INTERRUPTION = "spot_interruption"       # Spot 实例中断
    SPOT_RECLAIM = "spot_reclaim"                  # Spot 实例被回收
    CACHE_MISS_STORM = "cache_miss_storm"          # 缓存击穿风暴
    CACHE_PENETRATION = "cache_penetration"        # 缓存穿透
    CACHE_AVALANCHE = "cache_avalanche"            # 缓存雪崩
    HOT_KEY_EXPIRY = "hot_key_expiry"              # 热点 Key 过期
    HOT_TIER_DEGRADATION = "hot_tier_degradation"  # 热层退化
    WARM_TIER_SLOWDOWN = "warm_tier_slowdown"      # 温层延迟
    COLD_TIER_FAILURE = "cold_tier_failure"        # 冷层不可用
    NETWORK_LATENCY = "network_latency"             # 网络延迟注入
    COMBINED_STRESS = "combined_stress"             # 组合压力


class SLOResult(str, Enum):
    """SLO 判定结果."""
    PASS = "pass"
    FAIL = "fail"
    DEGRADED = "degraded"


class DataTier(str, Enum):
    """数据分层."""
    HOT = "hot"    # 热层 (< 1ms, 100% 命中目标)
    WARM = "warm"  # 温层 (< 10ms, 90% 命中目标)
    COLD = "cold"  # 冷层 (< 100ms, 归档数据)


class CacheState(str, Enum):
    """缓存状态."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    FAILED = "failed"


class SpotInstanceState(str, Enum):
    """Spot 实例状态."""
    RUNNING = "running"
    INTERRUPTED = "interrupted"   # 收到中断通知
    RECLAIMING = "reclaiming"     # 正在回收
    TERMINATED = "terminated"


# ────────────────────────────────────────────────────────────────
# SLO 定义
# ────────────────────────────────────────────────────────────────


@dataclass
class SLODefinition:
    """单条 SLO 定义.

    Attributes:
        name: SLO 名称
        metric: 监控指标名
        target: 目标值 (如 99.9 表示 99.9%)
        unit: 单位 (pct / ms / count)
        operator: 比较运算符 (lt / gt / gte / lte)
        weight: 在总分中的权重 (0-1)
        cost_sensitivity: 对成本维度的影响权重 (0-1)
    """
    name: str
    metric: str
    target: float
    unit: str = "pct"
    operator: str = "gte"
    weight: float = 0.25
    cost_sensitivity: float = 0.5

    def evaluate(self, measured: float) -> Tuple[bool, float]:
        """评估 SLO 是否达标.

        Returns:
            (pass, deviation): 是否达标, 偏离度 (0=完美, >0=偏差)
        """
        if self.operator == "gte":
            passed = measured >= self.target
            deviation = max(0.0, (self.target - measured) / self.target) if self.target > 0 else 0.0
        elif self.operator == "lte":
            passed = measured <= self.target
            deviation = max(0.0, (measured - self.target) / self.target) if self.target > 0 else 0.0
        elif self.operator == "gt":
            passed = measured > self.target
            deviation = max(0.0, (self.target - measured) / self.target) if self.target > 0 else 0.0
        else:  # lt
            passed = measured < self.target
            deviation = max(0.0, (measured - self.target) / self.target) if self.target > 0 else 0.0
        return passed, min(deviation, 1.0)


# 预定义 SLO 集合
DEFAULT_SLOS: List[SLODefinition] = [
    SLODefinition("可用性", "availability", 99.9, "pct", "gte", 0.30, 0.3),
    SLODefinition("P99 延迟", "latency_p99_ms", 200.0, "ms", "lte", 0.25, 0.25),
    SLODefinition("错误率", "error_rate", 1.0, "pct", "lte", 0.20, 0.20),
    SLODefinition("缓存命中率", "cache_hit_rate", 95.0, "pct", "gte", 0.15, 0.40),
    SLODefinition("数据分层可用率", "tier_availability", 99.0, "pct", "gte", 0.10, 0.25),
]


# ────────────────────────────────────────────────────────────────
# 混沌场景模拟器
# ────────────────────────────────────────────────────────────────


class SpotInstanceSimulator:
    """Spot 实例生命周期模拟器.

    模拟 AWS EC2 Spot Instance 的完整生命周期:
    - 正常运行
    - 收到 2 分钟中断通知
    - 开始回收
    - 实例终止

    也模拟竞价型实例的价格波动导致的中断。
    """

    def __init__(self, instance_count: int = 3, base_uptime_hours: float = 72.0):
        self._instance_count = instance_count
        self._base_uptime_hours = base_uptime_hours
        self._instances: Dict[str, Dict[str, Any]] = {}
        self._interruption_log: List[Dict[str, Any]] = []
        self._init_instances()

    def _init_instances(self) -> None:
        for i in range(self._instance_count):
            inst_id = f"spot-{i + 1:03d}"
            self._instances[inst_id] = {
                "id": inst_id,
                "state": SpotInstanceState.RUNNING,
                "interruption_notice_at": None,
                "termination_at": None,
                "uptime_seconds": random.uniform(0, self._base_uptime_hours * 3600),
                "price_multiplier": 1.0,
            }

    def inject_interruption(self, instance_id: Optional[str] = None) -> Dict[str, Any]:
        """注入中断事件到指定或随机实例."""
        if instance_id and instance_id in self._instances:
            target = instance_id
        else:
            running = [i for i, d in self._instances.items()
                       if d["state"] == SpotInstanceState.RUNNING]
            if not running:
                return {"ok": False, "error": "No running instances"}
            target = random.choice(running)

        inst = self._instances[target]
        now = time.time()
        inst["state"] = SpotInstanceState.INTERRUPTED
        inst["interruption_notice_at"] = now
        inst["termination_at"] = now + 120  # 2 分钟通知窗口

        event = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "instance_id": target,
            "event": "spot_interruption",
            "notice_time": inst["interruption_notice_at"],
            "deadline": inst["termination_at"],
        }
        self._interruption_log.append(event)
        return {"ok": True, "event": event}

    def inject_reclaim(self, instance_id: Optional[str] = None) -> Dict[str, Any]:
        """注入实例回收事件."""
        interrupted = [i for i, d in self._instances.items()
                       if d["state"] == SpotInstanceState.INTERRUPTED]
        if not interrupted:
            # 先中断再回收
            self.inject_interruption(instance_id)
            interrupted = [i for i, d in self._instances.items()
                           if d["state"] == SpotInstanceState.INTERRUPTED]

        target = instance_id if instance_id in self._instances else interrupted[0]
        inst = self._instances[target]
        inst["state"] = SpotInstanceState.RECLAIMING
        event = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "instance_id": target,
            "event": "spot_reclaim",
        }
        self._interruption_log.append(event)
        return {"ok": True, "event": event}

    def complete_termination(self, instance_id: str) -> Dict[str, Any]:
        """完成实例终止."""
        if instance_id not in self._instances:
            return {"ok": False, "error": f"Unknown instance {instance_id}"}
        inst = self._instances[instance_id]
        inst["state"] = SpotInstanceState.TERMINATED
        inst["termination_at"] = time.time()
        return {"ok": True, "instance_id": instance_id}

    def recover_instance(self, instance_id: str) -> Dict[str, Any]:
        """恢复实例 (模拟新 Spot 实例启动)."""
        if instance_id not in self._instances:
            return {"ok": False, "error": f"Unknown instance {instance_id}"}
        inst = self._instances[instance_id]
        inst["state"] = SpotInstanceState.RUNNING
        inst["interruption_notice_at"] = None
        inst["termination_at"] = None
        inst["uptime_seconds"] = 0
        return {"ok": True, "instance_id": instance_id}

    def get_state(self) -> Dict[str, Any]:
        """获取所有实例状态."""
        states = {}
        for inst_id, inst in self._instances.items():
            states[inst_id] = inst["state"].value
        running = sum(1 for s in states.values() if s == SpotInstanceState.RUNNING.value)
        return {
            "instances": self._instances,
            "running_count": running,
            "total_count": self._instance_count,
            "interruption_count": len(self._interruption_log),
            "availability": running / self._instance_count * 100 if self._instance_count else 0,
        }


class CacheDegradationSimulator:
    """缓存降级模拟器.

    模拟 Redis/内存缓存的各类故障模式:
    - 缓存击穿 (Cache Miss Storm): 大量请求同时查询已过期的热点 Key
    - 缓存穿透 (Cache Penetration): 查询不存在的数据，绕过缓存
    - 缓存雪崩 (Cache Avalanche): 大量 Key 同时过期
    - 热点 Key 过期 (Hot Key Expiry): 单个热点 Key 过期导致 DB 压力
    """

    def __init__(
        self,
        base_hit_rate: float = 0.98,
        base_latency_ms: float = 2.0,
        cache_capacity: int = 10000,
        hot_key_count: int = 100,
    ):
        self._base_hit_rate = base_hit_rate
        self._base_latency_ms = base_latency_ms
        self._cache_capacity = cache_capacity
        self._hot_key_count = hot_key_count
        self._state = CacheState.HEALTHY
        self._current_hit_rate = base_hit_rate
        self._current_latency_ms = base_latency_ms
        self._degradation_factor = 1.0  # 1.0 = 正常, >1 = 降级
        self._bloom_filter: set = set()
        self._init_bloom_filter()

    def _init_bloom_filter(self) -> None:
        """初始化布隆过滤器 (模拟已有 key 集合)."""
        for i in range(self._cache_capacity):
            self._bloom_filter.add(f"key-{i:06d}")

    def inject_cache_miss_storm(self, severity: float = 0.5) -> Dict[str, Any]:
        """注入缓存击穿风暴.

        Args:
            severity: 严重程度 0-1, 越高 hit_rate 越低
        """
        self._state = CacheState.DEGRADED
        self._degradation_factor = 1.0 + severity * 5.0
        self._current_hit_rate = max(0.1, self._base_hit_rate * (1 - severity * 0.9))
        self._current_latency_ms = self._base_latency_ms * self._degradation_factor
        return {
            "scenario": "cache_miss_storm",
            "severity": severity,
            "new_hit_rate": self._current_hit_rate,
            "new_latency_ms": self._current_latency_ms,
        }

    def inject_cache_penetration(self, penetration_ratio: float = 0.3) -> Dict[str, Any]:
        """注入缓存穿透.

        Args:
            penetration_ratio: 穿透比例 (请求中查询不存在 Key 的比例)
        """
        self._state = CacheState.DEGRADED
        self._degradation_factor = 1.0 + penetration_ratio * 8.0
        self._current_hit_rate = max(0.05, self._base_hit_rate * (1 - penetration_ratio * 1.5))
        self._current_latency_ms = self._base_latency_ms * self._degradation_factor
        return {
            "scenario": "cache_penetration",
            "penetration_ratio": penetration_ratio,
            "new_hit_rate": self._current_hit_rate,
            "new_latency_ms": self._current_latency_ms,
        }

    def inject_cache_avalanche(self, expired_ratio: float = 0.7) -> Dict[str, Any]:
        """注入缓存雪崩.

        Args:
            expired_ratio: 同时过期的 Key 比例
        """
        self._state = CacheState.DEGRADED
        self._degradation_factor = 1.0 + expired_ratio * 10.0
        self._current_hit_rate = max(0.01, self._base_hit_rate * (1 - expired_ratio))
        self._current_latency_ms = self._base_latency_ms * self._degradation_factor
        return {
            "scenario": "cache_avalanche",
            "expired_ratio": expired_ratio,
            "new_hit_rate": self._current_hit_rate,
            "new_latency_ms": self._current_latency_ms,
        }

    def inject_hot_key_expiry(self, key_count: int = 5) -> Dict[str, Any]:
        """注入热点 Key 过期.

        Args:
            key_count: 同时过期的热点 Key 数量
        """
        self._state = CacheState.DEGRADED
        severity = min(key_count / self._hot_key_count, 1.0)
        self._degradation_factor = 1.0 + severity * 6.0
        self._current_hit_rate = max(0.2, self._base_hit_rate * (1 - severity * 0.8))
        self._current_latency_ms = self._base_latency_ms * self._degradation_factor
        return {
            "scenario": "hot_key_expiry",
            "expired_hot_keys": key_count,
            "new_hit_rate": self._current_hit_rate,
            "new_latency_ms": self._current_latency_ms,
        }

    def reset(self) -> None:
        """恢复缓存到健康状态."""
        self._state = CacheState.HEALTHY
        self._current_hit_rate = self._base_hit_rate
        self._current_latency_ms = self._base_latency_ms
        self._degradation_factor = 1.0

    def get_metrics(self) -> Dict[str, Any]:
        """获取当前缓存指标."""
        return {
            "state": self._state.value,
            "hit_rate": round(self._current_hit_rate, 4),
            "latency_ms": round(self._current_latency_ms, 2),
            "degradation_factor": round(self._degradation_factor, 2),
            "capacity": self._cache_capacity,
            "hot_key_count": self._hot_key_count,
        }

    def query_key(self, key: str) -> Tuple[bool, float]:
        """模拟查询 Key，返回 (命中, 延迟ms)."""
        if self._state == CacheState.FAILED:
            return False, self._current_latency_ms * 10

        if key not in self._bloom_filter:
            # 穿透 — 查了不存在的 key
            return False, self._base_latency_ms * random.uniform(5, 15)

        if random.random() < self._current_hit_rate:
            return True, self._current_latency_ms * random.uniform(0.5, 1.0)
        else:
            return False, self._current_latency_ms * random.uniform(1.5, 3.0)


class DataTieringSimulator:
    """数据分层模拟器.

    模拟多级数据分层 (热/温/冷) 的性能特征:
    - 热层: < 1ms 延迟, 高命中率
    - 温层: < 10ms 延迟, 中等命中率
    - 冷层: < 100ms 延迟, 归档数据

    故障模式:
    - 热层退化到温层性能
    - 温层延迟增加
    - 冷层不可用
    """

    def __init__(self):
        self._tiers: Dict[str, Dict[str, Any]] = {
            DataTier.HOT.value: {
                "target_latency_ms": 1.0,
                "current_latency_ms": 1.0,
                "target_hit_rate": 0.95,
                "current_hit_rate": 0.95,
                "available": True,
                "degraded": False,
                "data_ratio": 0.10,  # 10% 数据在热层
            },
            DataTier.WARM.value: {
                "target_latency_ms": 10.0,
                "current_latency_ms": 10.0,
                "target_hit_rate": 0.85,
                "current_hit_rate": 0.85,
                "available": True,
                "degraded": False,
                "data_ratio": 0.30,  # 30% 数据在温层
            },
            DataTier.COLD.value: {
                "target_latency_ms": 100.0,
                "current_latency_ms": 100.0,
                "target_hit_rate": 0.99,
                "current_hit_rate": 0.99,
                "available": True,
                "degraded": False,
                "data_ratio": 0.60,  # 60% 数据在冷层
            },
        }

    def inject_hot_tier_degradation(self, latency_multiplier: float = 10.0) -> Dict[str, Any]:
        """热层退化 — 热层延迟增加到温层水平."""
        tier = self._tiers[DataTier.HOT.value]
        tier["degraded"] = True
        tier["current_latency_ms"] = tier["target_latency_ms"] * latency_multiplier
        tier["current_hit_rate"] = tier["target_hit_rate"] * 0.5
        return {"scenario": "hot_tier_degradation", "hot_latency_ms": tier["current_latency_ms"]}

    def inject_warm_tier_slowdown(self, latency_multiplier: float = 5.0) -> Dict[str, Any]:
        """温层延迟增加."""
        tier = self._tiers[DataTier.WARM.value]
        tier["degraded"] = True
        tier["current_latency_ms"] = tier["target_latency_ms"] * latency_multiplier
        return {"scenario": "warm_tier_slowdown", "warm_latency_ms": tier["current_latency_ms"]}

    def inject_cold_tier_failure(self) -> Dict[str, Any]:
        """冷层不可用."""
        tier = self._tiers[DataTier.COLD.value]
        tier["available"] = False
        tier["degraded"] = True
        tier["current_latency_ms"] = float("inf")
        return {"scenario": "cold_tier_failure"}

    def reset(self) -> None:
        """恢复所有分层."""
        for tier_name, tier in self._tiers.items():
            tier["current_latency_ms"] = tier["target_latency_ms"]
            tier["current_hit_rate"] = tier["target_hit_rate"]
            tier["available"] = True
            tier["degraded"] = False

    def query_tier(self, key: str) -> Tuple[Optional[str], float, bool]:
        """模拟跨分层查询.

        Returns:
            (tier_name, latency_ms, hit)
        """
        rand = random.random()
        if rand < self._tiers[DataTier.HOT.value]["data_ratio"]:
            tier = DataTier.HOT.value
        elif rand < (self._tiers[DataTier.HOT.value]["data_ratio"] +
                      self._tiers[DataTier.WARM.value]["data_ratio"]):
            tier = DataTier.WARM.value
        else:
            tier = DataTier.COLD.value

        tier_data = self._tiers[tier]
        if not tier_data["available"]:
            # Fallback to warm or hot
            fallback_tiers = [t for t in [DataTier.WARM.value, DataTier.HOT.value]
                              if self._tiers[t]["available"]]
            if not fallback_tiers:
                return None, 500.0, False
            tier = fallback_tiers[0]
            tier_data = self._tiers[tier]

        hit = random.random() < tier_data["current_hit_rate"]
        latency = tier_data["current_latency_ms"] * random.uniform(0.8, 1.5)
        return tier, latency, hit

    def get_metrics(self) -> Dict[str, Any]:
        """获取所有分层的指标."""
        result = {}
        for tier_name, tier in self._tiers.items():
            result[tier_name] = {
                "available": tier["available"],
                "degraded": tier["degraded"],
                "latency_ms": round(tier["current_latency_ms"], 2),
                "hit_rate": round(tier["current_hit_rate"], 4),
            }
        return result


# ────────────────────────────────────────────────────────────────
# SLO 度量收集器
# ────────────────────────────────────────────────────────────────


@dataclass
class SLOSnapshot:
    """单个时间点的 SLO 快照."""
    timestamp: str
    sLO_name: str
    metric: str
    measured: float
    target: float
    passed: bool
    deviation: float
    scenario: str


@dataclass
class ChaosTestReport:
    """混沌测试报告 — 成本-质量双维度验收标准.

    Attributes:
        test_id: 测试运行 ID
        start_time: 开始时间
        end_time: 结束时间
        scenarios_executed: 执行的场景数
        total_requests: 总请求数
        slo_results: 每个 SLO 的通过/失败
        cost_estimation: 成本估计
        quality_score: 质量评分
        cost_score: 成本评分
        overall_grade: 总评分 A-F
        recommendations: 改进建议
    """
    test_id: str
    start_time: str = ""
    end_time: str = ""
    scenarios_executed: int = 0
    total_requests: int = 0
    slo_results: List[Dict[str, Any]] = field(default_factory=list)
    cost_estimation: Dict[str, Any] = field(default_factory=dict)
    quality_score: float = 0.0
    cost_score: float = 0.0
    overall_grade: str = "N/A"
    recommendations: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "test_id": self.test_id,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "scenarios_executed": self.scenarios_executed,
            "total_requests": self.total_requests,
            "slo_results": self.slo_results,
            "cost_estimation": self.cost_estimation,
            "quality_score": round(self.quality_score, 2),
            "cost_score": round(self.cost_score, 2),
            "overall_grade": self.overall_grade,
            "recommendations": self.recommendations,
        }


# ────────────────────────────────────────────────────────────────
# 混沌引擎主类
# ────────────────────────────────────────────────────────────────


class ChaosEngine:
    """混沌工程主引擎 — 协调故障注入与 SLO 度量.

    用途:
    1. 初始化测试环境 (Spot/Cache/Tiering 模拟器)
    2. 注入混沌场景
    3. 收集 SLA 度量
    4. 生成成本-质量双维度测试报告
    """

    def __init__(self, instance_count: int = 3, slos: Optional[List[SLODefinition]] = None):
        self._slos = slos or DEFAULT_SLOS
        self._spot = SpotInstanceSimulator(instance_count=instance_count)
        self._cache = CacheDegradationSimulator()
        self._tiering = DataTieringSimulator()
        self._snapshots: List[SLOSnapshot] = []
        self._scenarios_executed: List[str] = []
        self._total_requests = 0
        self._simulated_latency_ms: List[float] = []
        self._simulated_errors: int = 0
        self._start_time: Optional[str] = None
        self._end_time: Optional[str] = None

    # ── 场景注入 ────────────────────────────────────────────────

    def run_scenario(self, scenario_type: ChaosScenarioType, **kwargs) -> Dict[str, Any]:
        """运行单个混沌场景并测量 SLO.

        Args:
            scenario_type: 场景类型
            **kwargs: 场景参数
        """
        if self._start_time is None:
            self._start_time = datetime.now(timezone.utc).isoformat()

        self._scenarios_executed.append(scenario_type.value)
        scenario_data: Dict[str, Any] = {"scenario": scenario_type.value, "params": kwargs}

        # 恢复所有模拟器到健康状态
        self._spot = SpotInstanceSimulator(instance_count=self._spot._instance_count)
        self._cache.reset()
        self._tiering.reset()

        # 注入场景
        if scenario_type == ChaosScenarioType.SPOT_INTERRUPTION:
            scenario_data["result"] = self._spot.inject_interruption(
                kwargs.get("instance_id"))
        elif scenario_type == ChaosScenarioType.SPOT_RECLAIM:
            scenario_data["result"] = self._spot.inject_reclaim(
                kwargs.get("instance_id"))
        elif scenario_type == ChaosScenarioType.CACHE_MISS_STORM:
            scenario_data["result"] = self._cache.inject_cache_miss_storm(
                kwargs.get("severity", 0.5))
        elif scenario_type == ChaosScenarioType.CACHE_PENETRATION:
            scenario_data["result"] = self._cache.inject_cache_penetration(
                kwargs.get("penetration_ratio", 0.3))
        elif scenario_type == ChaosScenarioType.CACHE_AVALANCHE:
            scenario_data["result"] = self._cache.inject_cache_avalanche(
                kwargs.get("expired_ratio", 0.7))
        elif scenario_type == ChaosScenarioType.HOT_KEY_EXPIRY:
            scenario_data["result"] = self._cache.inject_hot_key_expiry(
                kwargs.get("key_count", 5))
        elif scenario_type == ChaosScenarioType.HOT_TIER_DEGRADATION:
            scenario_data["result"] = self._tiering.inject_hot_tier_degradation(
                kwargs.get("latency_multiplier", 10.0))
        elif scenario_type == ChaosScenarioType.WARM_TIER_SLOWDOWN:
            scenario_data["result"] = self._tiering.inject_warm_tier_slowdown(
                kwargs.get("latency_multiplier", 5.0))
        elif scenario_type == ChaosScenarioType.COLD_TIER_FAILURE:
            scenario_data["result"] = self._tiering.inject_cold_tier_failure()
        elif scenario_type == ChaosScenarioType.NETWORK_LATENCY:
            lat_ms = kwargs.get("latency_ms", 500)
            scenario_data["result"] = {"scenario": "network_latency", "injected_ms": lat_ms}
        elif scenario_type == ChaosScenarioType.COMBINED_STRESS:
            self._spot.inject_interruption()
            self._cache.inject_cache_miss_storm(0.3)
            self._tiering.inject_hot_tier_degradation(5.0)
            scenario_data["result"] = {"scenario": "combined_stress", "spot": "interrupted",
                                        "cache": "degraded", "tiering": "hot_degraded"}

        # 模拟请求并测量
        request_count = kwargs.get("request_count", 500)
        scenario_data["measurements"] = self._simulate_requests(
            request_count, scenario_type)

        # 收集 SLO 快照
        self._collect_slo_snapshots(scenario_type.value, scenario_data["measurements"])

        scenario_data["spot_state"] = self._spot.get_state()
        scenario_data["cache_metrics"] = self._cache.get_metrics()
        scenario_data["tiering_metrics"] = self._tiering.get_metrics()

        return scenario_data

    def _simulate_requests(self, count: int, scenario_type: ChaosScenarioType) -> Dict[str, Any]:
        """模拟大量请求并收集性能指标."""
        latencies: List[float] = []
        errors = 0
        cache_hits = 0

        for i in range(count):
            self._total_requests += 1

            # 基础延迟 (正常)
            base_lat = random.gauss(20, 5)

            # 场景特定延迟
            if scenario_type in (ChaosScenarioType.CACHE_MISS_STORM,
                                  ChaosScenarioType.CACHE_PENETRATION,
                                  ChaosScenarioType.CACHE_AVALANCHE,
                                  ChaosScenarioType.HOT_KEY_EXPIRY):
                key = f"key-{i % 10000:06d}"
                hit, cache_lat = self._cache.query_key(key)
                if hit:
                    cache_hits += 1
                lat = base_lat + cache_lat
            elif scenario_type in (ChaosScenarioType.HOT_TIER_DEGRADATION,
                                    ChaosScenarioType.WARM_TIER_SLOWDOWN,
                                    ChaosScenarioType.COLD_TIER_FAILURE):
                key = f"key-{i % 10000:06d}"
                tier, tier_lat, hit = self._tiering.query_tier(key)
                if hit:
                    cache_hits += 1
                lat = base_lat + tier_lat
            elif scenario_type == ChaosScenarioType.NETWORK_LATENCY:
                lat = base_lat + random.gauss(500, 50)
            else:
                hit = random.random() < 0.98
                if hit:
                    cache_hits += 1
                lat = base_lat + (random.gauss(2, 0.5) if hit else random.gauss(50, 10))

            # Spot 中断影响: 部分请求失败
            spot_state = self._spot.get_state()
            availability = spot_state["availability"]
            if random.random() > (availability / 100.0):
                errors += 1
                continue

            latencies.append(max(0.5, lat))

        sorted_lat = sorted(latencies)
        n = len(sorted_lat)
        return {
            "count": count,
            "errors": errors,
            "error_rate": (errors / count * 100) if count else 0.0,
            "cache_hits": cache_hits,
            "cache_hit_rate": (cache_hits / count * 100) if count else 0.0,
            "latency_avg_ms": sum(latencies) / len(latencies) if latencies else 0.0,
            "latency_p50_ms": sorted_lat[int(n * 0.50)] if n > 0 else 0.0,
            "latency_p99_ms": sorted_lat[int(n * 0.99)] if n > 1 else (sorted_lat[0] if n > 0 else 0.0),
            "latency_max_ms": max(latencies) if latencies else 0.0,
        }

    def _collect_slo_snapshots(self, scenario: str, measurements: Dict[str, Any]) -> None:
        """根据测量值收集 SLO 快照."""
        timestamp = datetime.now(timezone.utc).isoformat()

        metric_map = {
            "availability": 100.0 - measurements["error_rate"],
            "latency_p99_ms": measurements["latency_p99_ms"],
            "error_rate": measurements["error_rate"],
            "cache_hit_rate": measurements["cache_hit_rate"],
            "tier_availability": 100.0 if measurements["error_rate"] < 5 else 95.0,
        }

        for slo in self._slos:
            measured = metric_map.get(slo.metric, 0.0)
            passed, deviation = slo.evaluate(measured)
            self._snapshots.append(SLOSnapshot(
                timestamp=timestamp,
                sLO_name=slo.name,
                metric=slo.metric,
                measured=measured,
                target=slo.target,
                passed=passed,
                deviation=deviation,
                scenario=scenario,
            ))

    # ── 报告生成 ────────────────────────────────────────────────

    def generate_report(self, test_id: str = "chaos-default") -> ChaosTestReport:
        """生成混沌测试报告 — 成本-质量双维度."""
        self._end_time = datetime.now(timezone.utc).isoformat()
        report = ChaosTestReport(
            test_id=test_id,
            start_time=self._start_time or "",
            end_time=self._end_time,
            scenarios_executed=len(self._scenarios_executed),
            total_requests=self._total_requests,
        )

        # 按 SLO 聚合结果
        slo_aggregated: Dict[str, Dict[str, Any]] = {}
        for snap in self._snapshots:
            if snap.sLO_name not in slo_aggregated:
                slo_aggregated[snap.sLO_name] = {
                    "slo_name": snap.sLO_name,
                    "metric": snap.metric,
                    "target": snap.target,
                    "measurements": [],
                    "passed": 0,
                    "failed": 0,
                }
            agg = slo_aggregated[snap.sLO_name]
            agg["measurements"].append({
                "scenario": snap.scenario,
                "measured": round(snap.measured, 2),
                "passed": snap.passed,
                "deviation": round(snap.deviation, 4),
            })
            if snap.passed:
                agg["passed"] += 1
            else:
                agg["failed"] += 1

        # 填充 SLO 结果
        for slo_name, agg in slo_aggregated.items():
            total = agg["passed"] + agg["failed"]
            pass_rate = (agg["passed"] / total * 100) if total > 0 else 100.0
            report.slo_results.append({
                "slo_name": agg["slo_name"],
                "metric": agg["metric"],
                "target": agg["target"],
                "pass_rate": round(pass_rate, 1),
                "passed": agg["passed"],
                "failed": agg["failed"],
                "status": "PASS" if pass_rate >= 95.0 else ("FAIL" if pass_rate < 80.0 else "DEGRADED"),
                "details": agg["measurements"],
            })

        # 计算质量评分 (0-100)
        quality_score = self._calculate_quality_score(report.slo_results)
        report.quality_score = quality_score

        # 计算成本评分 (0-100, 越低越好 → 越高分)
        cost_score = self._calculate_cost_score(report.slo_results)
        report.cost_score = cost_score

        # 综合评分
        overall = quality_score * 0.6 + cost_score * 0.4
        report.overall_grade = self._score_to_grade(overall)

        # 成本估计
        report.cost_estimation = self._estimate_cost()

        # 改进建议
        report.recommendations = self._generate_recommendations(report.slo_results)

        return report

    def _calculate_quality_score(self, slo_results: List[Dict[str, Any]]) -> float:
        """根据 SLO 达标率计算质量评分."""
        if not slo_results:
            return 100.0
        total_weight = sum(s.weight for s in self._slos)
        score = 0.0
        for result in slo_results:
            slo = next((s for s in self._slos if s.name == result["slo_name"]), None)
            if slo:
                weight = slo.weight / total_weight if total_weight > 0 else 1.0 / len(slo_results)
                score += result["pass_rate"] * weight
        return round(score, 1)

    def _calculate_cost_score(self, slo_results: List[Dict[str, Any]]) -> float:
        """根据成本敏感度计算成本评分."""
        # 成本评分: 高可用 = 高成本, 需要在质量和成本之间平衡
        # 如果所有 SLO 都通过，说明可能过度配置 (高成本)
        # 反之，如果全部失败，说明配置不足
        if not slo_results:
            return 50.0

        all_pass = all(r["pass_rate"] >= 95.0 for r in slo_results)
        any_fail = any(r["status"] == "FAIL" for r in slo_results)

        if all_pass:
            # 全部通过 → 可能存在过度配置，成本评分略降
            return 85.0
        elif any_fail:
            # 有失败 → 配置不足，成本评分低但需要改进
            failed_count = sum(1 for r in slo_results if r["status"] == "FAIL")
            return max(20.0, 60.0 - failed_count * 10.0)
        else:
            # 混合状态 → 比较平衡
            return 75.0

    def _score_to_grade(self, score: float) -> str:
        """将评分映射到 A~E 等级."""
        if score >= 90:
            return "A"
        elif score >= 80:
            return "B"
        elif score >= 70:
            return "C"
        elif score >= 60:
            return "D"
        else:
            return "E"

    def _estimate_cost(self) -> Dict[str, Any]:
        """估计当前配置的成本."""
        spot_state = self._spot.get_state()
        running = spot_state["running_count"]
        total = spot_state["total_count"]

        # 模拟成本计算: Spot 实例比 On-Demand 便宜 60-70%
        on_demand_hourly = 0.50  # 假设 On-Demand $0.50/h
        spot_discount = 0.65     # 65% 折扣
        spot_hourly = on_demand_hourly * (1 - spot_discount)

        spot_cost = running * spot_hourly
        on_demand_cost = running * on_demand_hourly

        cache_cost = 0.10  # 缓存层成本 $0.10/h (ElastiCache 小节点)
        tiering_cost = 0.05 * 3  # 三层存储成本

        total_hourly = spot_cost + cache_cost + tiering_cost
        total_monthly = total_hourly * 730  # 约一个月的小时数

        return {
            "spot_instances": running,
            "spot_hourly_rate": round(spot_hourly, 4),
            "spot_monthly": round(spot_cost * 730, 2),
            "savings_vs_on_demand": round((on_demand_cost - spot_cost) * 730, 2),
            "cache_monthly": round(cache_cost * 730, 2),
            "tiering_monthly": round(tiering_cost * 730, 2),
            "total_monthly_estimated": round(total_monthly, 2),
            "efficiency_ratio": round(on_demand_cost / max(spot_cost, 0.001), 2),
        }

    def _generate_recommendations(self, slo_results: List[Dict[str, Any]]) -> List[str]:
        """根据 SLO 结果生成改进建议."""
        recommendations = []

        for result in slo_results:
            if result["status"] == "FAIL":
                if result["slo_name"] == "可用性":
                    recommendations.append(
                        "⚠️ 可用性不达标: 建议增加 Spot 实例冗余 (至少 N+1)，"
                        "配置跨可用区分散部署，缩短中断通知处理时间 (< 30s)"
                    )
                elif result["slo_name"] == "P99 延迟":
                    recommendations.append(
                        "⚠️ P99 延迟超标: 建议优化缓存预热策略，"
                        "为热点数据启用本地缓存 (LocalCache)，考虑读写分离"
                    )
                elif result["slo_name"] == "错误率":
                    recommendations.append(
                        "⚠️ 错误率超标: 建议增强重试机制 (指数退避 + 抖动)，"
                        "完善熔断降级策略，配置 fallback 路径"
                    )
                elif result["slo_name"] == "缓存命中率":
                    recommendations.append(
                        "⚠️ 缓存命中率低: 建议增大缓存容量，"
                        "优化 Key 过期策略 (TTL 随机化防雪崩)，"
                        "启用布隆过滤器防穿透，配置热点 Key 自动发现"
                    )
                elif result["slo_name"] == "数据分层可用率":
                    recommendations.append(
                        "⚠️ 数据分层可用率不足: 建议热层启用双副本，"
                        "温层配置自动提升 (Promotion) 策略，"
                        "冷层增加超时重试与 fallback 到温层"
                    )

        # 成本-质量平衡建议
        passed_count = sum(1 for r in slo_results if r["status"] == "PASS")
        if passed_count == len(slo_results):
            recommendations.append(
                "✅ 所有 SLO 达标: 当前配置成本略高，可考虑进一步降低 Spot 实例数 "
                "或使用更小规格缓存节点来优化成本"
            )

        if not recommendations:
            recommendations.append("✅ 系统在当前混沌场景下表现良好，无需紧急改进")

        return recommendations

    def reset(self) -> None:
        """重置引擎状态."""
        self._spot = SpotInstanceSimulator(instance_count=self._spot._instance_count)
        self._cache.reset()
        self._tiering.reset()
        self._snapshots.clear()
        self._scenarios_executed.clear()
        self._total_requests = 0
        self._simulated_latency_ms.clear()
        self._simulated_errors = 0
        self._start_time = None
        self._end_time = None

    # ── 状态查询 ────────────────────────────────────────────────

    def get_spot_state(self) -> Dict[str, Any]:
        return self._spot.get_state()

    def get_cache_metrics(self) -> Dict[str, Any]:
        return self._cache.get_metrics()

    def get_tiering_metrics(self) -> Dict[str, Any]:
        return self._tiering.get_metrics()

    def get_slo_summary(self) -> Dict[str, Any]:
        """获取 SLO 汇总."""
        if not self._snapshots:
            return {"status": "no_data", "message": "尚未执行混沌场景"}
        slo_names = set(s.sLO_name for s in self._snapshots)
        summary = {}
        for name in slo_names:
            snaps = [s for s in self._snapshots if s.sLO_name == name]
            passed = sum(1 for s in snaps if s.passed)
            summary[name] = {
                "total": len(snaps),
                "passed": passed,
                "pass_rate": round(passed / len(snaps) * 100, 1) if snaps else 0,
            }
        return summary
