# -*- coding: utf-8 -*-
"""
智能体广场监控 Channel — 基于 MarineChannel 的全链路可观测实现.

提供:
1. 广场讨论全流程追踪 (创建→进行→总结)
2. 参与者行为监控
3. 异常检测与降级触发
4. SSE 流健康监控
5. 自适应采样集成
"""

from __future__ import annotations

import asyncio
import logging
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

from channels.marine_base import MarineChannel, ChannelPriority, ChannelStatus

from .collector import TraceCollector
from .models import (
    PlazaEventType,
    SamplingConfig,
    TraceContext,
    TraceSpan,
)
from .sampler import AdaptiveSampler

logger = logging.getLogger(__name__)


class PlazaMonitorChannel(MarineChannel):
    """智能体广场监控 Channel — 全链路可观测性.

    继承 MarineChannel 基类，注册到 Channel Registry。
    负责采集广场所有操作的全链路追踪数据。
    """

    # 类属性 (MarineChannel 基类使用)
    name: str = "plaza_monitor"
    description: str = "智能体广场监控 — 全链路可观测性"
    version: str = "1.0.0"
    priority: ChannelPriority = ChannelPriority.P0

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.channel_id = "plaza_monitor"
        self._collector: Optional[TraceCollector] = None
        self._active_discussions: Dict[str, Dict[str, Any]] = {}
        self._degradation_active = False
        self._health_status = {"status": "initializing", "errors": []}

    def initialize(self) -> bool:
        """初始化监控 Channel."""
        try:
            config = SamplingConfig(
                base_sample_rate=0.1,
                high_anomaly_rate=1.0,
                medium_anomaly_rate=0.5,
                anomaly_threshold_high=0.7,
                anomaly_threshold_medium=0.3,
            )
            sampler = AdaptiveSampler(config)
            self._collector = TraceCollector(sampler=sampler, config=config)

            # 启动异步刷新
            loop = asyncio.get_event_loop()
            if loop.is_running():
                loop.create_task(self._collector.start())

            self._health_status = {"status": "ok", "errors": []}
            self._health.status = ChannelStatus.OK
            self._health.message = "Initialized successfully"
            self._initialized = True
            logger.info("✅ PlazaMonitorChannel 初始化完成")
            return True
        except Exception as e:
            self._health_status = {"status": "error", "errors": [str(e)]}
            self._health.status = ChannelStatus.ERROR
            self._health.message = f"Initialization failed: {e}"
            logger.error(f"❌ PlazaMonitorChannel 初始化失败: {e}")
            return False

    def get_status(self) -> Dict[str, Any]:
        """获取 Channel 状态."""
        collector_metrics = {}
        sampler_stats = {}
        if self._collector:
            collector_metrics = self._collector.get_metrics()
            sampler_stats = self._collector.get_sampler_stats()

        return {
            "channel_id": self.channel_id,
            "name": self.name,
            "status": self._health.status.value if hasattr(self._health, 'status') else "unknown",
            "health": self._health_status,
            "degradation_active": self._degradation_active,
            "active_discussions": len(self._active_discussions),
            "collector": collector_metrics,
            "sampler": sampler_stats,
            "config": self._collector.config.to_dict() if self._collector else {},
        }

    def process_event(self, event: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """处理外部事件 — 实现 MarineChannel 抽象方法."""
        event_type = event.get("type", "")
        handler_map = {
            "discussion_created": self._on_discussion_created,
            "discussion_started": self._on_discussion_started,
            "discussion_ended": self._on_discussion_ended,
            "participant_joined": self._on_participant_joined,
            "participant_left": self._on_participant_left,
            "message_sent": self._on_message_sent,
            "fallback_triggered": self._on_fallback_triggered,
            "error_occurred": self._on_error_occurred,
            "llm_call_completed": self._on_llm_call_completed,
            "llm_call_failed": self._on_llm_call_failed,
        }
        handler = handler_map.get(event_type)
        if handler:
            return handler(event)
        logger.debug(f"未处理的事件类型: {event_type}")
        return None

    # ── 事件处理方法 ──────────────────────────────────────

    def _create_trace_span(
        self,
        event_type: str,
        anomaly_score: float = 0.0,
        status: str = "ok",
        duration_ms: float = 0.0,
        **kwargs,
    ) -> TraceSpan:
        """创建 TraceSpan."""
        ctx = TraceContext()
        return TraceSpan(
            trace_id=ctx.trace_id,
            span_id=ctx.span_id,
            event_type=event_type,
            anomaly_score=anomaly_score,
            status=status,
            duration_ms=duration_ms,
            source="plaza_monitor",
            **kwargs,
        )

    async def _record_async(self, span: TraceSpan):
        """异步记录 span."""
        if self._collector:
            await self._collector.record(span)

    def _record_sync(self, span: TraceSpan):
        """同步记录 span（使用 asyncio.create_task 异步执行）."""
        if self._collector:
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    loop.create_task(self._collector.record(span))
            except RuntimeError:
                pass

    def _on_discussion_created(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """讨论创建事件."""
        span = self._create_trace_span(
            event_type=PlazaEventType.DISCUSSION_CREATED.value,
            anomaly_score=0.0,
            status="ok",
            plaza_id=event.get("plaza_id"),
            discussion_id=event.get("discussion_id"),
            tags={"topic": event.get("topic", "")[:50]},
        )
        self._record_sync(span)
        return {"handled": True, "span_id": span.span_id}

    def _on_discussion_started(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """讨论开始事件."""
        disc_id = event.get("discussion_id", "")
        self._active_discussions[disc_id] = {
            "started_at": datetime.now(timezone.utc).isoformat(),
            "topic": event.get("topic", ""),
            "participant_count": event.get("participant_count", 0),
        }
        span = self._create_trace_span(
            event_type=PlazaEventType.DISCUSSION_STARTED.value,
            anomaly_score=0.0,
            status="ok",
            plaza_id=event.get("plaza_id"),
            discussion_id=disc_id,
            tags={
                "topic": event.get("topic", "")[:50],
                "participant_count": str(event.get("participant_count", 0)),
            },
        )
        self._record_sync(span)
        return {"handled": True, "span_id": span.span_id}

    def _on_discussion_ended(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """讨论结束事件."""
        disc_id = event.get("discussion_id", "")
        self._active_discussions.pop(disc_id, None)
        duration_s = event.get("duration_s", 0)
        span = self._create_trace_span(
            event_type=PlazaEventType.DISCUSSION_ENDED.value,
            anomaly_score=0.0,
            status="ok",
            duration_ms=duration_s * 1000,
            plaza_id=event.get("plaza_id"),
            discussion_id=disc_id,
            tags={"message_count": str(event.get("message_count", 0))},
        )
        self._record_sync(span)
        return {"handled": True, "span_id": span.span_id}

    def _on_participant_joined(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """参与者加入事件."""
        span = self._create_trace_span(
            event_type=PlazaEventType.PARTICIPANT_JOINED.value,
            anomaly_score=0.0,
            status="ok",
            plaza_id=event.get("plaza_id"),
            discussion_id=event.get("discussion_id"),
            agent_id=event.get("agent_id"),
            tags={
                "agent_name": event.get("agent_name", ""),
                "seat_tier": event.get("seat_tier", ""),
            },
        )
        self._record_sync(span)
        return {"handled": True, "span_id": span.span_id}

    def _on_participant_left(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """参与者离开事件."""
        span = self._create_trace_span(
            event_type=PlazaEventType.PARTICIPANT_LEFT.value,
            anomaly_score=0.0,
            status="ok",
            plaza_id=event.get("plaza_id"),
            discussion_id=event.get("discussion_id"),
            agent_id=event.get("agent_id"),
        )
        self._record_sync(span)
        return {"handled": True, "span_id": span.span_id}

    def _on_message_sent(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """消息发送事件."""
        anomaly = event.get("anomaly_score", 0.0)
        span = self._create_trace_span(
            event_type=PlazaEventType.MESSAGE_SENT.value,
            anomaly_score=anomaly,
            status="ok" if anomaly < 0.5 else "warning",
            duration_ms=event.get("duration_ms", 0),
            plaza_id=event.get("plaza_id"),
            discussion_id=event.get("discussion_id"),
            agent_id=event.get("agent_id"),
            token_count=event.get("token_count"),
            model_version=event.get("model_version"),
            tags={
                "round": str(event.get("round", 0)),
                "niche_role": event.get("niche_role", ""),
            },
        )
        self._record_sync(span)
        return {"handled": True, "span_id": span.span_id}

    def _on_fallback_triggered(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """降级触发事件 — 强制全量采集."""
        self._degradation_active = True
        span = self._create_trace_span(
            event_type=PlazaEventType.FALLBACK_TRIGGERED.value,
            anomaly_score=0.9,
            status="warning",
            duration_ms=event.get("duration_ms", 0),
            plaza_id=event.get("plaza_id"),
            discussion_id=event.get("discussion_id"),
            error_message=event.get("reason", "fallback_triggered"),
            tags={"fallback_type": event.get("fallback_type", "unknown")},
        )
        self._record_sync(span)
        logger.warning(f"⚠️ 降级触发: {event.get('reason', '')}")
        return {"handled": True, "span_id": span.span_id, "degradation": True}

    def _on_error_occurred(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """错误事件."""
        span = self._create_trace_span(
            event_type=PlazaEventType.ERROR_OCCURRED.value,
            anomaly_score=0.95,
            status="error",
            duration_ms=event.get("duration_ms", 0),
            plaza_id=event.get("plaza_id"),
            discussion_id=event.get("discussion_id"),
            error_message=event.get("error_message", "unknown_error"),
            tags={"error_code": event.get("error_code", "UNKNOWN")},
        )
        self._record_sync(span)
        self._health_status["errors"].append(
            f"{event.get('error_message', '')} @ {datetime.now(timezone.utc).isoformat()}"
        )
        if len(self._health_status["errors"]) > 100:
            self._health_status["errors"] = self._health_status["errors"][-100:]
        return {"handled": True, "span_id": span.span_id}

    def _on_llm_call_completed(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """LLM 调用完成事件."""
        latency = event.get("latency_ms", 0)
        anomaly = 0.0
        if latency > 10000:
            anomaly = 0.6
        elif latency > 5000:
            anomaly = 0.3

        span = self._create_trace_span(
            event_type=PlazaEventType.LLM_CALL_COMPLETED.value,
            anomaly_score=anomaly,
            status="ok" if anomaly < 0.5 else "warning",
            duration_ms=latency,
            model_version=event.get("model"),
            token_count=event.get("token_count"),
            agent_id=event.get("agent_id"),
            session_id=event.get("session_id"),
            tags={"provider": event.get("provider", "unknown")},
        )
        self._record_sync(span)
        return {"handled": True, "span_id": span.span_id}

    def _on_llm_call_failed(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """LLM 调用失败事件."""
        span = self._create_trace_span(
            event_type=PlazaEventType.LLM_CALL_FAILED.value,
            anomaly_score=0.85,
            status="error",
            duration_ms=event.get("latency_ms", 0),
            model_version=event.get("model"),
            agent_id=event.get("agent_id"),
            error_message=event.get("error", "llm_call_failed"),
            tags={"provider": event.get("provider", "unknown")},
        )
        self._record_sync(span)
        return {"handled": True, "span_id": span.span_id}

    # ── 公共 API ──────────────────────────────────────────

    def get_collector(self) -> Optional[TraceCollector]:
        """获取 TraceCollector 实例."""
        return self._collector

    def set_degradation_mode(self, active: bool):
        """设置降级模式."""
        self._degradation_active = active
        if self._collector:
            self._collector.update_config({"degradation_mode": active})
        logger.info(f"{'🔴' if active else '🟢'} 降级模式 {'激活' if active else '关闭'}")

    def get_active_discussions(self) -> Dict[str, Any]:
        """获取活跃讨论列表."""
        return dict(self._active_discussions)

    def get_telemetry(self, limit: int = 100) -> List[Dict[str, Any]]:
        """获取遥测记录."""
        if self._collector:
            return self._collector.get_telemetry_records(limit=limit)
        return []

    def get_metrics(self) -> Dict[str, Any]:
        """获取监控指标."""
        if self._collector:
            return self._collector.get_metrics()
        return {}

    def shutdown(self) -> bool:
        """关闭 Channel，释放资源."""
        try:
            if self._collector:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    loop.create_task(self._collector.stop())
            self._health.status = ChannelStatus.OFF
            self._health.message = "Shutdown"
            self._initialized = False
            logger.info("🛑 PlazaMonitorChannel 已关闭")
            return True
        except Exception as e:
            logger.error(f"❌ PlazaMonitorChannel 关闭失败: {e}")
            return False

    def update_sampling_config(self, config_dict: dict):
        """热更新采样策略."""
        if self._collector:
            self._collector.update_config(config_dict)
            logger.info(f"📋 采样策略已热更新: {config_dict}")
