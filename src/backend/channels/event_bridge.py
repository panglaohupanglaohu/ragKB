# -*- coding: utf-8 -*-
"""Channel-Event Bridge — connects EventBus to Marine Channel system.

Makes channels first-class citizens for runtime events:
- Subscribes to EventBus domain events
- Routes events to appropriate channels
- Allows channels to trigger tasks via EventBus

Usage (in main.py startup):
    from channels.event_bridge import ChannelEventBridge
    bridge = ChannelEventBridge()
    bridge.start()
"""

from __future__ import annotations

import asyncio
import inspect
import logging
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional

from .marine_base import MarineChannel, ChannelStatus, ChannelPriority, get_default_registry

logger = logging.getLogger(__name__)


class ChannelEventBridge(MarineChannel):
    """Bridges EventBus domain events to the Channel system.

    Subscribes to agent/task lifecycle events and:
    1. Forwards them to registered channel listeners
    2. Enables channels to trigger new tasks via the bridge
    3. Provides inter-agent messaging through channel routing
    """

    name = "event_bridge"
    description = "事件总线 ↔ Channel 系统桥接"
    version = "1.0.0"
    priority = ChannelPriority.P0

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._event_handlers: Dict[str, List[Callable]] = {}
        self._message_queue: asyncio.Queue = asyncio.Queue()
        self._running = False
        self._worker: Optional[asyncio.Task] = None
        self._delivered_count = 0

    def initialize(self) -> bool:
        """Initialize bridge and subscribe to EventBus."""
        try:
            from agents.event_bus import get_event_bus
            from agents.domain_events import EventType

            bus = get_event_bus()

            # Subscribe to all task and agent events
            for event_type in (
                EventType.TASK_CREATED,
                EventType.TASK_COMPLETED,
                EventType.TASK_FAILED,
                EventType.AGENT_STATE_CHANGED,
            ):
                bus.subscribe(event_type, self._on_domain_event)

            self._initialized = True
            self._health.status = ChannelStatus.OK
            self._health.message = "Event bridge active"
            logger.info("✅ ChannelEventBridge initialized — subscribed to EventBus")
            return True
        except Exception as e:
            logger.error(f"ChannelEventBridge init failed: {e}")
            self._health.status = ChannelStatus.ERROR
            self._health.message = str(e)
            return False

    def get_status(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "status": self._health.status.value,
            "delivered_count": self._delivered_count,
            "queue_size": self._message_queue.qsize(),
            "handlers_registered": {k: len(v) for k, v in self._event_handlers.items()},
        }

    def shutdown(self) -> bool:
        self._running = False
        if self._worker:
            self._worker.cancel()
        return True

    # ── Public API ────────────────────────────────────────────────────

    def on_event(self, event_type: str, handler: Callable) -> None:
        """Register a channel-side handler for a domain event type.

        Channels call this to receive routed events.
        """
        if event_type not in self._event_handlers:
            self._event_handlers[event_type] = []
        self._event_handlers[event_type].append(handler)

    async def send_agent_message(
        self,
        from_agent_id: str,
        to_agent_id: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Send a message from one agent to another via the channel system.

        This enables inter-agent communication through channels.
        """
        msg = {
            "type": "agent_message",
            "from_agent_id": from_agent_id,
            "to_agent_id": to_agent_id,
            "content": content,
            "metadata": metadata or {},
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        await self._message_queue.put(msg)
        self._delivered_count += 1
        logger.debug(f"Agent message queued: {from_agent_id} → {to_agent_id}")
        return msg

    async def trigger_task(
        self,
        title: str,
        agent_id: str,
        team_id: str = "",
        description: str = "",
        triggered_by: str = "",
    ) -> Optional[Dict[str, Any]]:
        """Trigger a new task through the channel system.

        This is how channels create tasks autonomously.
        """
        try:
            from agents.task_engine import AgentTask, TaskEngine
            from agents.api import _task_engine

            if _task_engine is None:
                logger.warning("TaskEngine not available — cannot trigger task")
                return None

            task = AgentTask(
                agent_id=agent_id,
                team_id=team_id,
                title=title,
                description=description,
                metadata={"triggered_by": triggered_by or self.name},
            )
            await _task_engine.submit_task(task)
            logger.info(f"Channel-triggered task: {title} → {agent_id}")
            return task.to_dict()
        except Exception as e:
            logger.error(f"Failed to trigger task: {e}")
            return None

    # ── Internal ──────────────────────────────────────────────────────

    async def _on_domain_event(self, event) -> None:
        """Handle incoming domain events from EventBus."""
        event_type = event.event_type.value if hasattr(event.event_type, "value") else str(event.event_type)

        # Route to registered channel handlers
        handlers = self._event_handlers.get(event_type, [])
        handlers.extend(self._event_handlers.get("*", []))

        for handler in handlers:
            try:
                if inspect.iscoroutinefunction(handler):
                    await handler(event)
                else:
                    handler(event)
                self._delivered_count += 1
            except Exception as e:
                logger.error(f"Channel event handler error [{event_type}]: {e}")

    async def start_worker(self) -> None:
        """Start background worker for processing inter-agent messages."""
        if self._running:
            return
        self._running = True
        self._worker = asyncio.create_task(self._process_messages())

    async def _process_messages(self) -> None:
        """Process queued inter-agent messages."""
        while self._running:
            try:
                msg = await asyncio.wait_for(self._message_queue.get(), timeout=1.0)
                # Route message to target agent's handler (if registered)
                to_agent = msg.get("to_agent_id", "")
                handlers = self._event_handlers.get(f"agent.{to_agent}", [])
                for handler in handlers:
                    try:
                        if inspect.iscoroutinefunction(handler):
                            await handler(msg)
                        else:
                            handler(msg)
                    except Exception as e:
                        logger.error(f"Message delivery error → {to_agent}: {e}")
            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Message worker error: {e}")


# Convenience accessor
_bridge_instance: Optional[ChannelEventBridge] = None


def get_event_bridge() -> ChannelEventBridge:
    """Get or create the global ChannelEventBridge instance."""
    global _bridge_instance
    if _bridge_instance is None:
        _bridge_instance = ChannelEventBridge()
    return _bridge_instance
