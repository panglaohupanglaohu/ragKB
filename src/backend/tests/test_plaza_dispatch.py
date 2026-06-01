# -*- coding: utf-8 -*-
"""Plaza discussion dispatch tests."""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from agents import api as api_module
from agents import plaza_engine as plaza_engine_module
from agents import plaza_routes
from agents import task_engine as task_engine_module
from agents.plaza_engine import PlazaEngine
from agents.plaza_store import PlazaStore
from agents.task_engine import AgentTask, TaskEngine
from agents.task_store import TaskStore


@pytest.fixture
def isolated_plaza_engine(monkeypatch):
    with TemporaryDirectory() as tmpdir:
        engine = PlazaEngine()
        engine._store = PlazaStore(base_dir=Path(tmpdir))
        engine._plazas = {}
        monkeypatch.setattr(plaza_engine_module, "_engine", engine)
        yield engine


@pytest.fixture
def isolated_task_engine(monkeypatch):
    with TemporaryDirectory() as tmpdir:
        engine = TaskEngine(store=TaskStore(base_dir=Path(tmpdir)))
        monkeypatch.setattr(task_engine_module, "_engine", engine)
        yield engine


def _build_plan_text() -> str:
    return (
        "## 执行计划\n"
        "| 序号 | 任务 | 负责角色 | 优先级 | 依赖 | 预期产出 |\n"
        "|---|---|---|---|---|---|\n"
        "| 1 | 修复启动链路 | developer | P0 | 无 | 启动补丁 |\n"
        "| 2 | 补回归测试 | qa | P1 | 1 | pytest 报告 |\n"
    )


def _seed_discussion(engine: PlazaEngine):
    plaza = engine.create_plaza("测试广场", "dispatch")
    disc = engine.create_discussion(plaza.id, "让 Plaza 真的能派发任务", "dispatch", "", 3)
    disc.plan = {
        "revision": 3,
        "revision_reason": "测试计划",
        "revised_at": "2026-05-29T00:00:00+00:00",
        "content": _build_plan_text(),
    }
    engine._store.save_plaza(plaza)
    return plaza, disc


class TestPlanParsing:
    def test_parse_markdown_plan_table(self):
        tasks = plaza_routes._parse_plan_table(_build_plan_text())
        assert len(tasks) == 2
        assert tasks[0]["title"] == "修复启动链路"
        assert tasks[0]["priority"] == 1
        assert tasks[0]["responsible"] == "developer"
        assert tasks[0]["expected_artifact"] == "启动补丁"
        assert tasks[1]["dependencies"] == "1"


class TestDiscussionDispatch:
    @pytest.mark.asyncio
    async def test_list_discussions_supports_optional_pagination(self, isolated_plaza_engine):
        plaza, _ = _seed_discussion(isolated_plaza_engine)
        isolated_plaza_engine.create_discussion(plaza.id, "第二个议题", "dispatch", "", 3)

        payload = await plaza_routes.list_discussions(plaza.id, limit=1, offset=1)

        assert payload["total"] == 2
        assert payload["limit"] == 1
        assert payload["offset"] == 1
        assert len(payload["items"]) == 1

    @pytest.mark.asyncio
    async def test_dispatch_tasks_updates_discussion_plan(self, isolated_plaza_engine, monkeypatch):
        plaza, disc = _seed_discussion(isolated_plaza_engine)
        submitted = []

        async def fake_submit_internal_task(team_id: str, **kwargs):
            task = AgentTask(
                task_id=f"task-{len(submitted) + 1}",
                team_id=team_id,
                title=kwargs["title"],
                description=kwargs["description"],
                priority=kwargs["priority"],
                metadata=kwargs["metadata"],
            )
            submitted.append(task)
            return task

        monkeypatch.setattr(api_module, "_submit_internal_task", fake_submit_internal_task)

        result = await plaza_routes.dispatch_tasks_from_discussion(
            plaza.id,
            disc.id,
            plaza_routes.DispatchTasksRequest(team_id="team-build"),
        )

        assert result["status"] == "dispatched"
        assert result["task_count"] == 2
        assert [task["task_id"] for task in result["tasks"]] == ["task-1", "task-2"]

        updated_disc = isolated_plaza_engine.get_discussion(plaza.id, disc.id)
        assert updated_disc.assigned_team_id == "team-build"
        assert updated_disc.plan["task_ids"] == ["task-1", "task-2"]
        assert updated_disc.plan["task_count"] == 2
        assert updated_disc.plan["team_id"] == "team-build"

        first_metadata = result["tasks"][0]["metadata"]
        assert first_metadata["source"] == "plaza"
        assert first_metadata["discussion_id"] == disc.id
        assert first_metadata["plan_revision"] == 3
        assert first_metadata["plan_item_index"] == 0
        assert first_metadata["responsible_role"] == "developer"
        assert first_metadata["skills_used"] == ["code_implementation", "debugging"]
        assert first_metadata["trace_context"]["discussion_id"] == disc.id
        assert first_metadata["trace_context"]["plaza_id"] == plaza.id
        assert first_metadata["trace_context"]["plan_revision"] == 3

        second_metadata = result["tasks"][1]["metadata"]
        assert second_metadata["responsible_role"] == "qa"
        assert second_metadata["skills_used"] == ["testing", "test_execution", "regression_testing"]

        summary = await plaza_routes.get_discussion_summary(plaza.id, disc.id)
        assert summary["plan_revision"] == 3
        assert summary["task_ids"] == ["task-1", "task-2"]
        assert summary["task_count"] == 2

    @pytest.mark.asyncio
    async def test_get_discussion_tasks_returns_only_linked_tasks(
        self,
        isolated_plaza_engine,
        isolated_task_engine,
    ):
        plaza, disc = _seed_discussion(isolated_plaza_engine)

        await isolated_task_engine.submit_task(
            AgentTask(
                task_id="task-2",
                team_id="team-build",
                title="第二个任务",
                metadata={
                    "source": "plaza",
                    "plaza_id": plaza.id,
                    "discussion_id": disc.id,
                    "plan_item_index": 1,
                },
            )
        )
        await isolated_task_engine.submit_task(
            AgentTask(
                task_id="task-1",
                team_id="team-build",
                title="第一个任务",
                metadata={
                    "source": "plaza",
                    "plaza_id": plaza.id,
                    "discussion_id": disc.id,
                    "plan_item_index": 0,
                },
            )
        )
        await isolated_task_engine.submit_task(
            AgentTask(
                task_id="task-x",
                team_id="other",
                title="无关任务",
                metadata={
                    "source": "plaza",
                    "plaza_id": plaza.id,
                    "discussion_id": "other-discussion",
                    "plan_item_index": 0,
                },
            )
        )

        result = await plaza_routes.get_discussion_tasks(plaza.id, disc.id)
        assert result["task_count"] == 2
        assert [task["task_id"] for task in result["tasks"]] == ["task-1", "task-2"]

        paged = await plaza_routes.get_discussion_tasks(plaza.id, disc.id, limit=1, offset=1)
        assert paged["task_count"] == 2
        assert paged["limit"] == 1
        assert paged["offset"] == 1
        assert paged["has_more"] is False
        assert [task["task_id"] for task in paged["tasks"]] == ["task-2"]
