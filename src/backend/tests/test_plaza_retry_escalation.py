# -*- coding: utf-8 -*-
"""Tests for Plaza retry + failure escalation."""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

_backend_root = Path(__file__).resolve().parent.parent
if str(_backend_root) not in sys.path:
    sys.path.insert(0, str(_backend_root))

from agents.plaza import Participant, SeatTier, NicheRole
from agents.plaza_engine import PlazaEngine, _MAX_RETRIES, _RETRY_BACKOFF_BASE
from agents import plaza_routes


@pytest.fixture
def engine():
    with patch("agents.plaza_engine.PlazaStore") as mock_store:
        mock_store.return_value.load_all.return_value = {}
        e = PlazaEngine()
    return e


@pytest.fixture
def participant():
    return Participant(
        agent_id="test-agent",
        agent_name="Test Agent",
        role="developer",
        team_id="test-team",
        seat_tier=SeatTier.INNER,
        niche_role=NicheRole.ANALYST,
        niche_index=0,
    )


class TestRetryAndEscalation:
    """Test LLM call retry logic and failure escalation."""

    @pytest.mark.asyncio
    async def test_successful_call_no_retry(self, engine, participant):
        async def good_chat(*args, **kwargs):
            return SimpleNamespace(response="Hello from agent")

        engine._chat_fn = good_chat

        content = await engine._generate_agent_content(participant, "say hello")
        assert content == "Hello from agent"
        assert len(engine._escalation_queue) == 0

    @pytest.mark.asyncio
    async def test_retry_on_failure_then_success(self, engine, participant, monkeypatch):
        # Patch sleep to avoid real delays
        monkeypatch.setattr(asyncio, "sleep", AsyncMock())

        call_count = [0]

        async def flaky_chat(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] < 3:
                raise Exception("LLM timeout")
            return SimpleNamespace(response="Recovered!")

        engine._chat_fn = flaky_chat

        content = await engine._generate_agent_content(participant, "test")
        assert content == "Recovered!"
        assert call_count[0] == 3
        assert len(engine._escalation_queue) == 0

    @pytest.mark.asyncio
    async def test_all_retries_exhausted_escalates(self, engine, participant, monkeypatch):
        monkeypatch.setattr(asyncio, "sleep", AsyncMock())

        async def always_fail(*args, **kwargs):
            raise Exception("permanent failure")

        engine._chat_fn = always_fail

        content = await engine._generate_agent_content(
            participant,
            "test prompt",
            plaza_id="plaza-1",
            discussion_id="disc-1",
            discussion_topic="讨论主题",
            round_number=2,
        )
        assert "暂时离线" in content
        assert len(engine._escalation_queue) == 1
        entry = engine._escalation_queue[0]
        assert entry["agent_id"] == "test-agent"
        assert entry["status"] == "pending"
        assert "permanent failure" in entry["error"]
        assert entry["plaza_id"] == "plaza-1"
        assert entry["discussion_id"] == "disc-1"
        assert entry["discussion_topic"] == "讨论主题"
        assert entry["round_number"] == 2

    def test_resolve_escalation(self, engine):
        engine._escalation_queue.append({
            "agent_id": "a1",
            "status": "pending",
            "error": "test",
            "timestamp": "2026-06-01T00:00:00Z",
        })
        assert engine.resolve_escalation(0) is True
        assert engine._escalation_queue[0]["status"] == "resolved"
        assert "resolved_at" in engine._escalation_queue[0]

    def test_resolve_escalation_invalid_index(self, engine):
        assert engine.resolve_escalation(99) is False

    def test_get_escalation_queue_empty(self, engine):
        assert engine.get_escalation_queue() == []

    @pytest.mark.asyncio
    async def test_retry_respects_max_retries_constant(self, engine, participant, monkeypatch):
        monkeypatch.setattr(asyncio, "sleep", AsyncMock())
        call_count = [0]

        async def counting_fail(*args, **kwargs):
            call_count[0] += 1
            raise Exception("fail")

        engine._chat_fn = counting_fail

        await engine._generate_agent_content(participant, "test")
        assert call_count[0] == _MAX_RETRIES

    @pytest.mark.asyncio
    async def test_escalation_route_filters_by_discussion_and_includes_index(self, engine, monkeypatch):
        engine._escalation_queue.extend([
            {
                "agent_id": "a-1",
                "agent_name": "Agent 1",
                "status": "pending",
                "error": "boom",
                "timestamp": "2026-06-02T00:00:00Z",
                "plaza_id": "plaza-a",
                "discussion_id": "disc-a",
                "discussion_topic": "Topic A",
                "round_number": 2,
            },
            {
                "agent_id": "a-2",
                "agent_name": "Agent 2",
                "status": "resolved",
                "error": "done",
                "timestamp": "2026-06-02T00:00:01Z",
                "plaza_id": "plaza-a",
                "discussion_id": "disc-a",
                "discussion_topic": "Topic A",
                "round_number": 3,
            },
            {
                "agent_id": "b-1",
                "agent_name": "Agent 3",
                "status": "pending",
                "error": "elsewhere",
                "timestamp": "2026-06-02T00:00:02Z",
                "plaza_id": "plaza-b",
                "discussion_id": "disc-b",
                "discussion_topic": "Topic B",
                "round_number": 1,
            },
        ])
        monkeypatch.setattr(plaza_routes, "get_plaza_engine", lambda: engine)

        payload = await plaza_routes.get_escalation_queue(
            plaza_id="plaza-a",
            discussion_id="disc-a",
            entry_status="pending",
        )

        assert payload["total"] == 1
        assert payload["pending_count"] == 1
        assert payload["items"][0]["index"] == 0
        assert payload["items"][0]["discussion_id"] == "disc-a"
