# -*- coding: utf-8 -*-
"""
Trace 采集器 — 本地缓冲 + 异步上报.

负责:
1. 接收 TraceSpan 并做采样决策
2. 本地缓冲已采样数据
3. 异步批量上报
4. 降级场景强制全量采集
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional

from .models import (
    MonitoringMetrics,
    SamplingConfig,
    SpanPriority,
    TelemetryRecord,
    TraceSpan,
)
from .sampler import AdaptiveSampler

logger = logging.getLogger(__name__)


class TraceCollector:
    """Trace 采集器 — 本地缓冲 + 异步上报.

    使用 asyncio 实现非阻塞采集，支持自定义上报回调函数。
    """

    def __init__(
        self,
        sampler: Optional[AdaptiveSampler] = None,
        config: Optional[SamplingConfig] = None,
        upload_callback: Optional[Callable[[List[Dict[str, Any]]], None]] = None,
    ):
        self._sampler = sampler or AdaptiveSampler(config or SamplingConfig())
        self._upload_callback = upload_callback
        self._buffer: List[Dict[str, Any]] = []
        self._p2_buffer: List[Dict[str, Any]] = []
        self._metrics = MonitoringMetrics()
        self._running = False
        self._flush_task: Optional[asyncio.Task] = None
        self._lock = asyncio.Lock()

        # 用于 CI/CD 校验的遥测记录
        self._telemetry_records: List[TelemetryRecord] = []

    @property
    def sampler(self) -> AdaptiveSampler:
        return self._sampler

    @property
    def metrics(self) -> MonitoringMetrics:
        return self._metrics

    @property
    def config(self) -> SamplingConfig:
        return self._sampler.config

    def update_config(self, config_dict: dict):
        """热更新采样策略."""
        self._sampler.update_from_dict(config_dict)
        logger.info(f"📋 采集器配置已更新: {config_dict}")

    async def start(self):
        """启动异步刷新任务."""
        if self._running:
            return
        self._running = True
        self._flush_task = asyncio.create_task(self._flush_loop())
        logger.info("📡 TraceCollector 已启动")

    async def stop(self):
        """停止采集器并刷新剩余数据."""
        self._running = False
        if self._flush_task:
            self._flush_task.cancel()
            try:
                await self._flush_task
            except asyncio.CancelledError:
                pass
        await self._flush_now()
        logger.info("📡 TraceCollector 已停止")

    async def record(self, span: TraceSpan) -> bool:
        """记录一个 TraceSpan.

        流程:
        1. 采样决策
        2. 如果采样 → 加入缓冲
        3. 更新指标

        Returns:
            True 如果被采样并加入缓冲
        """
        decision = self._sampler.decide(span)
        self._metrics.total_spans += 1

        if not decision.should_sample:
            return False

        # 更新指标
        self._metrics.sampled_spans += 1
        if decision.priority == SpanPriority.P0:
            self._metrics.p0_spans += 1
        elif decision.priority == SpanPriority.P1:
            self._metrics.p1_spans += 1
        else:
            self._metrics.p2_spans += 1

        if span.status in ("error", "critical"):
            self._metrics.error_spans += 1

        if span.event_type == "fallback_triggered":
            self._metrics.fallback_count += 1

        # 更新平均异常评分和耗时
        n = self._metrics.total_spans
        self._metrics.avg_anomaly_score += (
            span.anomaly_score - self._metrics.avg_anomaly_score
        ) / n
        self._metrics.avg_duration_ms += (
            span.duration_ms - self._metrics.avg_duration_ms
        ) / n

        # 降级场景或高异常 → 全量采集
        include_all = (
            self._sampler.config.degradation_mode
            or span.anomaly_score >= self._sampler.config.anomaly_threshold_high
            or span.event_type == "fallback_triggered"
        )

        span_dict = span.to_dict(include_all=include_all)

        # 记录遥测记录（用于 CI/CD 校验）
        p0_fields = list(span.get_p0_fields().keys())
        p1_fields = list(span.get_p1_fields().keys())
        p2_fields = list(span.get_p2_fields().keys())
        all_expected = p0_fields + (p1_fields if include_all else []) + (p2_fields if include_all else [])
        fields_present = [k for k in all_expected if k in span_dict]
        fields_missing = [k for k in all_expected if k not in span_dict]

        record = TelemetryRecord(
            trace_id=span.trace_id,
            span_id=span.span_id,
            event_type=span.event_type,
            timestamp=span.timestamp,
            sampled=True,
            priority=decision.priority.value,
            fields_present=fields_present,
            fields_missing=fields_missing,
            anomaly_score=span.anomaly_score,
            status=span.status,
            duration_ms=span.duration_ms,
        )
        self._telemetry_records.append(record)

        # 加入缓冲
        async with self._lock:
            if decision.priority == SpanPriority.P2:
                self._p2_buffer.append(span_dict)
            else:
                self._buffer.append(span_dict)

            # 缓冲上限保护
            max_size = self._sampler.config.max_buffer_size
            if len(self._buffer) > max_size:
                overflow = self._buffer[:-max_size]
                self._buffer = self._buffer[-max_size:]
                logger.warning(f"⚠️ 缓冲溢出，丢弃 {len(overflow)} 条记录")

        return True

    async def _flush_loop(self):
        """定时刷新循环."""
        interval = self._sampler.config.flush_interval_s
        while self._running:
            try:
                await asyncio.sleep(interval)
                await self._flush_now()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"❌ 刷新循环异常: {e}")

    async def _flush_now(self):
        """立即刷新缓冲数据."""
        async with self._lock:
            if not self._buffer and not self._p2_buffer:
                return
            batch = list(self._buffer)
            p2_batch = list(self._p2_buffer)
            self._buffer.clear()
            self._p2_buffer.clear()

        all_data = batch + p2_batch
        if not all_data:
            return

        self._metrics.last_flush_timestamp = datetime.now(timezone.utc).isoformat()
        self._metrics.buffer_usage_pct = 0.0

        if self._upload_callback:
            try:
                if asyncio.iscoroutinefunction(self._upload_callback):
                    await self._upload_callback(all_data)
                else:
                    self._upload_callback(all_data)
                logger.debug(f"📤 上报 {len(all_data)} 条追踪数据")
            except Exception as e:
                logger.error(f"❌ 上报失败: {e}")
                # 上报失败重新入队
                async with self._lock:
                    self._buffer.extend(batch)
                    self._p2_buffer.extend(p2_batch)
        else:
            logger.debug(f"📤 (无回调) 缓冲 {len(all_data)} 条追踪数据")

    async def flush(self) -> int:
        """手动触发刷新，返回刷新的记录数."""
        await self._flush_now()
        return len(self._buffer) + len(self._p2_buffer)

    def record_fingerprint_stability(self, stability_report: Dict[str, Any]) -> None:
        """记录指纹稳定性监控埋点.

        由 agents.fingerprint 模块在计算指纹后调用,
        将稳定性数据纳入监控体系。

        Args:
            stability_report: FingerprintEngine.get_stability_report() 的返回值
        """
        self._metrics.fingerprint_mutation_rate = stability_report.get(
            "mutation_rate", 0.0
        )
        self._metrics.fingerprint_is_stable = stability_report.get(
            "is_stable", True
        )
        self._metrics.fingerprint_total = stability_report.get(
            "total_fingerprints", 0
        )

        # 变异率超阈值时记录告警事件
        threshold = stability_report.get("alert_threshold", 0.05)
        mutation_rate = stability_report.get("mutation_rate", 0.0)
        if mutation_rate > threshold:
            logger.warning(
                "⚠️ 指纹变异率 %.4f 超过阈值 %.4f (total=%d)",
                mutation_rate, threshold,
                stability_report.get("total_fingerprints", 0),
            )
            self._metrics.fingerprint_alert_count += 1

        logger.debug(
            "📊 指纹稳定性埋点: mutation_rate=%.4f stable=%s",
            mutation_rate, stability_report.get("is_stable"),
        )

    def get_telemetry_records(
        self, limit: int = 100, status_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """获取遥测记录（用于 CI/CD 门禁校验）."""
        records = self._telemetry_records[-limit:]
        if status_filter:
            records = [r for r in records if r.status == status_filter]
        return [r.to_dict() for r in records]

    def get_metrics(self) -> Dict[str, Any]:
        """获取当前指标."""
        self._metrics.buffer_usage_pct = round(
            (len(self._buffer) + len(self._p2_buffer))
            / max(self._sampler.config.max_buffer_size, 1) * 100,
            2,
        )
        return self._metrics.to_dict()

    def get_sampler_stats(self) -> dict:
        """获取采样器统计."""
        return self._sampler.get_stats()
