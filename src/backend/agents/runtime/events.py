"""Shared runtime event envelope helpers."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Callable, Dict, Optional
from uuid import uuid4


def make_runtime_event_emitter(
    *,
    loop_kind: str,
    session_id: str = "",
    on_event: Optional[Callable[[str, Dict[str, Any]], None]] = None,
):
    """Return a stable runtime id and an emitter that enriches event payloads."""
    runtime_id = session_id or f"{loop_kind}-{uuid4().hex[:12]}"
    sequence = 0

    def emit(event_type: str, payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        nonlocal sequence
        sequence += 1
        event = {
            "type": event_type,
            "runtime_id": runtime_id,
            "loop_kind": loop_kind,
            "sequence": sequence,
            "session_id": session_id,
            "emitted_at": datetime.now(timezone.utc).isoformat(),
        }
        if payload:
            event.update(dict(payload))
        if on_event:
            on_event(event_type, event)
        return event

    return runtime_id, emit
