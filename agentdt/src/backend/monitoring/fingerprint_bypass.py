# -*- coding: utf-8 -*-
"""
指纹遥测旁路 Channel — 非侵入式行为指纹异步采集.

基于 MarineChannel 实现，在不干扰主业务流程的前提下:
1. 定期快照 A/B 测试行为指纹 (突变率、升级异常等)
2. 异步采集 Agent 执行日志中的指纹信号
3. 将指纹数据推入 TraceCollector 供后续分析与面板展示
4. 支持 ConfigMap 热更新采样策略

设计原则:
- 旁路 (bypass): 永不阻塞主业务，所有采集走 asyncio 后台任务
- 采样优先: 正常模式下仅 P0 字段实时采集，P1/P2 降频
- 降级全量: 异常检测触发时自动提升为全量采集
"""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

from channels.marine_base import (
    ChannelPriority,
    ChannelStatus,
    ChannelEvent,
    MarineChannel,
)

from .models import (
    MonitoringMetrics,
    SamplingConfig,
    SamplingDecision,
    SpanPriority,
    TraceContext,
    TraceSpan,
)

logger = logging.getLogger(__name__)


# ── Fingerprint Data Models ──────────────────────────────────────────────


@dataclass
class BehaviorFingerprint:
    """Agent 行为指纹快照 — 从 A/B 测试指标中提取的关键信号."""

    fingerprint_id: str = ""
    agent_id: str = ""
    team_id: str = ""
    trace_id: str = ""

    # 核心指纹字段 (P0 — 实时必采)
    false_upgrade_rate: float = 0.0
    behavior_fingerprint_mutation_rate: float = 0.0
    anomaly_propagation_depth: float = 0.0
    prediction_error_rate: float = 0.0

    # 扩展指纹字段 (P1 — 条件采样)
    resource_increase_pct: float = 0.0
    energy_increase_pct: float = 0.0
    policy_evaluation_latency_ms: float = 0.0
    evolution_stagnation_rate: float = 0.0

    # 衍生指纹 (P2 — 离线批量)
    temperature_slope: float = 0.0
    anomaly_score: float = 0.0
    ewma_threshold_breach: bool = False

    # 元数据
    collected_at: str = ""
    source: str = "fingerprint_bypass"
    extra: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.fingerprint_id:
            self.fingerprint_id = str(uuid4())[:8]
        if not self.collected_at:
            self.collected_at = datetime.now(timezone.utc).isoformat()

    def to_metrics(self) -> MonitoringMetrics:
        """转换为 MonitoringMetrics 供 TraceCollector 消费."""
        return MonitoringMetrics(
            span_id=self.fingerprint_id,
            trace_id=self.trace_id,
            span_name="behavior_fingerprint",
            false_upgrade_rate=self.false_upgrade_rate,
            resource_increase_pct=self.resource_increase_pct,
            behavior_fingerprint_mutation_rate=self.behavior_fingerprint_mutation_rate,
            anomaly_propagation_depth=self.anomaly_propagation_depth,
            prediction_error_rate=self.prediction_error_rate,
            energy_increase_pct=self.energy_increase_pct,
            temperature_slope=self.temperature_slope,
            policy_evaluation_latency_ms=self.policy_evaluation_latency_ms,
            evolution_stagnation_rate=self.evolution_stagnation_rate,
            anomaly_score=self.anomaly_score,
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "fingerprint_id": self.fingerprint_id,
            "agent_id": self.agent_id,
            "team_id": self.team_id,
            "trace_id": self.trace_id,
            "false_upgrade_rate": self.false_upgrade_rate,
            "behavior_fingerprint_mutation_rate": self.behavior_fingerprint_mutation_rate,
            "anomaly_propagation_depth": self.anomaly_propagation_depth,
            "prediction_error_rate": self.prediction_error_rate,
            "resource_increase_pct": self.resource_increase_pct,
            "energy_increase_pct": self.energy_increase_pct,
            "policy_evaluation_latency_ms": self.policy_evaluation_latency_ms,
            "evolution_stagnation_rate": self.evolution_stagnation_rate,
            "temperature_slope": self.temperature_slope,
            "anomaly_score": self.anomaly_score,
            "ewma_threshold_breach": self.ewma_threshold_breach,
            "collected_at": self.collected_at,
            "source": self.source,
            "extra": self.extra,
        }


