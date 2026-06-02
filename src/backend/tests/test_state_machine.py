# -*- coding: utf-8 -*-
"""Tests for unified state machine + timeout watchdog."""

from __future__ import annotations

import asyncio
import sys
import time
from pathlib import Path
from unittest.mock import patch

import pytest

_backend_root = Path(__file__).resolve().parent.parent
if str(_backend_root) not in sys.path:
    sys.path.insert(0, str(_backend_root))

from agents.runtime.state_machine import (
    AGENT_TRANSITIONS,
    TASK_TRANSITIONS,
    SESSION_TRANSITIONS,
    StateMachine,
    TimeoutRule,
    TimeoutWatchdog,
    TransitionError,
    create_agent_state_machine,
    create_task_state_machine,
)


class TestStateMachine:
    """Test core state machine logic."""

    def test_register_and_get(self):
        sm = StateMachine(AGENT_TRANSITIONS, "agent")
        entry = sm.register("a1", "idle")
        assert entry.state == "idle"
        assert sm.get("a1") is entry

    def test_valid_transition(self):
        sm = create_agent_state_machine()
        sm.register("a1", "idle")
        entry = sm.transition("a1", "working")
        assert entry.state == "working"

    def test_invalid_transition_raises(self):
        sm = create_agent_state_machine()
        sm.register("a1", "idle")
        with pytest.raises(TransitionError):
            sm.transition("a1", "error")  # idle → error not allowed

    def test_can_transition(self):
        sm = create_agent_state_machine()
        sm.register("a1", "idle")
        assert sm.can_transition("a1", "working") is True
        assert sm.can_transition("a1", "error") is False

    def test_unregister(self):
        sm = create_agent_state_machine()
        sm.register("a1", "idle")
        sm.unregister("a1")
        assert sm.get("a1") is None

    def test_transition_unknown_entity_raises(self):
        sm = create_agent_state_machine()
        with pytest.raises(KeyError):
            sm.transition("unknown", "working")

    def test_callback_fired_on_transition(self):
        sm = create_agent_state_machine()
        sm.register("a1", "idle")
        received = []
        sm.on_transition(lambda entry, old, new: received.append((old, new)))
        sm.transition("a1", "working")
        assert received == [("idle", "working")]

    def test_task_transitions(self):
        sm = create_task_state_machine()
        sm.register("t1", "pending")
        sm.transition("t1", "running")
        sm.transition("t1", "completed")
        assert sm.get("t1").state == "completed"
        # Completed is terminal
        with pytest.raises(TransitionError):
            sm.transition("t1", "running")

    def test_task_retry_from_failed(self):
        sm = create_task_state_machine()
        sm.register("t1", "pending")
        sm.transition("t1", "running")
        sm.transition("t1", "failed")
        # Can retry: failed → pending
        sm.transition("t1", "pending")
        assert sm.get("t1").state == "pending"

    def test_list_entries(self):
        sm = create_agent_state_machine()
        sm.register("a1", "idle")
        sm.register("a2", "working")
        entries = sm.list_entries()
        assert len(entries) == 2


class TestTimeoutWatchdog:
    """Test watchdog auto-transition."""

    @pytest.mark.asyncio
    async def test_watchdog_triggers_timeout(self):
        sm = create_agent_state_machine()
        entry = sm.register("a1", "working")
        # Backdate entered_at to simulate stuck state
        entry.entered_at = time.time() - 400

        rules = [TimeoutRule(state="working", timeout_seconds=300, target_state="error")]
        wd = TimeoutWatchdog(sm, rules, check_interval=0.05)

        await wd.start()
        await asyncio.sleep(0.15)
        await wd.stop()

        assert sm.get("a1").state == "error"

    @pytest.mark.asyncio
    async def test_watchdog_does_not_trigger_before_timeout(self):
        sm = create_agent_state_machine()
        sm.register("a1", "working")
        # entered_at is now (not timed out)

        rules = [TimeoutRule(state="working", timeout_seconds=300, target_state="error")]
        wd = TimeoutWatchdog(sm, rules, check_interval=0.05)

        await wd.start()
        await asyncio.sleep(0.15)
        await wd.stop()

        assert sm.get("a1").state == "working"

    @pytest.mark.asyncio
    async def test_watchdog_stop(self):
        sm = create_agent_state_machine()
        sm.register("a1", "idle")
        rules = [TimeoutRule(state="idle", timeout_seconds=1, target_state="stopped")]
        wd = TimeoutWatchdog(sm, rules, check_interval=0.05)
        await wd.start()
        await wd.stop()
        assert wd._running is False
