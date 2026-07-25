# -*- coding: utf-8 -*-
"""Plaza multi-team plan dispatch — parallel lanes for twin matchup."""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import AsyncMock, MagicMock

import pytest

from agents import plaza_engine as plaza_engine_module
from agents import plaza_routes
from agents.execution_plan import build_plan_from_text, save_plan_to_discussion
from agents.plaza_engine import PlazaEngine
from agents.plaza_store import PlazaStore


GOOD_PLAN = (
    "## 执行计划\n"
    "| 序号 | 任务 | 负责角色 | 优先级 | 依赖 | 预期产出 |\n"
    "|---|---|---|---|---|---|\n"
    "| 1 | 调研现状并整理约束 | researcher | P0 | 无 | 调研报告 |\n"
    "| 2 | 设计并实现方案 | developer | P1 | 1 | 可运行补丁 |\n"
)


@pytest.fixture
def isolated_plaza_engine(monkeypatch):
    with TemporaryDirectory() as tmpdir:
        engine = PlazaEngine()
        engine._store = PlazaStore(base_dir=Path(tmpdir))
        engine._plazas = {}
        monkeypatch.setattr(plaza_engine_module, "_engine", engine)
        yield engine


def _seed(engine, plan_text=GOOD_PLAN):
    plaza = engine.create_plaza("多队广场", "plan")
    disc = engine.create_discussion(plaza.id, "多队并行派发", "plan", "", 3)
    disc.plan = {"revision": 1, "content": plan_text}
    plan = build_plan_from_text(plan_text, topic=disc.topic, goal="")
    plan.status = "approved"
    save_plan_to_discussion(disc, plan)
    engine._store.save_plaza(plaza)
    return plaza, disc


class _FakeTask:
    def __init__(self, team_id, title, **kwargs):
        self.task_id = f"task_{team_id}_{title[:8]}_{id(self) % 10000}"
        self.team_id = team_id
        self.title = title
        self.metadata = kwargs.get("metadata") or {}

    def to_dict(self):
        return {
            "task_id": self.task_id,
            "team_id": self.team_id,
            "title": self.title,
            "metadata": self.metadata,
            "status": "pending",
        }


@pytest.mark.asyncio
async def test_resolve_dispatch_team_ids():
    assert plaza_routes._resolve_dispatch_team_ids("a", ["b", "a", "c"]) == ["b", "a", "c"]
    assert plaza_routes._resolve_dispatch_team_ids("only", []) == ["only"]
    assert plaza_routes._resolve_dispatch_team_ids("", ["x", "y"]) == ["x", "y"]


@pytest.mark.asyncio
async def test_multi_team_dispatch_clones_plan(isolated_plaza_engine, monkeypatch):
    engine = isolated_plaza_engine
    plaza, disc = _seed(engine)

    created = []

    async def fake_submit(team_id, **kwargs):
        t = _FakeTask(team_id, kwargs.get("title") or "t", metadata=kwargs.get("metadata"))
        created.append(t)
        return t

    monkeypatch.setattr(plaza_routes, "_submit_internal_task", fake_submit, raising=False)
    # patch where it's imported from
    import agents.api as agent_api

    monkeypatch.setattr(agent_api, "_submit_internal_task", fake_submit, raising=False)

    # re-import path used inside function
    async def _wrap(*a, **k):
        return await fake_submit(a[0] if a else k.get("team_id"), **{kk: vv for kk, vv in k.items() if kk != "team_id"})

    # Patch at module level used by plaza_routes
    async def submit_internal(team_id, agent_id="", title="", description="", priority=2, metadata=None, auto_start=False):
        return await fake_submit(team_id, title=title, metadata=metadata)

    monkeypatch.setattr(
        "agents.api._submit_internal_task",
        submit_internal,
        raising=False,
    )

    # Ensure plaza_routes imports fresh
    from agents.api import _submit_internal_task as _orig  # noqa: F401

    monkeypatch.setattr(
        plaza_routes,
        "_submit_internal_task",
        submit_internal,
        raising=False,
    )

    # Directly patch the import inside _dispatch_discussion_tasks by mocking agents.api
    import agents.api as api_mod

    monkeypatch.setattr(api_mod, "_submit_internal_task", submit_internal)

    result = await plaza_routes._dispatch_discussion_tasks_multi(
        plaza.id,
        disc,
        ["team_alpha", "team_beta"],
        auto_start=False,
    )

    assert result["multi_team"] is True
    assert result["team_ids"] == ["team_alpha", "team_beta"]
    assert result["dispatch_group_id"].startswith("dg_")
    assert len(result["dispatches"]) == 2
    # 2 steps × 2 teams = 4 tasks
    assert result["task_count"] == 4
    assert disc.plan["multi_team"] is True
    assert set(disc.plan["team_ids"]) == {"team_alpha", "team_beta"}
    # metadata has shared group
    groups = {t.metadata.get("dispatch_group_id") for t in created}
    assert len(groups) == 1 and list(groups)[0].startswith("dg_")
    teams_in_meta = {t.metadata.get("team_id") for t in created}
    assert teams_in_meta == {"team_alpha", "team_beta"}

    # 结构化步骤带 task_ids_by_team
    from agents.execution_plan import load_plan_from_discussion

    plan = load_plan_from_discussion(disc)
    assert plan is not None
    assert plan.status == "dispatched"
    assert any(s.task_ids_by_team for s in plan.steps)


@pytest.mark.asyncio
async def test_dispatch_endpoint_team_ids(isolated_plaza_engine, monkeypatch):
    """HTTP-level dispatch with team_ids body."""
    engine = isolated_plaza_engine
    plaza, disc = _seed(engine)

    # approve first
    await plaza_routes.approve_execution_plan(
        plaza.id, disc.id, plaza_routes.ApprovePlanRequest(approved_by="tester")
    )

    created = []

    async def submit_internal(team_id, agent_id="", title="", description="", priority=2, metadata=None, auto_start=False):
        t = _FakeTask(team_id, title or "t", metadata=metadata or {})
        created.append(t)
        return t

    import agents.api as api_mod

    monkeypatch.setattr(api_mod, "_submit_internal_task", submit_internal)

    req = plaza_routes.DispatchTasksRequest(
        team_id="team_a",
        team_ids=["team_a", "team_b"],
        mode="parallel",
    )
    resp = await plaza_routes.dispatch_tasks_from_discussion(plaza.id, disc.id, req)
    assert resp["status"] == "dispatched"
    assert resp["multi_team"] is True
    assert resp["team_ids"] == ["team_a", "team_b"]
    assert resp["task_count"] == 4  # 2 steps × 2 teams
    assert resp["twin_hint"]["extra_team_ids"] == ["team_b"]
    assert "team_ids=" in resp["twin_hint"]["url_query"]

    # get_execution_plan exposes multi_dispatch
    ge = await plaza_routes.get_execution_plan(plaza.id, disc.id)
    assert ge["multi_dispatch"]["multi_team"] is True
    assert set(ge["multi_dispatch"]["team_ids"]) == {"team_a", "team_b"}
