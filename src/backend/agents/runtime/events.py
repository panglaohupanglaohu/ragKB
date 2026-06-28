"""Shared runtime event envelope helpers."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Callable, Dict, Optional
from uuid import uuid4

RuntimeEvent = Dict[str, Any]
RuntimeEventCallback = Callable[[str, RuntimeEvent], None]


def make_runtime_event_emitter(
    *,
    loop_kind: str,
    session_id: str = "",
    on_event: Optional[RuntimeEventCallback] = None,
):
    """Return a stable runtime id and an emitter that enriches event payloads."""
    runtime_id = _runtime_id(loop_kind, session_id)
    sequence = 0

    def emit(event_type: str, payload: Optional[RuntimeEvent] = None) -> RuntimeEvent:
        nonlocal sequence
        sequence += 1
        event = _base_event(event_type, runtime_id, loop_kind, sequence, session_id)
        if payload:
            event.update(dict(payload))
        if on_event:
            on_event(event_type, event)
        return event

    return runtime_id, emit


def _runtime_id(loop_kind: str, session_id: str) -> str:
    return session_id or f"{loop_kind}-{uuid4().hex[:12]}"


def _base_event(
    event_type: str,
    runtime_id: str,
    loop_kind: str,
    sequence: int,
    session_id: str,
) -> RuntimeEvent:
    return {
        "type": event_type,
        "runtime_id": runtime_id,
        "loop_kind": loop_kind,
        "sequence": sequence,
        "session_id": session_id,
        "emitted_at": datetime.now(timezone.utc).isoformat(),
    }
