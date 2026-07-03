# -*- coding: utf-8 -*-
"""Regression tests for task JSON persistence."""

from __future__ import annotations

import json

from agents.task_engine import AgentTask, TaskStatus
from agents.task_store import TaskStore


def test_task_store_save_load_and_delete_roundtrip(tmp_path):
    store = TaskStore(base_dir=tmp_path)
    task = AgentTask(
        task_id="task-1",
        agent_id="agent-1",
        team_id="team-1",
        title="写文档",
        description="保持中文 JSON",
        status=TaskStatus.RUNNING,
        priority=1,
        started_at="2026-06-26T00:00:00+00:00",
        result={"ok": True},
        dependencies=["task-0"],
        metadata={"source": "test"},
    )

    store.save_task(task)
    loaded = store.load_all()

    assert (tmp_path / "task-1.json").exists()
    assert loaded["task-1"].to_dict() == task.to_dict()

    store.delete_task("task-1")

    assert not (tmp_path / "task-1.json").exists()
    assert store.load_all() == {}


def test_task_store_skips_invalid_json_files(tmp_path):
    store = TaskStore(base_dir=tmp_path)
    (tmp_path / "bad.json").write_text("{bad json", encoding="utf-8")
    store.save_task(AgentTask(task_id="good", title="Good", agent_id="a1"))

    loaded = store.load_all()

    assert list(loaded) == ["good"]


def test_task_store_uses_utf8_pretty_json(tmp_path):
    store = TaskStore(base_dir=tmp_path)
    task = AgentTask(task_id="task-cn", title="中文标题", agent_id="agent-1")

    store.save_task(task)

    text = (tmp_path / "task-cn.json").read_text(encoding="utf-8")
    data = json.loads(text)
    assert data["title"] == "中文标题"
    assert "\\u4e2d" not in text
    assert "\n  " in text
