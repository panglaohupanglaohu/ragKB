# -*- coding: utf-8 -*-
"""Regression tests for cost target completion tracking."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from agents.cost_target_tracker import CostTargetTracker, _target_id_from_metadata
from agents.domain_events import DomainEvent, EventType


def test_target_id_from_metadata_accepts_direct_or_nested_id():
    assert _target_id_from_metadata({"target_id": "target-1"}) == "target-1"
    assert _target_id_from_metadata({"cost_target": {"id": "target-2"}}) == "target-2"
    assert _target_id_from_metadata({"cost_target": "target-3"}) is None
    assert _target_id_from_metadata({}) is None


@pytest.mark.asyncio
async def test_tracker_rechecks_progress_for_completed_target_task(monkeypatch):
    calls = []

    class FakeStore:
        def get_progress(self, target_id):
            calls.append(target_id)
            return {"current": 10, "progress": 0.5, "status": "active"}

    monkeypatch.setattr("agents.cost_targets.get_target_store", lambda: FakeStore())

    tracker = CostTargetTracker()
    event = DomainEvent.create(
        EventType.TASK_COMPLETED,
        SimpleNamespace(metadata={"target_id": "target-1"}),
    )

    await tracker._on_task_completed(event)

    assert calls == ["target-1"]


@pytest.mark.asyncio
async def test_tracker_ignores_completed_task_without_target(monkeypatch):
    called = {"value": False}

    class FakeStore:
        def get_progress(self, target_id):
            called["value"] = True
            return {}

    monkeypatch.setattr("agents.cost_targets.get_target_store", lambda: FakeStore())

    tracker = CostTargetTracker()
    event = DomainEvent.create(
        EventType.TASK_COMPLETED,
        SimpleNamespace(metadata={}),
    )

    await tracker._on_task_completed(event)

    assert called["value"] is False
