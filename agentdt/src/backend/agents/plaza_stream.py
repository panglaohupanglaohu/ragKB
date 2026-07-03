# -*- coding: utf-8 -*-
"""Helpers for Plaza discussion Server-Sent Events streams."""

from __future__ import annotations

import json
from typing import Any, Dict


def format_sse_event(payload: Dict[str, Any], event_id: str = "") -> str:
    id_line = f"id: {event_id}\n" if event_id else ""
    return f"{id_line}data: {json.dumps(payload, ensure_ascii=False)}\n\n"


def parse_last_event_id(last_event_id: str) -> int:
    return int(last_event_id) if last_event_id and last_event_id.isdigit() else -1


def iter_replay_message_events(disc, last_seq: int):
    for msg in disc.messages:
        if msg.seq >= 0 and msg.seq <= last_seq:
            continue
        yield format_sse_event(
            {"type": "message", "message": msg.to_dict()},
            str(msg.seq),
        )


def build_stream_status_event(disc) -> tuple[int, str]:
    status_seq = max(msg.seq + 1 for msg in disc.messages) if disc.messages else 0
    return status_seq, format_sse_event(
        {"type": "status", "status": disc.status.value},
        str(status_seq),
    )


def iter_closed_discussion_events(disc, status_seq: int):
    next_seq = status_seq
    if disc.plan:
        next_seq += 1
        yield format_sse_event({"type": "plan_updated", "plan": disc.plan}, str(next_seq))
    next_seq += 1
    yield format_sse_event(
        {"type": "discussion_end", "summary": disc.summary},
        str(next_seq),
    )


def format_live_stream_event(event: Dict[str, Any]) -> str:
    msg = event.get("message")
    event_id = str(msg.seq) if msg and hasattr(msg, "seq") and msg.seq >= 0 else ""
    if msg and hasattr(msg, "to_dict"):
        event = {**event, "message": msg.to_dict()}
    return format_sse_event(event, event_id)


def is_discussion_end_event(event: Dict[str, Any]) -> bool:
    return event.get("type") == "discussion_end"


def build_stream_heartbeat_event() -> str:
    return format_sse_event({"type": "heartbeat"})


def subscribe_discussion_stream(engine, disc_id: str):
    return engine.subscribe(disc_id)


def unsubscribe_discussion_stream(engine, disc_id: str, queue) -> None:
    engine.unsubscribe(disc_id, queue)
