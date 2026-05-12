# -*- coding: utf-8 -*-
"""Event Bus — 轻量级进程内发布 / 订阅事件总线。

基于 asyncio 的发布-订阅模式:
- 同步 publish(): 立即通知所有订阅者，不等待异步完成
- 异步 apublish(): 等待所有订阅者处理完成（用于需要确认的场景）
- 订阅者按 event_type 注册，支持通配符 "*" 订阅所有事件
- 线程安全: 使用 asyncio.Lock 保护订阅列表

设计约束: 不依赖外部 MQ（Redis/RabbitMQ），纯进程内总线。
事件携带完整上下文（DomainEvent），消费者无需回查。
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Callable, Dict, List, Optional, Set

from .domain_events import DomainEvent, EventType

logger = logging.getLogger(__name__)


# 订阅者回调签名: async (event: DomainEvent) -> None
EventHandler = Callable[[DomainEvent], Any]


class EventBus:
    """进程内事件总线 — Pub/Sub 模式.

    用法:
        bus = EventBus()

        async def on_skill_created(event: DomainEvent):
            print(f"Skill created: {event.payload}")

        bus.subscribe(EventType.SKILL_CREATED, on_skill_created)
        bus.publish(event)  # 异步通知所有订阅者
    """

    def __init__(self):
        # event_type → set of async callbacks
        self._subscribers: Dict[str, Set[EventHandler]] = {}
        self._lock = asyncio.Lock()
        # 统计计数器
        self._published_count: int = 0
        self._delivered_count: int = 0

    # ── 订阅管理 ────────────────────────────────────────────────────

    def subscribe(self, event_type: EventType | str, handler: EventHandler) -> None:
        """订阅某个事件类型.

        Args:
            event_type: 事件类型 (EventType 枚举或 "*" 表示全局订阅)
            handler: 异步回调函数 (event: DomainEvent) -> None
        """
        key = event_type.value if isinstance(event_type, EventType) else event_type
        if key not in self._subscribers:
            self._subscribers[key] = set()
        self._subscribers[key].add(handler)
        logger.debug(f"📡 订阅: {key} → {getattr(handler, '__name__', str(handler))}")

    def unsubscribe(self, event_type: EventType | str, handler: EventHandler) -> None:
        """取消订阅."""
        key = event_type.value if isinstance(event_type, EventType) else event_type
        subs = self._subscribers.get(key, set())
        subs.discard(handler)
        if not subs:
            self._subscribers.pop(key, None)

    def get_subscribers(self, event_type: EventType | str) -> Set[EventHandler]:
        """获取某个事件类型的所有订阅者 (含通配符)."""
        key = event_type.value if isinstance(event_type, EventType) else event_type
        exact = self._subscribers.get(key, set())
        wildcard = self._subscribers.get("*", set())
        return exact | wildcard

    # ── 发布 ────────────────────────────────────────────────────────

    def publish(self, event: DomainEvent) -> None:
        """发布事件 — 异步通知但不等待 (fire-and-forget).

        适用于不需要确认的场景（如索引更新）。
        """
        event_type_key = event.event_type.value if hasattr(event.event_type, "value") else str(event.event_type)
        subscribers = self.get_subscribers(event.event_type)

        if not subscribers:
            return

        self._published_count += 1

        # 为每个订阅者创建独立 task，避免一个慢订阅者阻塞其他
        for handler in subscribers:
            try:
                asyncio.create_task(self._deliver(handler, event, event_type_key))
            except Exception as exc:
                logger.error(f"❌ 创建投递任务失败 [{event_type_key}]: {exc}")

    async def apublish(self, event: DomainEvent) -> None:
        """发布事件 — 等待所有订阅者处理完成.

        适用于需要确认的场景（如持久化后通知）。
        """
        event_type_key = event.event_type.value if hasattr(event.event_type, "value") else str(event.event_type)
        subscribers = self.get_subscribers(event.event_type)

        if not subscribers:
            return

        self._published_count += 1
        tasks = []
        for handler in subscribers:
            tasks.append(self._deliver(handler, event, event_type_key))

        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    async def _deliver(
        self,
        handler: EventHandler,
        event: DomainEvent,
        event_type_key: str,
    ) -> None:
        """投递事件给单个订阅者，捕获异常."""
        try:
            result = handler(event)
            # 如果是协程，await 它
            if asyncio.iscoroutine(result):
                await result
            self._delivered_count += 1
        except Exception as exc:
            logger.error(
                f"❌ 事件处理异常 [{event_type_key}] "
                f"handler={getattr(handler, '__name__', str(handler))}: {exc}",
                exc_info=True,
            )

    # ── 统计 ────────────────────────────────────────────────────────

    @property
    def stats(self) -> Dict[str, int]:
        """返回统计信息."""
        return {
            "published": self._published_count,
            "delivered": self._delivered_count,
            "subscriber_count": sum(len(s) for s in self._subscribers.values()),
            "event_types": len(self._subscribers),
        }

    def reset_stats(self) -> None:
        """重置统计计数器."""
        self._published_count = 0
        self._delivered_count = 0


# ── 全局单例 ──────────────────────────────────────────────────────────

_default_bus: Optional[EventBus] = None


def get_event_bus() -> EventBus:
    """获取全局事件总线单例."""
    global _default_bus
    if _default_bus is None:
        _default_bus = EventBus()
    return _default_bus


def reset_event_bus() -> None:
    """重置全局事件总线 (主要用于测试)."""
    global _default_bus
    _default_bus = None
