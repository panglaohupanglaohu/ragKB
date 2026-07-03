# -*- coding: utf-8 -*-
"""Tests for Channel-Event Bridge."""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path
from unittest.mock import AsyncMock, patch, MagicMock

import pytest

_backend_root = Path(__file__).resolve().parent.parent
if str(_backend_root) not in sys.path:
    sys.path.insert(0, str(_backend_root))

from channels.event_bridge import ChannelEventBridge, get_event_bridge
from agents.domain_events import DomainEvent, EventType


def _make_event(event_type, payload=None):
    return DomainEvent(
        event_id="test-evt-1",
        event_type=event_type,
        schema_version=1,
        payload=payload or {},
        timestamp="2026-06-02T00:00:00Z",
        source="test",
    )


@pytest.fixture
def bridge():
    b = ChannelEventBridge()
    return b


class TestChannelEventBridge:
    def test_initialize(self, bridge):
        with patch("agents.event_bus.get_event_bus") as mock_bus:
            mock_bus.return_value = MagicMock()
            result = bridge.initialize()
            assert result is True
            assert bridge._initialized is True

    def test_get_status(self, bridge):
        status = bridge.get_status()
        assert status["name"] == "event_bridge"
        assert "delivered_count" in status

    def test_on_event_registers_handler(self, bridge):
        handler = AsyncMock()
        bridge.on_event("task.completed", handler)
        assert "task.completed" in bridge._event_handlers
        assert handler in bridge._event_handlers["task.completed"]

    @pytest.mark.asyncio
    async def test_send_agent_message(self, bridge):
        msg = await bridge.send_agent_message(
            from_agent_id="agent-A",
            to_agent_id="agent-B",
            content="Hello from A",
        )
        assert msg["from_agent_id"] == "agent-A"
        assert msg["to_agent_id"] == "agent-B"
        assert msg["content"] == "Hello from A"
        assert bridge._delivered_count == 1

    @pytest.mark.asyncio
    async def test_domain_event_routes_to_handlers(self, bridge):
        received = []

        async def handler(event):
            received.append(event)

        bridge.on_event("task.completed", handler)

        event = _make_event(EventType.TASK_COMPLETED, {"task_id": "t1"})
        await bridge._on_domain_event(event)

        assert len(received) == 1
        assert received[0].payload["task_id"] == "t1"

    @pytest.mark.asyncio
    async def test_wildcard_handler_receives_all(self, bridge):
        received = []

        async def handler(event):
            received.append(event.event_type)

        bridge.on_event("*", handler)

        e1 = _make_event(EventType.TASK_CREATED)
        e2 = _make_event(EventType.TASK_FAILED)
        await bridge._on_domain_event(e1)
        await bridge._on_domain_event(e2)

        assert len(received) == 2

    @pytest.mark.asyncio
    async def test_trigger_task(self, bridge):
        mock_engine = MagicMock()
        mock_engine.submit_task = AsyncMock()

        with patch("channels.event_bridge._task_engine", mock_engine, create=True):
            # This will try to import from agents.api, so let's patch that
            with patch.dict("sys.modules", {"agents.api": MagicMock(_task_engine=mock_engine)}):
                result = await bridge.trigger_task(
                    title="Auto task",
                    agent_id="agent-X",
                    team_id="team-1",
                    triggered_by="test",
                )
                # submit_task was called
                assert mock_engine.submit_task.called

    def test_shutdown(self, bridge):
        assert bridge.shutdown() is True
        assert bridge._running is False
