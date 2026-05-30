# -*- coding: utf-8 -*-
"""Plaza to evolution bridge tests."""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

import agent_team_api as agent_team_api_module
from agents import api as api_module
from agents import plaza_engine as plaza_engine_module
from agents import task_engine as task_engine_module
from channels.system_evolution import (
    EvolutionItem,
    EvolutionStatus,
    SystemEvolutionChannel,
)
from agents.plaza_engine import PlazaEngine
from agents.plaza_routes import (
    EvolveRequest,
    evolve_from_discussion,
    get_discussion_verification_alerts,
    get_discussion_verification_queue,
)
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
        engine = TaskEngine(store=TaskStore(base_dir=Path(tmpdir) / "tasks"))
        monkeypatch.setattr(task_engine_module, "_engine", engine)
        yield engine


def _seed_discussion(engine: PlazaEngine):
    plaza = engine.create_plaza("演化广场", "evolution")
    disc = engine.create_discussion(plaza.id, "让 Plaza 接进 Evolution", "evolution", "", 3)
    disc.plan = {
        "revision": 2,
        "revision_reason": "测试演化桥接",
        "revised_at": "2026-05-29T00:00:00+00:00",
        "content": (
            "## 执行计划\n"
            "| 序号 | 任务 | 负责角色 | 优先级 | 依赖 | 预期产出 |\n"
            "|---|---|---|---|---|---|\n"
            "| 1 | 打通演化派发 | developer | P0 | 无 | 任务桥接补丁 |\n"
            "| 2 | 补充桥接测试 | qa | P1 | 1 | 回归测试报告 |\n"
        ),
    }
    engine._store.save_plaza(plaza)
    return plaza, disc


class TestEvolutionCycleGuards:
    def test_run_evolution_cycle_does_not_auto_verify_dispatched_items(self):
        channel = SystemEvolutionChannel()
        channel.initialize()
        channel.audit_rules = []

        item = EvolutionItem(
            id="ev-dispatch-only",
            title="仅派发",
            description="不应自动进入验证",
        )
        channel.evolution_items[item.id] = item

        result = channel.run_evolution_cycle()

        assert result["dispatch"]["count"] == 1
        assert result["verify"]["count"] == 0
        assert channel.evolution_items[item.id].status == EvolutionStatus.DISPATCHED.value

    def test_mark_build_complete_requires_artifacts(self):
        channel = SystemEvolutionChannel()
        channel.initialize()

        item = EvolutionItem(
            id="ev-build-guard",
            title="需要真实产物",
            description="无产物不允许进入验证",
            status=EvolutionStatus.IN_PROGRESS.value,
        )
        channel.evolution_items[item.id] = item

        assert channel.mark_build_complete(item.id) is False
        assert channel.evolution_items[item.id].status == EvolutionStatus.IN_PROGRESS.value

        assert channel.mark_build_complete(item.id, code_changes=["src/backend/main.py"]) is True
        assert channel.evolution_items[item.id].status == EvolutionStatus.VERIFY_PENDING.value


