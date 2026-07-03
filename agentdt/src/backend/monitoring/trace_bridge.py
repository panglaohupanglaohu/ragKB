# -*- coding: utf-8 -*-
"""
聚合链路 Trace ID 关联桥接器 — 统一 TraceContext 注入与传播.

核心职责:
1. 为多 Agent 协作 (Plaza 讨论、Handoff、Team 调度) 统一注入 Trace ID
2. 实现因果链: Team → Discussion → Round → Agent Turn → Tool Call
3. 提供轻量级 TraceContext 创建/传播 API
4. 与 FingerprintTelemetryChannel 联动，关联行为指纹

遵循 W3C Trace Context 标准:
- traceparent: 00-{trace_id}-{span_id}-{trace_flags}
- tracestate: 自定义键值对
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from contextvars import ContextVar
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional

from channels.marine_base import (
    ChannelPriority,
    ChannelStatus,
    ChannelEvent,
    MarineChannel,
)

from .models import (
    MonitoringMetrics,
    SpanPriority,
    TraceContext,
    TraceSpan,
)

logger = logging.getLogger(__name__)

# 异步上下文变量 — 跨协程传播当前 trace ID
_current_trace_id: ContextVar[Optional[str]] = ContextVar("trace_id", default=None)
_current_span_id: ContextVar[Optional[str]] = ContextVar("span_id", default=None)


# ── Trace Link 数据模型 ──────────────────────────────────────────────────


@dataclass
class TraceLink:
    """Trace 链路节点 — 描述一次协作事件在因果链中的位置."""

    link_id: str = ""
    trace_id: str = ""
    span_id: str = ""
    parent_span_id: str = ""
    link_type: str = ""  # plaza_discussion, handoff, team_schedule, agent_turn, tool_call
    source_agent_id: str = ""
    target_agent_id: str = ""
    source_team_id: str = ""
    target_team_id: str = ""
    discussion_id: str = ""
    task_id: str = ""
    round_number: int = 0
    iteration: int = 0
    tool_name: str = ""
    latency_ms: float = 0.0
    success: bool = True
    error_message: str = ""
    tags: Dict[str, str] = field(default_factory=dict)
    created_at: str = ""

    def __post_init__(self) -> None:
        if not self.link_id:
            self.link_id = str(uuid.uuid4())[:8]
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "link_id": self.link_id,
            "trace_id": self.trace_id,
            "span_id": self.span_id,
            "parent_span_id": self.parent_span_id,
            "link_type": self.link_type,
            "source_agent_id": self.source_agent_id,
            "target_agent_id": self.target_agent_id,
            "source_team_id": self.source_team_id,
            "target_team_id": self.target_team_id,
            "discussion_id": self.discussion_id,
            "task_id": self.task_id,
            "round_number": self.round_number,
            "iteration": self.iteration,
            "tool_name": self.tool_name,
            "latency_ms": self.latency_ms,
            "success": self.success,
            "error_message": self.error_message,
            "tags": self.tags,
            "created_at": self.created_at,
        }


@dataclass
class TraceTopologyNode:
    """Trace 拓扑节点 — 用于前端面板展示."""

    node_id: str
    node_type: str  # team, agent, discussion, task, tool
    label: str
    trace_id: str
    parent_ids: List[str] = field(default_factory=list)
    child_ids: List[str] = field(default_factory=list)
    metrics: Dict[str, float] = field(default_factory=dict)
    status: str = "ok"  # ok, warn, error

    def to_dict(self) -> Dict[str, Any]:
        return {
            "node_id": self.node_id,
            "node_type": self.node_type,
            "label": self.label,
            "trace_id": self.trace_id,
            "parent_ids": self.parent_ids,
            "child_ids": self.child_ids,
            "metrics": self.metrics,
            "status": self.status,
        }


# ── Trace Bridge — 核心桥接器 ────────────────────────────────────────────


class TraceBridge:
    """Trace ID 桥接器 — 创建和传播 TraceContext.

    用法 (上下文管理器风格):
        bridge = TraceBridge()
        with bridge.span("plaza_discussion", discussion_id="...") as ctx:
            # 内部自动设置 trace_id / span_id
            ...
    """

    def __init__(self):
        self._links: List[TraceLink] = []
        self._topology_nodes: Dict[str, TraceTopologyNode] = {}
        self._max_links: int = 5000
        self._lock: asyncio.Lock = asyncio.Lock()

    # ── Trace ID 创建与传播 ──────────────────────────────────────────

    def new_trace(self, source: str = "") -> TraceContext:
        """创建一条新的 Trace (根 span)."""
        trace_id = uuid.uuid4().hex[:32]
        span_id = uuid.uuid4().hex[:16]
        ctx = TraceContext(
            trace_id=trace_id,
            parent_span_id="",
            span_id=span_id,
            trace_flags=1,
        )
        _current_trace_id.set(trace_id)
        _current_span_id.set(span_id)
        logger.debug(f"🔗 New trace: {trace_id[:8]}... source={source}")
        return ctx

    def child_span(self, parent_ctx: TraceContext, span_name: str = "") -> TraceContext:
        """从父 span 创建子 span."""
        span_id = uuid.uuid4().hex[:16]
        ctx = TraceContext(
            trace_id=parent_ctx.trace_id,
            parent_span_id=parent_ctx.span_id,
            span_id=span_id,
            trace_flags=parent_ctx.trace_flags,
        )
        _current_span_id.set(span_id)
        logger.debug(f"🔗 Child span: {span_id[:8]}... ← {parent_ctx.span_id[:8]}... [{span_name}]")
        return ctx

    def current_trace_id(self) -> Optional[str]:
        """获取当前上下文中的 trace_id."""
        return _current_trace_id.get()

    def current_span_id(self) -> Optional[str]:
        """获取当前上下文中的 span_id."""
        return _current_span_id.get()

    # ── Trace Link 记录 ───────────────────────────────────────────────

    async def record_link(self, link: TraceLink) -> None:
        """记录一次协作事件到因果链."""
        async with self._lock:
            self._links.append(link)
            if len(self._links) > self._max_links:
                self._links = self._links[-self._max_links:]

            # 更新拓扑节点
            await self._update_topology(link)

    async def _update_topology(self, link: TraceLink) -> None:
        """根据 TraceLink 更新拓扑图."""
        # 添加/更新源节点
        if link.source_agent_id:
            src_key = f"agent:{link.source_agent_id}"
            src_node = self._topology_nodes.get(src_key)
            if not src_node:
                src_node = TraceTopologyNode(
                    node_id=src_key,
                    node_type="agent",
                    label=link.source_agent_id,
                    trace_id=link.trace_id,
                )
                self._topology_nodes[src_key] = src_node
            if link.target_agent_id:
                tgt_key = f"agent:{link.target_agent_id}"
                if tgt_key not in src_node.child_ids:
                    src_node.child_ids.append(tgt_key)

        # 添加/更新目标节点
        if link.target_agent_id:
            tgt_key = f"agent:{link.target_agent_id}"
            tgt_node = self._topology_nodes.get(tgt_key)
            if not tgt_node:
                tgt_node = TraceTopologyNode(
                    node_id=tgt_key,
                    node_type="agent",
                    label=link.target_agent_id,
                    trace_id=link.trace_id,
                )
                self._topology_nodes[tgt_key] = tgt_node
            if link.source_agent_id:
                src_key = f"agent:{link.source_agent_id}"
                if src_key not in tgt_node.parent_ids:
                    tgt_node.parent_ids.append(src_key)

        # 讨论节点
        if link.discussion_id:
            disc_key = f"discussion:{link.discussion_id}"
            disc_node = self._topology_nodes.get(disc_key)
            if not disc_node:
                disc_node = TraceTopologyNode(
                    node_id=disc_key,
                    node_type="discussion",
                    label=f"Discussion {link.discussion_id[:8]}",
                    trace_id=link.trace_id,
                )
                self._topology_nodes[disc_key] = disc_node

    # ── 查询接口 (供前端面板) ─────────────────────────────────────────

    async def get_recent_links(self, limit: int = 50) -> List[Dict[str, Any]]:
        """获取最近的 TraceLink 记录."""
        async with self._lock:
            return [l.to_dict() for l in self._links[-limit:]]

    async def get_topology(self) -> Dict[str, Any]:
        """获取当前 Trace 拓扑图."""
        async with self._lock:
            nodes = [n.to_dict() for n in self._topology_nodes.values()]
            links = []
            for node in self._topology_nodes.values():
                for child_id in node.child_ids:
                    links.append({
                        "source": node.node_id,
                        "target": child_id,
                    })
            return {
                "nodes": nodes,
                "links": links,
                "total_traces": len(set(n.trace_id for n in self._topology_nodes.values())),
            }

    async def get_trace_chain(self, trace_id: str) -> List[Dict[str, Any]]:
        """获取某条 Trace 的完整链路."""
        async with self._lock:
            chain = [l.to_dict() for l in self._links if l.trace_id == trace_id]
            chain.sort(key=lambda x: x["created_at"])
            return chain

    async def get_stats(self) -> Dict[str, Any]:
        """获取桥接器统计信息."""
        async with self._lock:
            return {
                "total_links": len(self._links),
                "total_traces": len(set(l.trace_id for l in self._links)),
                "total_nodes": len(self._topology_nodes),
                "link_types": self._count_link_types(),
            }

    def _count_link_types(self) -> Dict[str, int]:
        counts: Dict[str, int] = {}
        for l in self._links:
            counts[l.link_type] = counts.get(l.link_type, 0) + 1
        return counts


# ── Trace Bridge Channel (MarineChannel) ──────────────────────────────────


class TraceBridgeChannel(MarineChannel):
    """聚合链路 Trace ID 关联 Channel.

    监听主业务事件，自动创建 TraceLink 并更新拓扑。
    """

    channel_name: str = "trace_bridge"
    priority: ChannelPriority = ChannelPriority.P0

    def __init__(self):
        super().__init__(name=self.channel_name, priority=self.priority)
        self._bridge = TraceBridge()

    # ── MarineChannel 接口 ──────────────────────────────────────────────

    def initialize(self) -> None:
        self.status = ChannelStatus.OK
        logger.info("🔗 TraceBridgeChannel initialized — tracing all collaboration links")

    async def process_event(self, event: ChannelEvent) -> bool:
        """处理协作事件，自动创建 TraceLink.

        事件类型:
        - plaza_discussion_start: 广场讨论开始
        - plaza_discussion_turn: 广场讨论轮次
        - handoff_executed: Agent 交接已执行
        - task_dispatched: 任务已派发
        - agent_turn: Agent 单轮执行
        - tool_call: 工具调用
        - ewma_breach: EWMA 阈值突破 (关联指纹)
        """
        try:
            data = event.data or {}
            trace_id = data.get("trace_id", _current_trace_id.get() or uuid.uuid4().hex[:32])
            parent_span_id = data.get("parent_span_id", "")
            span_id = data.get("span_id", uuid.uuid4().hex[:16])

            link = TraceLink(
                trace_id=trace_id,
                span_id=span_id,
                parent_span_id=parent_span_id,
                link_type=event.event_type,
                source_agent_id=data.get("source_agent_id", data.get("agent_id", "")),
                target_agent_id=data.get("target_agent_id", ""),
                source_team_id=data.get("source_team_id", data.get("team_id", "")),
                target_team_id=data.get("target_team_id", ""),
                discussion_id=data.get("discussion_id", ""),
                task_id=data.get("task_id", ""),
                round_number=data.get("round_number", 0),
                iteration=data.get("iteration", 0),
                tool_name=data.get("tool_name", ""),
                latency_ms=data.get("latency_ms", 0.0),
                success=data.get("success", True),
                error_message=data.get("error_message", ""),
                tags=data.get("tags", {}),
            )
            await self._bridge.record_link(link)
            return True
        except Exception as e:
            logger.error(f"TraceBridgeChannel process_event error: {e}", exc_info=True)
            return False

    def get_status(self) -> Dict[str, Any]:
        return {
            "channel": self.channel_name,
            "status": self.status.value,
            "priority": self.priority.value,
        }

    async def shutdown(self) -> None:
        self.status = ChannelStatus.OFF
        logger.info("TraceBridgeChannel shutdown complete")

    # ── 查询接口 ───────────────────────────────────────────────────────

    @property
    def bridge(self) -> TraceBridge:
        return self._bridge

    async def get_recent_links(self, limit: int = 50) -> List[Dict[str, Any]]:
        return await self._bridge.get_recent_links(limit)

    async def get_topology(self) -> Dict[str, Any]:
        return await self._bridge.get_topology()

    async def get_trace_chain(self, trace_id: str) -> List[Dict[str, Any]]:
        return await self._bridge.get_trace_chain(trace_id)

    async def get_stats(self) -> Dict[str, Any]:
        return await self._bridge.get_stats()


# ── 工具函数 ─────────────────────────────────────────────────────────────


def generate_trace_id() -> str:
    """生成新的 trace ID (32 位 hex)."""
    return uuid.uuid4().hex[:32]


def generate_span_id() -> str:
    """生成新的 span ID (16 位 hex)."""
    return uuid.uuid4().hex[:16]


def make_trace_context(trace_id: str = "", parent_span_id: str = "") -> TraceContext:
    """便捷创建 TraceContext."""
    return TraceContext(
        trace_id=trace_id or generate_trace_id(),
        parent_span_id=parent_span_id,
        span_id=generate_span_id(),
        trace_flags=1,
    )


# ── 全局单例 ───────────────────────────────────────────────────────────

_trace_bridge_channel: Optional[TraceBridgeChannel] = None


def get_trace_bridge_channel() -> TraceBridgeChannel:
    """获取全局 TraceBridgeChannel 单例."""
    global _trace_bridge_channel
    if _trace_bridge_channel is None:
        _trace_bridge_channel = TraceBridgeChannel()
    return _trace_bridge_channel


def get_trace_bridge() -> TraceBridge:
    """获取全局 TraceBridge 实例."""
    return get_trace_bridge_channel().bridge
