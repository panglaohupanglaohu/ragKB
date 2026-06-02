# -*- coding: utf-8 -*-
"""Unified State Machine + Watchdog for Agent / Task / Session states.

Provides:
- StateMachine: Generic finite-state machine with valid transition enforcement
- TimeoutWatchdog: Background asyncio task that auto-transitions stale entities
"""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

logger = logging.getLogger("state_machine")


# ── Valid Transition Maps ────────────────────────────────────────────────────

# AgentState transitions (from agents/models.py)
AGENT_TRANSITIONS: Dict[str, Set[str]] = {
    "idle": {"working", "paused", "stopped"},
    "working": {"idle", "paused", "error", "stopped"},
    "paused": {"idle", "working", "stopped"},
    "error": {"idle", "stopped"},
    "stopped": {"idle"},
}

# TaskStatus transitions (from task_engine.py)
TASK_TRANSITIONS: Dict[str, Set[str]] = {
    "pending": {"running", "cancelled"},
    "running": {"completed", "failed", "cancelled"},
    "completed": set(),  # terminal
    "failed": {"pending"},  # allow retry
    "cancelled": set(),  # terminal
}

# Session state transitions (for future runtime sessions)
SESSION_TRANSITIONS: Dict[str, Set[str]] = {
    "created": {"active", "expired"},
    "active": {"idle", "expired", "closed"},
    "idle": {"active", "expired", "closed"},
    "expired": {"closed"},
    "closed": set(),  # terminal
}


class TransitionError(Exception):
    """Raised when an invalid state transition is attempted."""


@dataclass
class StateEntry:
    """Tracks current state + timing for a single entity."""

    entity_id: str
    entity_type: str  # "agent" | "task" | "session"
    state: str
    entered_at: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)


TransitionCallback = Callable[[StateEntry, str, str], None]


class StateMachine:
    """Generic state machine enforcing valid transitions.

    Parameters
    ----------
    transitions : dict mapping state → set of valid next states
    entity_type : label for logging/events ("agent", "task", "session")
    """

    def __init__(
        self,
        transitions: Dict[str, Set[str]],
        entity_type: str = "entity",
    ) -> None:
        self._transitions = transitions
        self._entity_type = entity_type
        self._entries: Dict[str, StateEntry] = {}
        self._callbacks: List[TransitionCallback] = []

    def register(self, entity_id: str, initial_state: str, **metadata: Any) -> StateEntry:
        """Register an entity with its initial state."""
        entry = StateEntry(
            entity_id=entity_id,
            entity_type=self._entity_type,
            state=initial_state,
            metadata=metadata,
        )
        self._entries[entity_id] = entry
        return entry

    def unregister(self, entity_id: str) -> None:
        """Remove an entity from tracking."""
        self._entries.pop(entity_id, None)

    def get(self, entity_id: str) -> Optional[StateEntry]:
        return self._entries.get(entity_id)

    def transition(self, entity_id: str, new_state: str) -> StateEntry:
        """Transition entity to new_state. Raises TransitionError if invalid."""
        entry = self._entries.get(entity_id)
        if entry is None:
            raise KeyError(f"{self._entity_type} '{entity_id}' not registered")

        valid_next = self._transitions.get(entry.state, set())
        if new_state not in valid_next:
            raise TransitionError(
                f"{self._entity_type} '{entity_id}': "
                f"cannot transition {entry.state} → {new_state} "
                f"(valid: {valid_next})"
            )

        old_state = entry.state
        entry.state = new_state
        entry.entered_at = time.time()
        logger.debug(
            "%s %s: %s → %s", self._entity_type, entity_id, old_state, new_state
        )
        self._fire_callbacks(entry, old_state, new_state)
        return entry

    def can_transition(self, entity_id: str, new_state: str) -> bool:
        """Check if transition is valid without performing it."""
        entry = self._entries.get(entity_id)
        if entry is None:
            return False
        return new_state in self._transitions.get(entry.state, set())

    def on_transition(self, callback: TransitionCallback) -> None:
        """Register a callback for state transitions."""
        self._callbacks.append(callback)

    def list_entries(self) -> List[StateEntry]:
        return list(self._entries.values())

    def _fire_callbacks(self, entry: StateEntry, old: str, new: str) -> None:
        for cb in self._callbacks:
            try:
                cb(entry, old, new)
            except Exception as e:
                logger.warning("State callback error: %s", e)


# ── Timeout Watchdog ─────────────────────────────────────────────────────────


@dataclass
class TimeoutRule:
    """A rule that auto-transitions entities stuck in a state too long."""

    state: str
    timeout_seconds: float
    target_state: str


class TimeoutWatchdog:
    """Background task that checks for stale states and auto-transitions them.

    Parameters
    ----------
    machine : StateMachine to monitor
    rules : list of TimeoutRules defining which states have timeouts
    check_interval : seconds between watchdog checks (default 10)
    """

    def __init__(
        self,
        machine: StateMachine,
        rules: List[TimeoutRule],
        check_interval: float = 10.0,
    ) -> None:
        self._machine = machine
        self._rules = rules
        self._check_interval = check_interval
        self._task: Optional[asyncio.Task] = None
        self._running = False

    async def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._loop())
        logger.info(
            "Watchdog started for %s (%d rules, interval=%ss)",
            self._machine._entity_type,
            len(self._rules),
            self._check_interval,
        )

    async def stop(self) -> None:
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None

    async def _loop(self) -> None:
        while self._running:
            try:
                await asyncio.sleep(self._check_interval)
                self._check_timeouts()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Watchdog error: %s", e)

    def _check_timeouts(self) -> None:
        now = time.time()
        for entry in self._machine.list_entries():
            for rule in self._rules:
                if entry.state == rule.state:
                    elapsed = now - entry.entered_at
                    if elapsed > rule.timeout_seconds:
                        logger.warning(
                            "Watchdog: %s '%s' stuck in '%s' for %.1fs (limit: %ss) → '%s'",
                            entry.entity_type,
                            entry.entity_id,
                            entry.state,
                            elapsed,
                            rule.timeout_seconds,
                            rule.target_state,
                        )
                        try:
                            self._machine.transition(entry.entity_id, rule.target_state)
                        except (TransitionError, KeyError) as e:
                            logger.error("Watchdog transition failed: %s", e)
                    break  # only first matching rule per entry


# ── Convenience Factories ────────────────────────────────────────────────────


def create_agent_state_machine() -> StateMachine:
    """Create a StateMachine for agent lifecycle."""
    return StateMachine(AGENT_TRANSITIONS, entity_type="agent")


def create_task_state_machine() -> StateMachine:
    """Create a StateMachine for task lifecycle."""
    return StateMachine(TASK_TRANSITIONS, entity_type="task")


def create_session_state_machine() -> StateMachine:
    """Create a StateMachine for session lifecycle."""
    return StateMachine(SESSION_TRANSITIONS, entity_type="session")


# Default timeout rules
DEFAULT_AGENT_TIMEOUT_RULES = [
    TimeoutRule(state="working", timeout_seconds=300, target_state="error"),
]

DEFAULT_TASK_TIMEOUT_RULES = [
    TimeoutRule(state="running", timeout_seconds=600, target_state="failed"),
]

DEFAULT_SESSION_TIMEOUT_RULES = [
    TimeoutRule(state="idle", timeout_seconds=1800, target_state="expired"),
]