class TestPlazaEvolutionBridge:
    @pytest.mark.asyncio
    async def test_evolve_from_discussion_creates_traceable_items(
        self,
        isolated_plaza_engine,
        isolated_task_engine,
        monkeypatch,
    ):
        plaza, disc = _seed_discussion(isolated_plaza_engine)
        evolution_engine = SystemEvolutionChannel()
        evolution_engine.initialize()
        evolution_engine.audit_rules = []
        monkeypatch.setattr(agent_team_api_module, "_evolution_engine", evolution_engine)

        created_tasks = []

        async def fake_submit_internal_task(team_id: str, **kwargs):
            task = AgentTask(
                task_id=f"plaza-task-{len(created_tasks) + 1}",
                team_id=team_id,
                title=kwargs["title"],
                description=kwargs["description"],
                priority=kwargs["priority"],
                metadata=kwargs["metadata"],
            )
            created_tasks.append(task)
            await isolated_task_engine.submit_task(task)
            return task

        monkeypatch.setattr(api_module, "_submit_internal_task", fake_submit_internal_task)

        result = await evolve_from_discussion(plaza.id, disc.id, EvolveRequest(team_id="team-build"))

        assert result["status"] == "evolving"
        assert result["task_count"] == 2
        assert len(result["items"]) == 2

        for item in result["items"]:
            assert item["source_discussion_id"] == disc.id
            assert item["source_task_ids"] == ["plaza-task-1", "plaza-task-2"]
            assert item["trace_context"]["discussion_id"] == disc.id

        stored_items = list(evolution_engine.evolution_items.values())
        assert len(stored_items) == 2
        assert all(item.source_plaza_id == plaza.id for item in stored_items)
        assert all(item.source_discussion_id == disc.id for item in stored_items)
        assert all(item.source_task_ids == ["plaza-task-1", "plaza-task-2"] for item in stored_items)
        assert all(item.status == EvolutionStatus.DISPATCHED.value for item in stored_items)
        assert all(item.trace_context["plaza_id"] == plaza.id for item in stored_items)

        for task in result["tasks"]:
            metadata = task["metadata"]
            assert len(metadata["evolution_item_ids"]) == 2
            assert metadata["trace_context"]["task_id"] == task["task_id"]
            assert metadata["trace_context"]["evolution_item_ids"] == metadata["evolution_item_ids"]

        linked_task = isolated_task_engine.get_task("plaza-task-1")
        assert linked_task is not None
        assert len(linked_task.metadata["evolution_item_ids"]) == 2

    @pytest.mark.asyncio
    async def test_discussion_verification_queue_surfaces_manual_verify_items(
        self,
        isolated_plaza_engine,
        monkeypatch,
    ):
        plaza, disc = _seed_discussion(isolated_plaza_engine)
        evolution_engine = SystemEvolutionChannel()
        evolution_engine.initialize()
        evolution_engine.evolution_items["evo-manual"] = EvolutionItem(
            id="evo-manual",
            title="人工验证项",
            status=EvolutionStatus.VERIFY_PENDING.value,
            verify_test_name="manual-check",
            verify_result="pending",
            verify_detail="Awaiting verify test: manual-check",
            source_plaza_id=plaza.id,
            source_discussion_id=disc.id,
            source_task_ids=["plaza-task-1"],
        )
        evolution_engine.evolution_items["evo-other"] = EvolutionItem(
            id="evo-other",
            title="其他讨论",
            status=EvolutionStatus.VERIFY_PENDING.value,
            verify_test_name="other-check",
            source_plaza_id=plaza.id,
            source_discussion_id="other-disc",
            source_task_ids=["task-x"],
        )
        monkeypatch.setattr(agent_team_api_module, "_evolution_engine", evolution_engine)

        payload = await get_discussion_verification_queue(plaza.id, disc.id)

        assert payload["count"] == 1
        assert payload["items"][0]["id"] == "evo-manual"
        assert payload["items"][0]["requires_manual_verify"] is True
        assert payload["items"][0]["verify_detail"] == "Awaiting verify test: manual-check"

    @pytest.mark.asyncio
    async def test_discussion_verification_alerts_surface_retry_and_manual_verify(
        self,
        isolated_plaza_engine,
        monkeypatch,
    ):
        plaza, disc = _seed_discussion(isolated_plaza_engine)
        evolution_engine = SystemEvolutionChannel()
        evolution_engine.initialize()
        evolution_engine.evolution_items["evo-manual"] = EvolutionItem(
            id="evo-manual",
            title="人工验证项",
            status=EvolutionStatus.VERIFY_PENDING.value,
            verify_test_name="manual-check",
            verify_result="pending",
            verify_detail="Awaiting verify test: manual-check",
            source_plaza_id=plaza.id,
            source_discussion_id=disc.id,
        )
        evolution_engine.evolution_items["evo-retry"] = EvolutionItem(
            id="evo-retry",
            title="重试项",
            status=EvolutionStatus.DISPATCHED.value,
            verify_result="failed",
            verify_detail="回归失败 (retry queued 1/3)",
            retry_count=1,
            source_plaza_id=plaza.id,
            source_discussion_id=disc.id,
        )
        monkeypatch.setattr(agent_team_api_module, "_evolution_engine", evolution_engine)

        payload = await get_discussion_verification_alerts(plaza.id, disc.id)

        assert payload["count"] == 2
        assert payload["alerts"][0]["item_id"] == "evo-manual"
        assert payload["alerts"][0]["alert_level"] == "warning"
        assert payload["alerts"][0]["next_action"] == "run_verify_test:manual-check"
        assert payload["alerts"][1]["item_id"] == "evo-retry"
        assert payload["alerts"][1]["next_action"] == "redispatch_build"
