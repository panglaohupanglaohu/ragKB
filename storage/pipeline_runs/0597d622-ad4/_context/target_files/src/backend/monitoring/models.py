# -*- coding: utf-8 -*-
"""
监控数据模型 — 全链路追踪与埋点字段定义

遵循 W3C Trace Context 标准，定义 P0/P1/P2 三级埋点字段。
"""

from __future__ import annotations

import enum
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


class SpanPriority(str, enum.Enum):
    """埋点优先级 — P0 实时必采 / P1 条件采样 / P2 离线批量."""
    P0 = "P0"  # 实时必采
    P1 = "P1"  # 条件采样
    P2 = "P2"  # 离线批量


class PlazaEventType(str, enum.Enum):
    """广场事件类型."""
    DISCUSSION_CREATED = "discussion_created"
    DISCUSSION_STARTED = "discussion_started"
    DISCUSSION_ENDED = "discussion_ended"
    PARTICIPANT_JOINED = "participant_joined"
    PARTICIPANT_LEFT = "participant_left"
    MESSAGE_SENT = "message_sent"
    MODERATOR_SUMMARY = "moderator_summary"
    PLAN_ASSIGNED = "plan_assigned"
    SSE_STREAM_STARTED = "sse_stream_started"
    SSE_STREAM_ENDED = "sse_stream_ended"
    FALLBACK_TRIGGERED = "fallback_triggered"
    ERROR_OCCURRED = "error_occurred"
    LLM_CALL_STARTED = "llm_call_started"
    LLM_CALL_COMPLETED = "llm_call_completed"
    LLM_CALL_FAILED = "llm_call_failed"
    SAMPLING_ADJUSTED = "sampling_adjusted"
    DEGRADATION_ACTIVATED = "degradation_activated"


@dataclass
class TraceContext:
    """W3C Trace Context — 全链路追踪上下文."""
    trace_id: str = field(default_factory=lambda: uuid.uuid4().hex[:32])
    span_id: str = field(default_factory=lambda: uuid.uuid4().hex[:16])
    parent_span_id: Optional[str] = None
    sampled: bool = True
    trace_flags: str = "01"  # W3C trace flags

    def to_w3c_traceparent(self) -> str:
        """生成 W3C traceparent 头: version-trace_id-span_id-flags."""
        return f"00-{self.trace_id}-{self.span_id}-{self.trace_flags}"

    @classmethod
    def from_w3c_traceparent(cls, traceparent: str) -> Optional["TraceContext"]:
        """从 W3C traceparent 解析."""
        parts = traceparent.split("-")
        if len(parts) != 4:
            return None
        return cls(
            trace_id=parts[1],
            span_id=parts[2],
            trace_flags=parts[3],
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "trace_id": self.trace_id,
            "span_id": self.span_id,
            "parent_span_id": self.parent_span_id,
            "sampled": self.sampled,
            "trace_flags": self.trace_flags,
        }


@dataclass
class TraceSpan:
    """单个追踪 Span — 代表一次操作/事件的完整追踪信息.

    P0 字段 (实时必采):
        trace_id, span_id, parent_span_id, event_type, timestamp,
        anomaly_score, status, duration_ms, source

    P1 字段 (条件采样):
        model_version, gpu_power_w, cpu_usage_pct, memory_mb,
        token_count, latency_p99_ms, agent_id, session_id

    P2 字段 (离线批量):
        node_pue, thermal_sensor_c, energy_kwh, carbon_g,
        network_rtt_ms, disk_iops, container_restart_count
    """
    # ── 核心字段 (P0) ──
    trace_id: str
    span_id: str
    parent_span_id: Optional[str] = None
    event_type: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    anomaly_score: float = 0.0
    status: str = "ok"  # ok | warning | error | critical
    duration_ms: float = 0.0
    source: str = "plaza"  # plaza | api_gateway | websocket | sidecar

    # ── 扩展字段 (P1) ──
    model_version: Optional[str] = None
    gpu_power_w: Optional[float] = None
    cpu_usage_pct: Optional[float] = None
    memory_mb: Optional[float] = None
    token_count: Optional[int] = None
    latency_p99_ms: Optional[float] = None
    agent_id: Optional[str] = None
    session_id: Optional[str] = None

    # ── 扩展字段 (P2) ──
    node_pue: Optional[float] = None
    thermal_sensor_c: Optional[float] = None
    energy_kwh: Optional[float] = None
    carbon_g: Optional[float] = None
    network_rtt_ms: Optional[float] = None
    disk_iops: Optional[int] = None
    container_restart_count: Optional[int] = None

    # ── 元数据 ──
    tags: Dict[str, str] = field(default_factory=dict)
    error_message: Optional[str] = None
    plaza_id: Optional[str] = None
    discussion_id: Optional[str] = None

    def get_priority(self) -> SpanPriority:
        """根据字段填充情况判断优先级."""
        if self.anomaly_score >= 0.7 or self.status in ("error", "critical"):
            return SpanPriority.P0
        if self.anomaly_score >= 0.3:
            return SpanPriority.P1
        return SpanPriority.P2

    def get_p0_fields(self) -> Dict[str, Any]:
        """获取 P0 必采字段."""
        return {
            "trace_id": self.trace_id,
            "span_id": self.span_id,
            "parent_span_id": self.parent_span_id,
            "event_type": self.event_type,
            "timestamp": self.timestamp,
            "anomaly_score": self.anomaly_score,
            "status": self.status,
            "duration_ms": self.duration_ms,
            "source": self.source,
        }

    def get_p1_fields(self) -> Dict[str, Any]:
        """获取 P1 条件采样字段."""
        return {
            k: v for k, v in {
                "model_version": self.model_version,
                "gpu_power_w": self.gpu_power_w,
                "cpu_usage_pct": self.cpu_usage_pct,
                "memory_mb": self.memory_mb,
                "token_count": self.token_count,
                "latency_p99_ms": self.latency_p99_ms,
                "agent_id": self.agent_id,
                "session_id": self.session_id,
            }.items() if v is not None
        }

    def get_p2_fields(self) -> Dict[str, Any]:
        """获取 P2 离线批量字段."""
        return {
            k: v for k, v in {
                "node_pue": self.node_pue,
                "thermal_sensor_c": self.thermal_sensor_c,
                "energy_kwh": self.energy_kwh,
                "carbon_g": self.carbon_g,
                "network_rtt_ms": self.network_rtt_ms,
                "disk_iops": self.disk_iops,
                "container_restart_count": self.container_restart_count,
            }.items() if v is not None
        }

    def to_dict(self, include_all: bool = False) -> Dict[str, Any]:
        """序列化.

        Args:
            include_all: 是否包含所有字段（降级场景全量采集时使用）
        """
        result = self.get_p0_fields()
        if include_all or self.anomaly_score >= 0.7:
            result.update(self.get_p1_fields())
            result.update(self.get_p2_fields())
        elif self.anomaly_score >= 0.3:
            result.update(self.get_p1_fields())
        result["tags"] = self.tags
        if self.error_message:
            result["error_message"] = self.error_message
        if self.plaza_id:
            result["plaza_id"] = self.plaza_id
        if self.discussion_id:
            result["discussion_id"] = self.discussion_id
        return result


