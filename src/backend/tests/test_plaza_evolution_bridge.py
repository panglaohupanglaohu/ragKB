# -*- coding: utf-8 -*-
"""Plaza to evolution bridge tests."""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

import agent_team_api as agent_team_api_module
from agents import api as api_module
from agents import plaza_engine as plaza_engine_module
from channels.system_evolution import (
    EvolutionItem,
    EvolutionStatus,
    SystemEvolutionChannel,
)
from agents.plaza_engine import PlazaEngine
from agents.plaza_routes import EvolveRequest, evolve_from_discussion
from agents.plaza_store import PlazaStore
from agents.task_engine import AgentTask


@pytest.fixture
def isolated_plaza_engine(monkeypatch):
    with TemporaryDirectory() as tmpdir:
        engine = PlazaEngine()
        engine._store = PlazaStore(base_dir=Path(tmpdir))
        engine._plazas = {}
        monkeypatch.setattr(plaza_engine_module, "_engine", engine)
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
    async def test_evolve_from_discussion_creates_traceable_items(self, isolated_plaza_engine, monkeypatch):
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
            return task

        monkeypatch.setattr(api_module, "_submit_internal_task", fake_submit_internal_task)

        result = await evolve_from_discussion(plaza.id, disc.id, EvolveRequest(team_id="team-build"))

        assert result["status"] == "evolving"
        assert result["task_count"] == 2
        assert len(result["items"]) == 2

        for item in result["items"]:
            assert item["source_discussion_id"] == disc.id
            assert item["source_task_ids"] == ["plaza-task-1", "plaza-task-2"]

        stored_items = list(evolution_engine.evolution_items.values())
        assert len(stored_items) == 2
        assert all(item.source_plaza_id == plaza.id for item in stored_items)
        assert all(item.source_discussion_id == disc.id for item in stored_items)
        assert all(item.source_task_ids == ["plaza-task-1", "plaza-task-2"] for item in stored_items)
        assert all(item.status == EvolutionStatus.DISPATCHED.value for item in stored_items)
