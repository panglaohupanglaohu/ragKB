# -*- coding: utf-8 -*-
"""Regression tests for runtime event envelope helpers."""

from __future__ import annotations

from agents.runtime.events import make_runtime_event_emitter


def test_runtime_event_emitter_uses_session_id_and_sequences_events():
    callback_events = []
    runtime_id, emit = make_runtime_event_emitter(
        loop_kind="plan_loop",
        session_id="sess-1",
        on_event=lambda kind, payload: callback_events.append((kind, payload)),
    )

    first = emit("start", {"extra": "value"})
    second = emit("done")

    assert runtime_id == "sess-1"
    assert first["runtime_id"] == "sess-1"
    assert first["loop_kind"] == "plan_loop"
    assert first["sequence"] == 1
    assert first["session_id"] == "sess-1"
    assert first["extra"] == "value"
    assert second["sequence"] == 2
    assert callback_events == [("start", first), ("done", second)]


def test_runtime_event_emitter_generates_runtime_id_without_session():
    runtime_id, emit = make_runtime_event_emitter(loop_kind="tool_loop")
    event = emit("loop_start")

    assert runtime_id.startswith("tool_loop-")
    assert len(runtime_id) == len("tool_loop-") + 12
    assert event["runtime_id"] == runtime_id
    assert event["session_id"] == ""
