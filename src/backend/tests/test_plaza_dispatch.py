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

    def test_resolve_startable_discussion_resets_closed_state(self, isolated_plaza_engine):
        plaza, disc = _seed_discussion(isolated_plaza_engine)
        disc.status = DiscussionStatus.CLOSED
        disc.current_round = 2
        disc.messages.append(PlazaMessage(discussion_id=disc.id, agent_id="a-1", content="旧消息"))
        disc.summary = "旧总结"
        disc.assigned_team_id = "team-old"
        isolated_plaza_engine._store.save_plaza(plaza)

        refreshed = plaza_routes._resolve_startable_discussion(
            isolated_plaza_engine,
            plaza.id,
            disc.id,
        )

        assert refreshed.status == DiscussionStatus.OPEN
        assert refreshed.current_round == 0
        assert refreshed.messages == []
        assert refreshed.summary == ""
        assert refreshed.assigned_team_id == ""

    def test_schedule_discussion_run_uses_background_task(self, isolated_plaza_engine, monkeypatch):
        plaza, disc = _seed_discussion(isolated_plaza_engine)
        scheduled = []

        def fake_create_task(coro):
            scheduled.append(coro)
            coro.close()
            return object()

        monkeypatch.setattr(plaza_routes.asyncio, "create_task", fake_create_task)

        plaza_routes._schedule_discussion_run(isolated_plaza_engine, plaza.id, disc.id)

        assert len(scheduled) == 1

    def test_format_sse_event_preserves_optional_id_and_unicode_payload(self):
        assert plaza_routes._format_sse_event({"type": "heartbeat"}) == (
            'data: {"type": "heartbeat"}\n\n'
        )
        assert plaza_routes._format_sse_event({"type": "message", "text": "议事"}, "7") == (
            'id: 7\ndata: {"type": "message", "text": "议事"}\n\n'
        )

    def test_parse_last_event_id_matches_existing_digit_only_behavior(self):
        assert plaza_routes._parse_last_event_id("") == -1
        assert plaza_routes._parse_last_event_id("abc") == -1
        assert plaza_routes._parse_last_event_id("-1") == -1
        assert plaza_routes._parse_last_event_id("12") == 12

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

    def test_build_final_summary_prompt_uses_history_and_plan_contract(self, isolated_plaza_engine):
        _, disc = _seed_discussion(isolated_plaza_engine)
        disc.description = "最终总结背景"
        disc.goal = "生成可派发任务"
        disc.max_rounds = 2
        disc.messages.append(
            PlazaMessage(
                discussion_id=disc.id,
                agent_id="dev-1",
                agent_name="开发者",
                content="优先拆边界再补测试",
                round_number=1,
            )
        )

        prompt = isolated_plaza_engine._build_final_summary_prompt(disc)

        assert "关于「让 Plaza 真的能派发任务」的讨论已经完成 2 轮" in prompt
        assert "背景描述: 最终总结背景" in prompt
        assert "讨论目标: 生成可派发任务" in prompt
        assert "优先拆边界再补测试" in prompt
        assert "## 加权结论 (P0→P1→P2)" in prompt
        assert "| 序号 | 任务 | 负责角色 | 优先级 | 依赖 | 预期产出 |" in prompt
        assert "请用 Markdown 输出，简洁有力，能直接作为任务单下发。" in prompt

    def test_apply_deterministic_summary_fallback_sets_plan_ready_summary(self, isolated_plaza_engine):
        plaza, disc = _seed_discussion(isolated_plaza_engine)
        disc.summary = "LLM 当前不可用"
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

        isolated_plaza_engine._apply_deterministic_summary_fallback(disc, moderator, [speaker])

        assert isolated_plaza_engine._has_actionable_plan(disc.summary)
        assert "LLM 不可用或未返回结构化计划" in disc.summary
        assert "| 序号 | 任务 | 负责角色 | 优先级 | 依赖 | 预期产出 |" in disc.summary
        assert disc.key_conclusions == [
            "围绕「让 Plaza 真的能派发任务」明确目标与关键约束",
            "分步推进方案设计、验证与执行",
            "演练通过后再进入实际派发",
        ]

    @pytest.mark.asyncio
    async def test_close_discussion_with_summary_broadcasts_closing_events(
        self,
        isolated_plaza_engine,
        monkeypatch,
    ):
        plaza, disc = _seed_discussion(isolated_plaza_engine)
        disc.max_rounds = 2
        disc.summary = "## 讨论概要\n收束内容\n\n## 执行计划\n| 序号 | 任务 |\n|---|---|"
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

        closing_msg = await isolated_plaza_engine._close_discussion_with_summary(disc, moderator)

        assert closing_msg is disc.messages[-1]
        assert closing_msg.seq == 0
        assert closing_msg.agent_id == "pm-1"
        assert closing_msg.niche_role == "moderator"
        assert closing_msg.round_number == 3
        assert closing_msg.metadata == {"summary_kind": "closing_brief"}
        assert closing_msg.content == "本场收束：讨论概要\n立即执行：先从 P0 任务切入推进。"
        assert disc.status == DiscussionStatus.CLOSED
        assert disc.ended_at
        assert broadcasts[0][1]["type"] == "message"
        assert broadcasts[0][1]["message"]["seq"] == 0
        assert broadcasts[1][1] == {
            "type": "discussion_end",
            "summary": disc.summary,
        }

    def test_build_auto_extract_description_uses_summary_and_plan(self, isolated_plaza_engine):
        _, disc = _seed_discussion(isolated_plaza_engine)
        disc.summary = "共识摘要"
        disc.plan = {"content": "执行计划内容"}

        description = isolated_plaza_engine._build_auto_extract_description(disc)

        assert description == (
            "[议事广场自动萃取] 议题: 让 Plaza 真的能派发任务\n\n"
            "共识摘要:\n共识摘要\n\n"
            "执行计划:\n执行计划内容"
        )

    def test_prepare_interjection_context_resolves_moderator_and_speakers(self, isolated_plaza_engine):
        plaza, disc = _seed_discussion(isolated_plaza_engine)
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

        result = isolated_plaza_engine._prepare_interjection_context(plaza.id, disc.id)

        assert result[0] is plaza
        assert result[1] is disc
        assert result[2] is moderator
        assert result[3] == [speaker]

    def test_prepare_interjection_context_rejects_missing_moderator(self, isolated_plaza_engine):
        plaza, disc = _seed_discussion(isolated_plaza_engine)

        with pytest.raises(ValueError) as exc_info:
            isolated_plaza_engine._prepare_interjection_context(plaza.id, disc.id)

        assert str(exc_info.value) == "广场没有议事长"

    def test_build_simulated_interjection_plan_content_uses_chosen_agent(self, isolated_plaza_engine):
        plaza, _ = _seed_discussion(isolated_plaza_engine)
        speaker = isolated_plaza_engine.add_participant(
            plaza.id,
            "dev-1",
            "开发者",
            "developer",
        )

        content = isolated_plaza_engine._build_simulated_interjection_plan_content(
            "这是一条很长的用户插话，需要被截断后写入修订说明，避免计划说明过长。",
            speaker,
        )

        assert "针对用户问题「这是一条很长的用户插话，需要被截断后写入修订说明，避免计划说明过长。」修订" in content
        assert "| 1 | 回应用户问题 | 开发者 | P0 | 无 | 方案落地 |" in content
        assert "## 执行计划" in content

    def test_build_interjection_redirect_prompt_lists_candidates(self, isolated_plaza_engine):
        plaza, disc = _seed_discussion(isolated_plaza_engine)
        disc.current_round = 3
        disc.messages.append(
            PlazaMessage(
                discussion_id=disc.id,
                agent_id="pm-1",
                agent_name="主持人",
                content="先聚焦当前方案",
                round_number=3,
            )
        )
        speaker = isolated_plaza_engine.add_participant(
            plaza.id,
            "dev-1",
            "开发者",
            "developer",
        )

        prompt = isolated_plaza_engine._build_interjection_redirect_prompt(
            disc,
            [speaker],
            "用户要求补充验收标准",
        )

        assert "讨论话题: 「让 Plaza 真的能派发任务」" in prompt
        assert "当前轮次: 3" in prompt
        assert "先聚焦当前方案" in prompt
        assert "用户插话: 「用户要求补充验收标准」" in prompt
        assert "- dev-1 | 开发者 | developer" in prompt
        assert "REPLY: 你给用户和全场的纠偏回应" in prompt
        assert "NEXT: 候选中的 agent_id" in prompt

    def test_build_interjection_nominated_reply_prompt_uses_context(self, isolated_plaza_engine):
        plaza, disc = _seed_discussion(isolated_plaza_engine)
        disc.messages.append(
            PlazaMessage(
                discussion_id=disc.id,
                agent_id="pm-1",
                agent_name="主持人",
                content="先回应验收标准",
                round_number=2,
            )
        )
        chosen = isolated_plaza_engine.add_participant(
            plaza.id,
            "qa-1",
            "测试",
            "qa",
        )

        prompt = isolated_plaza_engine._build_interjection_nominated_reply_prompt(
            disc,
            chosen,
            "用户要求补充验收标准",
            "请 测试 先回应。",
        )

        assert "你是 测试（qa）。主持人刚刚点名你" in prompt
        assert "讨论话题: 「让 Plaza 真的能派发任务」" in prompt
        assert "用户插话: 「用户要求补充验收标准」" in prompt
        assert "主持人刚才的话: 「请 测试 先回应。」" in prompt
        assert "先回应验收标准" in prompt
        assert "必须回答用户的具体问题" in prompt

    def test_build_interjection_supplementary_reply_prompt_uses_prior_reply(self, isolated_plaza_engine):
        plaza, disc = _seed_discussion(isolated_plaza_engine)
        disc.messages.append(
            PlazaMessage(
                discussion_id=disc.id,
                agent_id="qa-1",
                agent_name="测试",
                content="需要验收标准",
                round_number=2,
            )
        )
        chosen = isolated_plaza_engine.add_participant(
            plaza.id,
            "qa-1",
            "测试",
            "qa",
        )
        extra = isolated_plaza_engine.add_participant(
            plaza.id,
            "dev-1",
            "开发者",
            "developer",
        )
        speaker_msg = PlazaMessage(
            discussion_id=disc.id,
            agent_id="qa-1",
            agent_name="测试",
            content="先补验收标准。",
            round_number=2,
        )

        prompt = isolated_plaza_engine._build_interjection_supplementary_reply_prompt(
            disc,
            extra,
            chosen,
            speaker_msg,
            "用户要求补充验收标准",
        )

        assert "你是 开发者（developer）。" in prompt
        assert "讨论话题: 「让 Plaza 真的能派发任务」" in prompt
        assert "用户刚才提出了问题/建议: 「用户要求补充验收标准」" in prompt
        assert "主持人点名的 测试 已回应: 「先补验收标准。」" in prompt
        assert "需要验收标准" in prompt
        assert "不要重复已有观点" in prompt

    def test_build_interjection_revised_plan_prompt_uses_responses_and_existing_plan(self, isolated_plaza_engine):
        plaza, disc = _seed_discussion(isolated_plaza_engine)
        disc.goal = "补全验收"
        chosen = isolated_plaza_engine.add_participant(
            plaza.id,
            "qa-1",
            "测试",
            "qa",
        )
        speaker_msg = PlazaMessage(
            discussion_id=disc.id,
            agent_id="qa-1",
            agent_name="测试",
            content="需要加入回归测试。",
            round_number=2,
        )
        extra_reply = PlazaMessage(
            discussion_id=disc.id,
            agent_id="dev-1",
            agent_name="开发者",
            content="实现前先拆接口边界。",
            round_number=2,
        )

        prompt = isolated_plaza_engine._build_interjection_revised_plan_prompt(
            disc,
            "用户要求补充验收标准",
            chosen,
            speaker_msg,
            [extra_reply],
        )

        assert "讨论话题: 「让 Plaza 真的能派发任务」" in prompt
        assert "讨论目标: 补全验收" in prompt
        assert "用户插话: 「用户要求补充验收标准」" in prompt
        assert "测试: 需要加入回归测试。" in prompt
        assert "开发者: 实现前先拆接口边界。" in prompt
        assert '"revision": 3' in prompt
        assert "| 序号 | 任务 | 负责角色 | 优先级 | 依赖 | 预期产出 |" in prompt
        assert "必须体现用户刚提出的问题/建议的处理方式" in prompt

    def test_format_interjection_responses_defaults_when_empty(self, isolated_plaza_engine):
        assert isolated_plaza_engine._format_interjection_responses(None, None, []) == "无回应"

    @pytest.mark.asyncio
    async def test_publish_interjection_plan_update_saves_and_resumes(
        self,
        isolated_plaza_engine,
        monkeypatch,
    ):
        plaza, disc = _seed_discussion(isolated_plaza_engine)
        disc.current_round = 4
        moderator = isolated_plaza_engine.add_participant(
            plaza.id,
            "pm-1",
            "主持人",
            "project_manager",
            niche_role=plaza_engine_module.NicheRole.MODERATOR,
        )
        published = []
        broadcasts = []
        saved = []

        async def fake_publish_message(disc_arg, participant, content, **kwargs):
            published.append((disc_arg.id, participant.agent_id, content, kwargs))
            msg = PlazaMessage(
                discussion_id=disc_arg.id,
                agent_id=participant.agent_id,
                agent_name=participant.agent_name,
                content=content,
                round_number=kwargs["round_number"],
            )
            msg.reply_to = kwargs["reply_to"]
            msg.metadata.update(kwargs["metadata"])
            return msg

        async def fake_broadcast(discussion_id, event):
            broadcasts.append((discussion_id, event))

        monkeypatch.setattr(isolated_plaza_engine, "publish_message", fake_publish_message)
        monkeypatch.setattr(isolated_plaza_engine, "_broadcast", fake_broadcast)
        monkeypatch.setattr(isolated_plaza_engine._store, "save_plaza", lambda plaza_arg: saved.append(plaza_arg.id))

        msg = await isolated_plaza_engine._publish_interjection_plan_update(
            plaza,
            disc,
            moderator,
            _build_plan_text(),
            "用户补充验收标准",
            "reply-to-message",
        )

        assert msg.reply_to == "reply-to-message"
        assert msg.metadata == {"interjection_kind": "revised_plan"}
        assert disc.plan["revision_reason"] == "用户补充验收标准"
        assert disc.plan["content"] == _build_plan_text()
        assert published[0][3]["round_number"] == 4
        assert published[0][3]["niche_role"] == "moderator"
        assert broadcasts[0][1] == {"type": "plan_updated", "plan": disc.plan}
        assert broadcasts[1][1] == {"type": "interjection_state", "state": "resumed"}
        assert saved == [plaza.id]

    @pytest.mark.asyncio
    async def test_broadcast_interjection_paused_uses_stable_payload(
        self,
        isolated_plaza_engine,
        monkeypatch,
    ):
        _, disc = _seed_discussion(isolated_plaza_engine)
        broadcasts = []

        async def fake_broadcast(discussion_id, event):
            broadcasts.append((discussion_id, event))

        monkeypatch.setattr(isolated_plaza_engine, "_broadcast", fake_broadcast)

        await isolated_plaza_engine._broadcast_interjection_paused(disc)

        assert broadcasts == [
            (
                disc.id,
                {
                    "type": "interjection_state",
                    "state": "paused",
                    "message": "议事长正在纠偏当前讨论节奏",
                },
            )
        ]

    @pytest.mark.asyncio
    async def test_handle_simulated_interjection_publishes_reply_plan_and_saves(
        self,
        isolated_plaza_engine,
        monkeypatch,
    ):
        plaza, disc = _seed_discussion(isolated_plaza_engine)
        disc.current_round = 2
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
        broadcasts = []
        saved = []

        async def fake_broadcast(discussion_id, event):
            broadcasts.append((discussion_id, event))

        monkeypatch.setattr(isolated_plaza_engine, "_broadcast", fake_broadcast)
        monkeypatch.setattr(isolated_plaza_engine._store, "save_plaza", lambda plaza_arg: saved.append(plaza_arg.id))

        result = await isolated_plaza_engine._handle_simulated_interjection(
            plaza,
            disc,
            moderator,
            [speaker],
            "用户要求补充验收标准",
            "user-msg-1",
        )

        assert result["moderator_reply"].reply_to == "user-msg-1"
        assert result["moderator_reply"].metadata["interjection_kind"] == "moderator_redirect"
        assert result["moderator_reply"].metadata["nominated_agent_id"] == "dev-1"
        assert result["nominated_reply"].reply_to == result["moderator_reply"].id
        assert result["nominated_reply"].metadata == {
            "interjection_kind": "nominated_reply",
            "prompted_by": "pm-1",
        }
        assert result["extra_replies"] == []
        assert result["moderator_resume"].metadata == {"interjection_kind": "revised_plan"}
        assert disc.plan["revision_reason"] == "用户要求补充验收标准"
        assert "## 执行计划" in disc.plan["content"]
        assert broadcasts[-2][1] == {"type": "plan_updated", "plan": disc.plan}
        assert broadcasts[-1][1] == {"type": "interjection_state", "state": "resumed"}
        assert saved == [plaza.id]

    def test_ensure_interjection_nomination_prefix_adds_missing_prefix(self, isolated_plaza_engine):
        plaza, _ = _seed_discussion(isolated_plaza_engine)
        chosen = isolated_plaza_engine.add_participant(
            plaza.id,
            "qa-1",
            "测试",
            "qa",
        )

        result = isolated_plaza_engine._ensure_interjection_nomination_prefix("请先补充验收。", chosen)

        assert result == "请 测试 先回应。请先补充验收。"

    def test_ensure_interjection_nomination_prefix_keeps_existing_prefix(self, isolated_plaza_engine):
        plaza, _ = _seed_discussion(isolated_plaza_engine)
        chosen = isolated_plaza_engine.add_participant(
            plaza.id,
            "qa-1",
            "测试",
            "qa",
        )

        result = isolated_plaza_engine._ensure_interjection_nomination_prefix(
            "请 测试 先回应。请补充验收。",
            chosen,
        )

        assert result == "请 测试 先回应。请补充验收。"

    def test_ensure_interjection_nomination_prefix_ignores_missing_choice(self, isolated_plaza_engine):
        assert isolated_plaza_engine._ensure_interjection_nomination_prefix("继续讨论。", None) == "继续讨论。"

    @pytest.mark.asyncio
    async def test_publish_interjection_moderator_redirect_uses_stable_metadata(
        self,
        isolated_plaza_engine,
        monkeypatch,
    ):
        plaza, disc = _seed_discussion(isolated_plaza_engine)
        disc.current_round = 2
        moderator = isolated_plaza_engine.add_participant(
            plaza.id,
            "pm-1",
            "主持人",
            "project_manager",
            niche_role=plaza_engine_module.NicheRole.MODERATOR,
        )
        chosen = isolated_plaza_engine.add_participant(
            plaza.id,
            "dev-1",
            "开发者",
            "developer",
        )
        published = []

        async def fake_publish_message(disc_arg, participant, content, **kwargs):
            published.append((disc_arg.id, participant.agent_id, content, kwargs))
            return PlazaMessage(
                discussion_id=disc_arg.id,
                agent_id=participant.agent_id,
                agent_name=participant.agent_name,
                content=content,
                round_number=kwargs["round_number"],
                reply_to=kwargs["reply_to"],
                metadata=kwargs["metadata"],
            )

        monkeypatch.setattr(isolated_plaza_engine, "publish_message", fake_publish_message)

        msg = await isolated_plaza_engine._publish_interjection_moderator_redirect(
            disc,
            moderator,
            "请 开发者 先回应。",
            "user-msg-1",
            chosen,
        )

        assert msg.reply_to == "user-msg-1"
        assert msg.metadata == {
            "interjection_kind": "moderator_redirect",
            "nominated_agent_id": "dev-1",
        }
        assert published[0][2] == "请 开发者 先回应。"
        assert published[0][3]["round_number"] == 2
        assert published[0][3]["niche_role"] == "moderator"

    @pytest.mark.asyncio
    async def test_publish_simulated_interjection_speaker_reply_uses_stable_metadata(
        self,
        isolated_plaza_engine,
        monkeypatch,
    ):
        plaza, disc = _seed_discussion(isolated_plaza_engine)
        disc.current_round = 3
        moderator = isolated_plaza_engine.add_participant(
            plaza.id,
            "pm-1",
            "主持人",
            "project_manager",
            niche_role=plaza_engine_module.NicheRole.MODERATOR,
        )
        chosen = isolated_plaza_engine.add_participant(
            plaza.id,
            "dev-1",
            "开发者",
            "developer",
        )
        moderator_msg = PlazaMessage(
            discussion_id=disc.id,
            agent_id="pm-1",
            agent_name="主持人",
            content="请开发者回应。",
            round_number=3,
        )
        published = []

        async def fake_publish_message(disc_arg, participant, content, **kwargs):
            published.append((disc_arg.id, participant.agent_id, content, kwargs))
            return PlazaMessage(
                discussion_id=disc_arg.id,
                agent_id=participant.agent_id,
                agent_name=participant.agent_name,
                content=content,
                round_number=kwargs["round_number"],
                reply_to=kwargs["reply_to"],
                metadata=kwargs["metadata"],
            )

        monkeypatch.setattr(isolated_plaza_engine, "publish_message", fake_publish_message)

        msg = await isolated_plaza_engine._publish_simulated_interjection_speaker_reply(
            disc,
            chosen,
            moderator,
            "用户提出了一个很长的问题，需要限制模拟回复中引用的长度，避免内容过长影响消息展示。",
            moderator_msg,
        )

        assert msg.reply_to == moderator_msg.id
        assert msg.metadata == {
            "interjection_kind": "nominated_reply",
            "prompted_by": "pm-1",
        }
        assert published[0][2].startswith("我先回应这个插话：用户提出了一个很长的问题")
        assert "当前更关键的是把它落到本轮的约束与方案上。" in published[0][2]
        assert published[0][3]["round_number"] == 3
        assert published[0][3]["niche_role"] == chosen.niche_role.value

    @pytest.mark.asyncio
    async def test_generate_interjection_nominated_reply_sets_link_metadata(
        self,
        isolated_plaza_engine,
        monkeypatch,
    ):
        plaza, disc = _seed_discussion(isolated_plaza_engine)
        disc.current_round = 3
        moderator = isolated_plaza_engine.add_participant(
            plaza.id,
            "pm-1",
            "主持人",
            "project_manager",
            niche_role=plaza_engine_module.NicheRole.MODERATOR,
        )
        chosen = isolated_plaza_engine.add_participant(
            plaza.id,
            "qa-1",
            "测试",
            "qa",
        )
        moderator_msg = PlazaMessage(
            discussion_id=disc.id,
            agent_id="pm-1",
            agent_name="主持人",
            content="请测试回应。",
            round_number=3,
        )
        calls = []

        async def fake_agent_speak(disc_arg, participant, prompt, round_number, niche_role):
            calls.append((disc_arg.id, participant.agent_id, prompt, round_number, niche_role))
            return PlazaMessage(
                discussion_id=disc_arg.id,
                agent_id=participant.agent_id,
                agent_name=participant.agent_name,
                content="补充验收标准。",
                round_number=round_number,
            )

        monkeypatch.setattr(isolated_plaza_engine, "_agent_speak", fake_agent_speak)

        msg = await isolated_plaza_engine._generate_interjection_nominated_reply(
            disc,
            chosen,
            "请直接回应用户问题。",
            moderator,
            moderator_msg,
        )

        assert msg.reply_to == moderator_msg.id
        assert msg.metadata == {
            "interjection_kind": "nominated_reply",
            "prompted_by": "pm-1",
        }
        assert calls == [(disc.id, "qa-1", "请直接回应用户问题。", 3, chosen.niche_role.value)]

    @pytest.mark.asyncio
    async def test_generate_interjection_supplementary_reply_sets_link_metadata(
        self,
        isolated_plaza_engine,
        monkeypatch,
    ):
        plaza, disc = _seed_discussion(isolated_plaza_engine)
        disc.current_round = 3
        moderator = isolated_plaza_engine.add_participant(
            plaza.id,
            "pm-1",
            "主持人",
            "project_manager",
            niche_role=plaza_engine_module.NicheRole.MODERATOR,
        )
        extra_speaker = isolated_plaza_engine.add_participant(
            plaza.id,
            "dev-1",
            "开发者",
            "developer",
        )
        moderator_msg = PlazaMessage(
            discussion_id=disc.id,
            agent_id="pm-1",
            agent_name="主持人",
            content="请测试回应。",
            round_number=3,
        )
        speaker_msg = PlazaMessage(
            discussion_id=disc.id,
            agent_id="qa-1",
            agent_name="测试",
            content="先补验收。",
            round_number=3,
        )
        calls = []

        async def fake_agent_speak(disc_arg, participant, prompt, round_number, niche_role):
            calls.append((disc_arg.id, participant.agent_id, prompt, round_number, niche_role))
            return PlazaMessage(
                discussion_id=disc_arg.id,
                agent_id=participant.agent_id,
                agent_name=participant.agent_name,
                content="补充实现约束。",
                round_number=round_number,
            )

        monkeypatch.setattr(isolated_plaza_engine, "_agent_speak", fake_agent_speak)

        msg = await isolated_plaza_engine._generate_interjection_supplementary_reply(
            disc,
            extra_speaker,
            "请补充工程约束。",
            moderator,
            speaker_msg,
            moderator_msg,
        )

        assert msg.reply_to == speaker_msg.id
        assert msg.metadata == {
            "interjection_kind": "supplementary_reply",
            "prompted_by": "pm-1",
        }
        assert calls == [(disc.id, "dev-1", "请补充工程约束。", 3, extra_speaker.niche_role.value)]

    @pytest.mark.asyncio
    async def test_handle_llm_interjection_orchestrates_replies_and_plan(
        self,
        isolated_plaza_engine,
        monkeypatch,
    ):
        plaza, disc = _seed_discussion(isolated_plaza_engine)
        disc.current_round = 3
        moderator = isolated_plaza_engine.add_participant(
            plaza.id,
            "pm-1",
            "主持人",
            "project_manager",
            niche_role=plaza_engine_module.NicheRole.MODERATOR,
        )
        chosen = isolated_plaza_engine.add_participant(
            plaza.id,
            "qa-1",
            "测试",
            "qa",
        )
        extra = isolated_plaza_engine.add_participant(
            plaza.id,
            "dev-1",
            "开发者",
            "developer",
        )
        generated_prompts = []
        plan_updates = []

        async def fake_generate_agent_content(participant, prompt, **kwargs):
            generated_prompts.append((participant.agent_id, prompt, kwargs))
            if len(generated_prompts) == 1:
                return "REPLY: 请测试先回应用户验收问题。\nNEXT: qa-1"
            return _build_plan_text()

        async def fake_generate_nominated_reply(disc_arg, chosen_arg, prompt, moderator_arg, moderator_msg):
            return PlazaMessage(
                discussion_id=disc_arg.id,
                agent_id=chosen_arg.agent_id,
                agent_name=chosen_arg.agent_name,
                content="需要加入回归测试。",
                round_number=disc_arg.current_round,
                reply_to=moderator_msg.id,
                metadata={"interjection_kind": "nominated_reply", "prompted_by": moderator_arg.agent_id},
            )

        async def fake_generate_supplementary_reply(
            disc_arg,
            extra_speaker,
            prompt,
            moderator_arg,
            speaker_msg,
            moderator_msg,
        ):
            return PlazaMessage(
                discussion_id=disc_arg.id,
                agent_id=extra_speaker.agent_id,
                agent_name=extra_speaker.agent_name,
                content="实现前先拆接口边界。",
                round_number=disc_arg.current_round,
                reply_to=speaker_msg.id,
                metadata={"interjection_kind": "supplementary_reply", "prompted_by": moderator_arg.agent_id},
            )

        async def fake_publish_plan_update(plaza_arg, disc_arg, moderator_arg, plan_text, reason, reply_to):
            plan_updates.append((plaza_arg.id, disc_arg.id, moderator_arg.agent_id, plan_text, reason, reply_to))
            return PlazaMessage(
                discussion_id=disc_arg.id,
                agent_id=moderator_arg.agent_id,
                agent_name=moderator_arg.agent_name,
                content=plan_text,
                round_number=disc_arg.current_round,
                reply_to=reply_to,
                metadata={"interjection_kind": "revised_plan"},
            )

        monkeypatch.setattr(isolated_plaza_engine, "_generate_agent_content", fake_generate_agent_content)
        monkeypatch.setattr(isolated_plaza_engine, "_generate_interjection_nominated_reply", fake_generate_nominated_reply)
        monkeypatch.setattr(isolated_plaza_engine, "_generate_interjection_supplementary_reply", fake_generate_supplementary_reply)
        monkeypatch.setattr(isolated_plaza_engine, "_publish_interjection_plan_update", fake_publish_plan_update)

        result = await isolated_plaza_engine._handle_llm_interjection(
            plaza,
            disc,
            moderator,
            [chosen, extra],
            "用户要求补充验收标准",
            "user-msg-1",
            plaza.id,
            disc.id,
        )

        assert result["moderator_reply"].reply_to == "user-msg-1"
        assert result["moderator_reply"].metadata["nominated_agent_id"] == "qa-1"
        assert result["nominated_reply"].agent_id == "qa-1"
        assert [msg.agent_id for msg in result["extra_replies"]] == ["dev-1"]
        assert result["moderator_resume"].metadata == {"interjection_kind": "revised_plan"}
        assert plan_updates[0][4] == "用户要求补充验收标准"
        assert plan_updates[0][5] == result["extra_replies"][-1].id
        assert len(generated_prompts) == 2

    def test_build_regenerate_plan_prompt_uses_recent_context_and_plan(self, isolated_plaza_engine):
        _, disc = _seed_discussion(isolated_plaza_engine)
        disc.goal = "重新生成计划"
        for index in range(35):
            disc.messages.append(
                PlazaMessage(
                    discussion_id=disc.id,
                    agent_id=f"agent-{index}",
                    agent_name=f"成员{index}",
                    content=f"观点{index}-" + ("x" * 240),
                    round_number=index,
                )
            )

        prompt = isolated_plaza_engine._build_regenerate_plan_prompt(disc)

        assert "讨论话题: 「让 Plaza 真的能派发任务」" in prompt
        assert "讨论目标: 重新生成计划" in prompt
        assert "[成员5] 观点5-" in prompt
        assert "[成员4]" not in prompt
        assert "观点34-" in prompt
        assert "x" * 201 not in prompt
        assert '"revision": 3' in prompt
        assert "| 序号 | 任务 | 负责角色 | 优先级 | 依赖 | 预期产出 |" in prompt
        assert "只输出以上内容，不要客套。" in prompt

    def test_resolve_regenerate_plan_moderator_prefers_discussion_moderator(self, isolated_plaza_engine):
        plaza, disc = _seed_discussion(isolated_plaza_engine)
        explicit = isolated_plaza_engine.add_participant(
            plaza.id,
            "pm-explicit",
            "显式主持",
            "project_manager",
        )
        isolated_plaza_engine.add_participant(
            plaza.id,
            "pm-niche",
            "壁龛主持",
            "project_manager",
            niche_role=plaza_engine_module.NicheRole.MODERATOR,
        )
        disc.moderator_agent_id = "pm-explicit"

        assert isolated_plaza_engine._resolve_regenerate_plan_moderator(plaza, disc) is explicit

    def test_resolve_regenerate_plan_moderator_falls_back_to_niche(self, isolated_plaza_engine):
        plaza, disc = _seed_discussion(isolated_plaza_engine)
        niche = isolated_plaza_engine.add_participant(
            plaza.id,
            "pm-niche",
            "壁龛主持",
            "project_manager",
            niche_role=plaza_engine_module.NicheRole.MODERATOR,
        )

        assert isolated_plaza_engine._resolve_regenerate_plan_moderator(plaza, disc) is niche

    def test_build_regenerate_plan_fallback_returns_actionable_plan(self, isolated_plaza_engine):
        plaza, disc = _seed_discussion(isolated_plaza_engine)
        isolated_plaza_engine.add_participant(
            plaza.id,
            "dev-1",
            "开发者",
            "developer",
        )

        plan_text = isolated_plaza_engine._build_regenerate_plan_fallback(plaza, disc)

        assert isolated_plaza_engine._has_actionable_plan(plan_text)
        assert "刷新计划时 LLM 不可用或未返回结构化计划" in plan_text
        assert "| 序号 | 任务 | 负责角色 | 优先级 | 依赖 | 预期产出 |" in plan_text

    @pytest.mark.asyncio
    async def test_publish_regenerated_plan_updates_message_broadcast_and_save(
        self,
        isolated_plaza_engine,
        monkeypatch,
    ):
        plaza, disc = _seed_discussion(isolated_plaza_engine)
        moderator = isolated_plaza_engine.add_participant(
            plaza.id,
            "pm-1",
            "议事长",
            "project_manager",
            niche_role=plaza_engine_module.NicheRole.MODERATOR,
        )
        events = isolated_plaza_engine.subscribe(disc.id)
        saved_plazas = []
        monkeypatch.setattr(
            isolated_plaza_engine._store,
            "save_plaza",
            lambda saved: saved_plazas.append(saved.id),
        )

        result = await isolated_plaza_engine._publish_regenerated_plan(
            plaza,
            disc,
            moderator,
            _build_plan_text(),
        )

        message_event = await events.get()
        plan_event = await events.get()

        assert result["status"] == "refreshed"
        assert result["plan"] is disc.plan
        assert result["message"] is disc.messages[-1]
        assert disc.plan["revision"] == 4
        assert disc.plan["revision_reason"] == "用户请求刷新执行计划"
        assert disc.plan["content"] == _build_plan_text()
        assert result["message"].niche_role == "moderator"
        assert result["message"].metadata == {"interjection_kind": "revised_plan"}
        assert message_event["type"] == "message"
        assert message_event["message"]["metadata"] == {"interjection_kind": "revised_plan"}
        assert plan_event == {"type": "plan_updated", "plan": disc.plan}
        assert saved_plazas == [plaza.id]

    @pytest.mark.asyncio
    async def test_publish_simulated_opening_appends_moderator_message_and_broadcasts(
        self,
        isolated_plaza_engine,
    ):
        plaza, disc = _seed_discussion(isolated_plaza_engine)
        moderator = isolated_plaza_engine.add_participant(
            plaza.id,
            "pm-1",
            "议事长",
            "project_manager",
            niche_role=plaza_engine_module.NicheRole.MODERATOR,
        )
        events = isolated_plaza_engine.subscribe(disc.id)

        msg = await isolated_plaza_engine._publish_simulated_opening(disc, moderator)
        event = await events.get()

        assert msg is disc.messages[-1]
        assert msg.seq == 0
        assert msg.agent_id == "pm-1"
        assert msg.niche_role == "moderator"
        assert msg.round_number == 0
        assert msg.content == "欢迎各位参与「让 Plaza 真的能派发任务」的讨论。让我们开始吧。"
        assert event["type"] == "message"
        assert event["message"] == msg.to_dict()

    @pytest.mark.asyncio
    async def test_publish_simulated_round_message_uses_fallback_content_and_broadcasts(
        self,
        isolated_plaza_engine,
    ):
        plaza, disc = _seed_discussion(isolated_plaza_engine)
        speaker = isolated_plaza_engine.add_participant(
            plaza.id,
            "dev-1",
            "开发者",
            "developer",
        )
        events = isolated_plaza_engine.subscribe(disc.id)

        msg = await isolated_plaza_engine._publish_simulated_round_message(disc, speaker, 2)
        event = await events.get()

        assert msg is disc.messages[-1]
        assert msg.seq == 0
        assert msg.agent_id == "dev-1"
        assert msg.agent_name == "开发者"
        assert msg.role == "developer"
        assert msg.niche_role == speaker.niche_role.value
        assert msg.round_number == 2
        assert "围绕「本次讨论」" in msg.content
        assert event["type"] == "message"
        assert event["message"] == msg.to_dict()

    @pytest.mark.asyncio
    async def test_run_simulated_round_broadcasts_start_and_speaker_messages(
        self,
        isolated_plaza_engine,
        monkeypatch,
    ):
        plaza, disc = _seed_discussion(isolated_plaza_engine)
        speakers = [
            isolated_plaza_engine.add_participant(plaza.id, "dev-1", "开发者", "developer"),
            isolated_plaza_engine.add_participant(plaza.id, "qa-1", "测试", "qa"),
        ]
        events = isolated_plaza_engine.subscribe(disc.id)
        sleeps = []

        async def fake_sleep(seconds):
            sleeps.append(seconds)

        monkeypatch.setattr(plaza_engine_module.asyncio, "sleep", fake_sleep)

        await isolated_plaza_engine._run_simulated_round(disc, speakers, 2)
        round_event = await events.get()
        first_message = await events.get()
        second_message = await events.get()

        assert disc.current_round == 2
        assert round_event == {"type": "round_start", "round": 2, "max_rounds": disc.max_rounds}
        assert [message.agent_id for message in disc.messages] == ["dev-1", "qa-1"]
        assert [message.round_number for message in disc.messages] == [2, 2]
        assert first_message["type"] == "message"
        assert first_message["message"]["agent_id"] == "dev-1"
        assert second_message["type"] == "message"
        assert second_message["message"]["agent_id"] == "qa-1"
        assert sleeps == [0.1, 0.1]

    @pytest.mark.asyncio
    async def test_complete_simulated_discussion_updates_plan_and_end_events(
        self,
        isolated_plaza_engine,
    ):
        plaza, disc = _seed_discussion(isolated_plaza_engine)
        moderator = isolated_plaza_engine.add_participant(
            plaza.id,
            "pm-1",
            "议事长",
            "project_manager",
            niche_role=plaza_engine_module.NicheRole.MODERATOR,
        )
        speaker = isolated_plaza_engine.add_participant(
            plaza.id,
            "dev-1",
            "开发者",
            "developer",
        )
        events = isolated_plaza_engine.subscribe(disc.id)

        await isolated_plaza_engine._complete_simulated_discussion(disc, moderator, [speaker])
        plan_event = await events.get()
        end_event = await events.get()

        assert isolated_plaza_engine._has_actionable_plan(disc.summary)
        assert disc.key_conclusions == [
            "围绕「让 Plaza 真的能派发任务」明确目标与关键约束",
            "分步推进方案设计、验证与执行",
            "演练通过后再进入实际派发",
        ]
        assert disc.plan["revision"] == 4
        assert disc.plan["revision_reason"] == "模拟模式自动生成"
        assert disc.plan["content"] == disc.summary
        assert disc.status == DiscussionStatus.CLOSED
        assert disc.ended_at
        assert plan_event == {"type": "plan_updated", "plan": disc.plan}
        assert end_event == {"type": "discussion_end", "summary": disc.summary}
