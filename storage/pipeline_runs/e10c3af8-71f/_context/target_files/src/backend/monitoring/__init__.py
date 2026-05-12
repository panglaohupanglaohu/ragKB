# -*- coding: utf-8 -*-
"""
智能体广场实时监控与自动化质量保障系统 — 监控模块

基于统一 traceId 的全链路可观测体系，支持：
- W3C Trace Context 标准
- P0/P1/P2 三级埋点字段分层采集
- 自适应采样（基于 anomalyScore 动态调整）
- 本地缓冲与异步上报
- 降级场景全量采集
- ConfigMap 热更新采样策略
- 指纹遥测旁路 (非侵入式行为指纹异步采集)
- 聚合链路 Trace ID 关联 (跨 Plaza/Handoff/Task 全链路追踪)
- 面板监控 API (前端实时指标看板)
"""

from __future__ import annotations

from .models import (
    TraceSpan,
    TraceContext,
    SpanPriority,
    SamplingDecision,
    SamplingConfig,
    MonitoringMetrics,
    PlazaEventType,
    TelemetryRecord,
)
from .sampler import AdaptiveSampler
from .collector import TraceCollector
from .plaza_monitor import PlazaMonitorChannel
from .fingerprint_bypass import (
    FingerprintTelemetryChannel,
    BehaviorFingerprint,
    FingerprintBuffer,
    get_fingerprint_channel,
)
from .trace_bridge import (
    TraceBridge,
    TraceBridgeChannel,
    TraceLink,
    TraceTopologyNode,
    get_trace_bridge,
    get_trace_bridge_channel,
    generate_trace_id,
    generate_span_id,
    make_trace_context,
)
from .monitoring_routes import router as monitoring_router

__all__ = [
    "TraceSpan",
    "TraceContext",
    "SpanPriority",
    "SamplingDecision",
    "SamplingConfig",
    "MonitoringMetrics",
    "PlazaEventType",
    "TelemetryRecord",
    "AdaptiveSampler",
    "TraceCollector",
    "PlazaMonitorChannel",
    # Fingerprint Telemetry Bypass
    "FingerprintTelemetryChannel",
    "BehaviorFingerprint",
    "FingerprintBuffer",
    "get_fingerprint_channel",
    # Trace Bridge
    "TraceBridge",
    "TraceBridgeChannel",
    "TraceLink",
    "TraceTopologyNode",
    "get_trace_bridge",
    "get_trace_bridge_channel",
    "generate_trace_id",
    "generate_span_id",
    "make_trace_context",
    # Monitoring Routes
    "monitoring_router",
]
