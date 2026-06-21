# -*- coding: utf-8 -*-
"""Cost Target Tracker — 任务完成时复测关联的 Token 优化目标进度 (Phase 9.1).

闭环后半环的关键一接：成本页派发的优化任务带 metadata.target_id，
任务 TASK_COMPLETED 时自动复测该目标 → current 下降 / 达标自动推进 cost_efficiency 棘轮(8R.6)。
"""
from __future__ import annotations

import logging

from .domain_events import DomainEvent, EventType
from .event_bus import get_event_bus

logger = logging.getLogger(__name__)


class CostTargetTracker:
    """订阅 TASK_COMPLETED，对带 target_id 的任务复测成本目标进度。"""

    def __init__(self):
        self._bus = get_event_bus()
        self._subscribed = False

    def start(self) -> None:
        if self._subscribed:
            return
        self._bus.subscribe(EventType.TASK_COMPLETED, self._on_task_completed)
        self._subscribed = True
        logger.info("CostTargetTracker started")

    def stop(self) -> None:
        self._bus.unsubscribe(EventType.TASK_COMPLETED, self._on_task_completed)
        self._subscribed = False

    async def _on_task_completed(self, event: DomainEvent) -> None:
        try:
            payload = event.payload
            metadata = getattr(payload, "metadata", {}) or {}
            tid = metadata.get("target_id")
            if not tid:
                ct = metadata.get("cost_target")
                tid = ct.get("id") if isinstance(ct, dict) else None
            if not tid:
                return
            from .cost_targets import get_target_store
            # get_progress 内部复测 current，并在达标时自动推进 cost_efficiency 棘轮(8R.6)
            prog = get_target_store().get_progress(tid)
            logger.info(
                "🎯 cost target %s 复测：current=%s progress=%s status=%s",
                tid, prog.get("current"), prog.get("progress"), prog.get("status"),
            )
        except Exception as e:
            logger.debug("CostTargetTracker 处理失败(非致命): %s", e)


_tracker = None


def get_cost_target_tracker() -> "CostTargetTracker":
    global _tracker
    if _tracker is None:
        _tracker = CostTargetTracker()
        _tracker.start()
    return _tracker