@dataclass
class FingerprintBuffer:
    """指纹遥测本地缓冲 — 环形队列，避免内存无限增长."""

    max_size: int = 1000
    fingerprints: List[BehaviorFingerprint] = field(default_factory=list)
    _lock: asyncio.Lock = field(default_factory=asyncio.Lock)

    async def push(self, fp: BehaviorFingerprint) -> None:
        async with self._lock:
            self.fingerprints.append(fp)
            if len(self.fingerprints) > self.max_size:
                self.fingerprints = self.fingerprints[-self.max_size:]

    async def drain(self, limit: int = 100) -> List[BehaviorFingerprint]:
        """取出并清空缓冲中的指纹."""
        async with self._lock:
            drained = self.fingerprints[:limit]
            self.fingerprints = self.fingerprints[limit:]
            return drained

    async def snapshot(self) -> List[BehaviorFingerprint]:
        """获取当前快照 (不清空)."""
        async with self._lock:
            return list(self.fingerprints)

    @property
    async def size(self) -> int:
        async with self._lock:
            return len(self.fingerprints)


# ── Fingerprint Telemetry Bypass Channel ──────────────────────────────────


class FingerprintTelemetryChannel(MarineChannel):
    """指纹遥测旁路 Channel — 非侵入式行为指纹采集.

    继承 MarineChannel，实现 process_event / get_status。
    不做任何阻塞主业务的操作，所有采集走 asyncio 后台循环。
    """

    channel_name: str = "fingerprint_telemetry"
    priority: ChannelPriority = ChannelPriority.P1

    def __init__(self, sampling_config: Optional[SamplingConfig] = None):
        super().__init__(name=self.channel_name, priority=self.priority)
        self._buffer = FingerprintBuffer()
        self._sampling_config = sampling_config or SamplingConfig()
        self._collect_task: Optional[asyncio.Task] = None
        self._snapshot_interval: float = 5.0  # 快照间隔 (秒)
        self._last_snapshot_time: float = 0.0
        self._fingerprints_collected: int = 0
        self._fingerprints_dropped: int = 0
        self._anomaly_detected: bool = False

    # ── MarineChannel 接口 ──────────────────────────────────────────────

    def initialize(self) -> None:
        """初始化 Channel，启动后台采集循环."""
        self.status = ChannelStatus.OK
        self._collect_task = asyncio.ensure_future(self._collection_loop())
        logger.info("🔍 FingerprintTelemetryChannel initialized — bypass mode active")

    async def process_event(self, event: ChannelEvent) -> bool:
        """处理遥测事件 — 从主业务旁路接收指纹信号.

        事件类型:
        - agent_loop_iteration: Agent 循环迭代事件 (携带 A/B 指标)
        - plaza_discussion_turn: 广场讨论轮次事件
        - ewma_breach: EWMA 阈值突破事件 (触发降级全量)
        - handoff_executed: Agent 交接事件
        """
        try:
            if event.event_type == "ewma_breach":
                self._anomaly_detected = True
                logger.warning("⚠️ EWMA breach detected — enabling full fingerprint collection")

            elif event.event_type == "agent_loop_iteration":
                await self._collect_from_agent_loop(event)

            elif event.event_type in ("plaza_discussion_turn", "handoff_executed"):
                await self._collect_from_collaboration(event)

            elif event.event_type == "reset_anomaly":
                self._anomaly_detected = False
                logger.info("✅ Anomaly cleared — resuming normal fingerprint sampling")

            return True
        except Exception as e:
            logger.error(f"FingerprintTelemetryChannel process_event error: {e}", exc_info=True)
            return False

    def get_status(self) -> Dict[str, Any]:
        """返回 Channel 运行状态."""
        return {
            "channel": self.channel_name,
            "status": self.status.value,
            "priority": self.priority.value,
            "fingerprints_collected": self._fingerprints_collected,
            "fingerprints_dropped": self._fingerprints_dropped,
            "buffer_size": len(self._buffer.fingerprints),
            "anomaly_detected": self._anomaly_detected,
            "snapshot_interval_s": self._snapshot_interval,
            "sampling_config": {
                "p0_rate": self._sampling_config.p0_sample_rate,
                "p1_rate": self._sampling_config.p1_sample_rate,
                "p2_rate": self._sampling_config.p2_sample_rate,
                "degradation_mode": self._sampling_config.degradation_mode,
            },
        }

    async def shutdown(self) -> None:
        """优雅关闭 — 取消后台任务."""
        if self._collect_task:
            self._collect_task.cancel()
            try:
                await self._collect_task
            except asyncio.CancelledError:
                pass
        self.status = ChannelStatus.OFF
        logger.info("FingerprintTelemetryChannel shutdown complete")

    # ── 采集逻辑 ───────────────────────────────────────────────────────

    async def _collection_loop(self) -> None:
        """后台采集循环 — 定期快照 + 异步上报."""
        while self.status != ChannelStatus.OFF:
            try:
                await asyncio.sleep(self._snapshot_interval)
                if self.status == ChannelStatus.OFF:
                    break
                await self._periodic_snapshot()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Fingerprint collection loop error: {e}", exc_info=True)
                await asyncio.sleep(1.0)

    async def _periodic_snapshot(self) -> None:
        """定期快照: 将缓冲中的指纹推入 TraceCollector."""
        try:
            from .collector import TraceCollector, get_collector
            collector = get_collector()
        except Exception:
            logger.debug("TraceCollector not available, skipping snapshot")
            return

        fps = await self._buffer.drain(limit=50)
        for fp in fps:
            try:
                trace_ctx = TraceContext(
                    trace_id=fp.trace_id or str(uuid4()),
                    parent_span_id="",
                    span_id=fp.fingerprint_id,
                )
                span = TraceSpan(
                    span_id=fp.fingerprint_id,
                    trace_id=trace_ctx.trace_id,
                    parent_span_id="",
                    span_name="behavior_fingerprint",
                    priority=SpanPriority.P0 if self._anomaly_detected else SpanPriority.P1,
                    metrics=fp.to_metrics(),
                    tags={
                        "agent_id": fp.agent_id,
                        "team_id": fp.team_id,
                        "source": fp.source,
                        "bypass": "true",
                    },
                )
                collector.ingest(span)
            except Exception as e:
                logger.debug(f"Failed to push fingerprint to collector: {e}")

    async def _collect_from_agent_loop(self, event: ChannelEvent) -> None:
        """从 Agent 循环迭代事件中提取指纹."""
        data = event.data or {}
        fp = BehaviorFingerprint(
            agent_id=data.get("agent_id", ""),
            team_id=data.get("team_id", ""),
            trace_id=data.get("trace_id", ""),
            false_upgrade_rate=data.get("false_upgrade_rate", 0.0),
            behavior_fingerprint_mutation_rate=data.get("behavior_fingerprint_mutation_rate", 0.0),
            anomaly_propagation_depth=data.get("anomaly_propagation_depth", 0.0),
            prediction_error_rate=data.get("prediction_error_rate", 0.0),
            resource_increase_pct=data.get("resource_increase_pct", 0.0),
            energy_increase_pct=data.get("energy_increase_pct", 0.0),
            policy_evaluation_latency_ms=data.get("policy_evaluation_latency_ms", 0.0),
            evolution_stagnation_rate=data.get("evolution_stagnation_rate", 0.0),
            temperature_slope=data.get("temperature_slope", 0.0),
            anomaly_score=data.get("anomaly_score", 0.0),
            ewma_threshold_breach=data.get("ewma_threshold_breach", False),
            extra=data.get("extra", {}),
        )
        await self._buffer.push(fp)
        self._fingerprints_collected += 1

    async def _collect_from_collaboration(self, event: ChannelEvent) -> None:
        """从协作事件 (Plaza / Handoff) 中提取指纹."""
        data = event.data or {}
        fp = BehaviorFingerprint(
            agent_id=data.get("agent_id", ""),
            team_id=data.get("team_id", ""),
            trace_id=data.get("trace_id", ""),
            behavior_fingerprint_mutation_rate=data.get("mutation_rate", 0.0),
            anomaly_propagation_depth=data.get("propagation_depth", 0.0),
            prediction_error_rate=data.get("error_rate", 0.0),
            extra={
                "event_type": event.event_type,
                "discussion_id": data.get("discussion_id", ""),
                "plaza_id": data.get("plaza_id", ""),
            },
        )
        await self._buffer.push(fp)
        self._fingerprints_collected += 1

    # ── 查询接口 ───────────────────────────────────────────────────────

    async def get_recent_fingerprints(self, limit: int = 50) -> List[Dict[str, Any]]:
        """获取最近采集的指纹数据 (供 API 面板查询)."""
        fps = await self._buffer.snapshot()
        return [fp.to_dict() for fp in fps[-limit:]]

    async def get_stats(self) -> Dict[str, Any]:
        """获取指纹采集统计."""
        return {
            "total_collected": self._fingerprints_collected,
            "total_dropped": self._fingerprints_dropped,
            "buffer_size": await self._buffer.size,
            "anomaly_detected": self._anomaly_detected,
            "last_snapshot_time": self._last_snapshot_time,
        }


# ── 全局单例 ───────────────────────────────────────────────────────────

_fingerprint_channel: Optional[FingerprintTelemetryChannel] = None


def get_fingerprint_channel() -> FingerprintTelemetryChannel:
    """获取全局 FingerprintTelemetryChannel 单例."""
    global _fingerprint_channel
    if _fingerprint_channel is None:
        _fingerprint_channel = FingerprintTelemetryChannel()
    return _fingerprint_channel
