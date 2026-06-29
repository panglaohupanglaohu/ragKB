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
from agents.plaza import DiscussionStatus, PlazaMessage
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


class TestDiscussionLifecycle:
    @pytest.mark.asyncio
    async def test_create_discussion_persists_goal_and_metadata(self, isolated_plaza_engine):
        plaza = isolated_plaza_engine.create_plaza("生命周期广场", "lifecycle")

        payload = await plaza_routes.create_discussion(
            plaza.id,
            plaza_routes.CreateDiscussionRequest(
                topic="验证 Plaza 生命周期",
                description="从创建到启动的主路径",
                goal="确保讨论能被稳定创建",
                moderator_agent_id="pm-1",
                max_rounds=4,
            ),
        )

        stored = isolated_plaza_engine.get_discussion(plaza.id, payload["id"])
        assert payload["topic"] == "验证 Plaza 生命周期"
        assert payload["status"] == DiscussionStatus.OPEN.value
        assert stored is not None
        assert stored.goal == "确保讨论能被稳定创建"
        assert stored.moderator_agent_id == "pm-1"
        assert stored.max_rounds == 4

    @pytest.mark.asyncio
    async def test_start_discussion_resets_closed_discussion_before_scheduling(
        self,
        isolated_plaza_engine,
        monkeypatch,
    ):
        plaza, disc = _seed_discussion(isolated_plaza_engine)
        disc.status = DiscussionStatus.CLOSED
        disc.current_round = 2
        disc.messages.append(
            PlazaMessage(
                discussion_id=disc.id,
                agent_id="agent-1",
                agent_name="Agent 1",
                content="旧消息",
                round_number=2,
            )
        )
        disc.summary = "旧总结"
        disc.plan["task_ids"] = ["task-old"]
        disc.assigned_team_id = "team-old"
        isolated_plaza_engine._store.save_plaza(plaza)

        scheduled = []

        def fake_create_task(coro):
            scheduled.append(coro)
            coro.close()
            return object()

        monkeypatch.setattr(plaza_routes.asyncio, "create_task", fake_create_task)

        result = await plaza_routes.start_discussion(plaza.id, disc.id)

        refreshed = isolated_plaza_engine.get_discussion(plaza.id, disc.id)
        assert result["status"] == "started"
        assert scheduled, "discussion run coroutine should be scheduled"
        assert refreshed is not None
        assert refreshed.status == DiscussionStatus.OPEN
        assert refreshed.current_round == 0
        assert refreshed.messages == []
        assert refreshed.summary == ""
        assert refreshed.plan == {}
        assert refreshed.assigned_team_id == ""

    @pytest.mark.asyncio
    async def test_start_discussion_rejects_non_open_non_closed_state(self, isolated_plaza_engine):
        plaza, disc = _seed_discussion(isolated_plaza_engine)
        disc.status = DiscussionStatus.IN_PROGRESS
        isolated_plaza_engine._store.save_plaza(plaza)

        with pytest.raises(plaza_routes.HTTPException) as exc_info:
            await plaza_routes.start_discussion(plaza.id, disc.id)

        assert exc_info.value.status_code == 400
        assert "无法启动" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_run_discussion_startup_uses_simulated_path_without_chat_fn(
        self,
        isolated_plaza_engine,
        monkeypatch,
    ):
        plaza, disc = _seed_discussion(isolated_plaza_engine)
        broadcasts = []
        simulated = []
        saved = []

        async def fake_sleep(_seconds):
            return None

        async def fake_broadcast(discussion_id, event):
            broadcasts.append((discussion_id, event))

        async def fake_run_simulated(disc_arg, moderator, speakers):
            simulated.append((disc_arg.id, moderator.agent_id if moderator else "", [s.agent_id for s in speakers]))
            disc_arg.status = DiscussionStatus.CLOSED

        monkeypatch.setattr(plaza_engine_module.asyncio, "sleep", fake_sleep)
        monkeypatch.setattr(isolated_plaza_engine, "_broadcast", fake_broadcast)
        monkeypatch.setattr(isolated_plaza_engine, "_run_simulated", fake_run_simulated)
        monkeypatch.setattr(isolated_plaza_engine._store, "save_plaza", lambda plaza_arg: saved.append(plaza_arg.id))

        result = await isolated_plaza_engine.run_discussion(plaza.id, disc.id)

        assert result is disc
        assert disc.started_at
        assert broadcasts[0][1] == {
            "type": "discussion_start",
            "discussion_id": disc.id,
            "topic": disc.topic,
        }
        assert simulated
        assert simulated[0][0] == disc.id
        assert saved == [plaza.id]

    @pytest.mark.asyncio
    async def test_run_discussion_opening_uses_moderator_prompt(
        self,
        isolated_plaza_engine,
        monkeypatch,
    ):
        plaza, disc = _seed_discussion(isolated_plaza_engine)
        disc.description = "保留现有行为"
        disc.goal = "拆清楚开场边界"
        moderator = isolated_plaza_engine.add_participant(
            plaza.id,
            "pm-1",
            "主持人",
            "project_manager",
            niche_role=plaza_engine_module.NicheRole.MODERATOR,
        )
        speaker = isolated_plaza_engine.add_participant(
            plaza.id,
            "dev-1",
            "开发者",
            "developer",
        )
        calls = []

        async def fake_speak_with_lock(disc_arg, participant_arg, prompt, round_number, niche_role):
            calls.append((disc_arg.id, participant_arg.agent_id, prompt, round_number, niche_role))
            return PlazaMessage(
                discussion_id=disc_arg.id,
                agent_id=participant_arg.agent_id,
                content="开场",
                round_number=round_number,
            )

        monkeypatch.setattr(isolated_plaza_engine, "_speak_with_lock", fake_speak_with_lock)

        result = await isolated_plaza_engine._run_discussion_opening(disc, moderator, [speaker])

        assert result.content == "开场"
        assert calls
        _, agent_id, prompt, round_number, niche_role = calls[0]
        assert agent_id == "pm-1"
        assert round_number == 0
        assert niche_role == "moderator"
        assert "讨论话题: 「让 Plaza 真的能派发任务」" in prompt
        assert "话题描述: 保留现有行为" in prompt
        assert "讨论目标: 拆清楚开场边界" in prompt
        assert "参与者: 开发者" in prompt
        assert "不要自行转换或重新解读话题" in prompt

    def test_build_round_speaker_prompt_uses_recent_context(self, isolated_plaza_engine):
        plaza, disc = _seed_discussion(isolated_plaza_engine)
        disc.description = "已有背景"
        disc.goal = "保持行为"
        speaker = isolated_plaza_engine.add_participant(
            plaza.id,
            "dev-1",
            "开发者",
            "developer",
        )
        disc.messages.append(
            PlazaMessage(
                discussion_id=disc.id,
                agent_id="pm-1",
                agent_name="主持人",
                content="先确认边界",
                round_number=0,
            )
        )

        prompt = isolated_plaza_engine._build_round_speaker_prompt(disc, speaker, 2, 1)

        assert "你正在参与关于「让 Plaza 真的能派发任务」的团队讨论。" in prompt
        assert "背景描述: 已有背景" in prompt
        assert "讨论目标: 保持行为" in prompt
        assert "你是 开发者（developer）。第 2 轮，第 2 次发言。" in prompt
        assert "先确认边界" in prompt
        assert "回应上面讨论中你认为重要的点" in prompt

    @pytest.mark.asyncio
    async def test_abort_discussion_for_fallback_records_message(
        self,
        isolated_plaza_engine,
        monkeypatch,
    ):
        plaza, disc = _seed_discussion(isolated_plaza_engine)
        disc.max_rounds = 5
        moderator = isolated_plaza_engine.add_participant(
            plaza.id,
            "pm-1",
            "主持人",
            "project_manager",
            niche_role=plaza_engine_module.NicheRole.MODERATOR,
        )
        broadcasts = []

        async def fake_broadcast(discussion_id, event):
            broadcasts.append((discussion_id, event))

        monkeypatch.setattr(isolated_plaza_engine, "_broadcast", fake_broadcast)

        await isolated_plaza_engine._abort_discussion_for_fallback(disc, moderator, 2, 2)

        assert disc.max_rounds == 2
        assert len(disc.messages) == 1
        abort_msg = disc.messages[0]
        assert abort_msg.seq == 0
        assert abort_msg.agent_id == "pm-1"
        assert abort_msg.agent_name == "主持人"
        assert abort_msg.niche_role == "moderator"
        assert abort_msg.round_number == 2
        assert "LLM 当前不可用" in abort_msg.content
        assert broadcasts[0][0] == disc.id
        assert broadcasts[0][1]["type"] == "message"
        assert broadcasts[0][1]["message"]["seq"] == 0

    def test_build_round_summary_prompt_uses_round_messages(self, isolated_plaza_engine):
        _, disc = _seed_discussion(isolated_plaza_engine)
        disc.messages.append(
            PlazaMessage(
                discussion_id=disc.id,
                agent_id="dev-1",
                agent_name="开发者",
                content="需要拆清楚轮次职责",
                round_number=2,
            )
        )

        prompt = isolated_plaza_engine._build_round_summary_prompt(disc, 2)

        assert "你是主持人。第 2 轮讨论已结束。" in prompt
        assert "需要拆清楚轮次职责" in prompt
        assert "总结大家达成的共识和仍有分歧的地方" in prompt
        assert "提出下一轮需要重点讨论的问题" in prompt