@dataclass
class SamplingDecision:
    """采样决策结果."""
    should_sample: bool
    priority: SpanPriority
    sample_rate: float
    reason: str = ""


@dataclass
class SamplingConfig:
    """采样策略配置 — 支持 ConfigMap 热更新."""
    base_sample_rate: float = 0.1       # 基础采样率 10%
    high_anomaly_rate: float = 1.0      # 高异常评分采样率 100%
    medium_anomaly_rate: float = 0.5    # 中异常评分采样率 50%
    anomaly_threshold_high: float = 0.7
    anomaly_threshold_medium: float = 0.3
    p1_sample_rate: float = 0.3         # P1 字段采样率
    p2_batch_interval_s: int = 60       # P2 批量上报间隔(秒)
    max_buffer_size: int = 10000        # 本地缓冲最大条数
    flush_interval_s: int = 10          # 异步上报间隔(秒)
    degradation_mode: bool = False      # 降级模式（全量采集）
    schema_version: str = "1.0"         # Schema 版本号

    def to_dict(self) -> Dict[str, Any]:
        return {
            "base_sample_rate": self.base_sample_rate,
            "high_anomaly_rate": self.high_anomaly_rate,
            "medium_anomaly_rate": self.medium_anomaly_rate,
            "anomaly_threshold_high": self.anomaly_threshold_high,
            "anomaly_threshold_medium": self.anomaly_threshold_medium,
            "p1_sample_rate": self.p1_sample_rate,
            "p2_batch_interval_s": self.p2_batch_interval_s,
            "max_buffer_size": self.max_buffer_size,
            "flush_interval_s": self.flush_interval_s,
            "degradation_mode": self.degradation_mode,
            "schema_version": self.schema_version,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SamplingConfig":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class MonitoringMetrics:
    """监控指标聚合."""
    total_spans: int = 0
    sampled_spans: int = 0
    p0_spans: int = 0
    p1_spans: int = 0
    p2_spans: int = 0
    error_spans: int = 0
    fallback_count: int = 0
    avg_anomaly_score: float = 0.0
    avg_duration_ms: float = 0.0
    buffer_usage_pct: float = 0.0
    last_flush_timestamp: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_spans": self.total_spans,
            "sampled_spans": self.sampled_spans,
            "p0_spans": self.p0_spans,
            "p1_spans": self.p1_spans,
            "p2_spans": self.p2_spans,
            "error_spans": self.error_spans,
            "fallback_count": self.fallback_count,
            "avg_anomaly_score": round(self.avg_anomaly_score, 4),
            "avg_duration_ms": round(self.avg_duration_ms, 2),
            "buffer_usage_pct": round(self.buffer_usage_pct, 2),
            "last_flush_timestamp": self.last_flush_timestamp,
        }


@dataclass
class TelemetryRecord:
    """遥测记录 — 用于 CI/CD 门禁校验."""
    trace_id: str
    span_id: str
    event_type: str
    timestamp: str
    sampled: bool
    priority: str
    fields_present: List[str]
    fields_missing: List[str]
    anomaly_score: float
    status: str
    duration_ms: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "trace_id": self.trace_id,
            "span_id": self.span_id,
            "event_type": self.event_type,
            "timestamp": self.timestamp,
            "sampled": self.sampled,
            "priority": self.priority,
            "fields_present": self.fields_present,
            "fields_missing": self.fields_missing,
            "anomaly_score": self.anomaly_score,
            "status": self.status,
            "duration_ms": self.duration_ms,
        }
