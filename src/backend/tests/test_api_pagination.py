# -*- coding: utf-8 -*-
"""Pagination regressions for agent-config list endpoints."""

from __future__ import annotations

from pathlib import Path

import pytest

from agents import api as api_module
from agents.models import AgentProfile, ModelConfig
from agents.skill_library import init_skill_library
from agents.skill_registry import SkillRegistry
from agents.task_engine import AgentTask, TaskEngine
from agents.task_store import TaskStore
from agents.team_manager import TeamManager
from agents.team_store import TeamStore
from agents.tool_registry import ToolRegistry


@pytest.fixture
def paginated_api_state(monkeypatch, tmp_path):
    store = TeamStore(path=tmp_path / "teams.json")
    team_manager = TeamManager(store=store)

    tool_registry = ToolRegistry()
    tool_registry.load_defaults()

    skill_registry = SkillRegistry()
    skill_registry.load_defaults()
    init_skill_library(team_manager=team_manager, skill_registry=skill_registry)

    monkeypatch.setattr(api_module, "_team_manager", team_manager)
    monkeypatch.setattr(api_module, "_tool_registry", tool_registry)
    monkeypatch.setattr(api_module, "_skill_registry", skill_registry)
    monkeypatch.setattr(api_module, "_sessions", {})
    monkeypatch.setattr(api_module, "_delegated_tasks", [])

    task_engine = TaskEngine(store=TaskStore(base_dir=Path(tmp_path) / "tasks"))
    monkeypatch.setattr(api_module, "get_task_engine", lambda: task_engine)

    team = team_manager.create_team(name="分页测试团队", team_id="team-page")
    for index in range(5):
        team.add_agent(
            AgentProfile(
                agent_id=f"agent-{index}",
                name=f"Agent {index}",
                role="developer",
            )
        )
    team.add_model(
        ModelConfig(
            model_id="model-a",
            provider="openai",
            name="gpt-test",
            max_tokens=4096,
            temperature=0.2,
        )
    )
    team.add_model(
        ModelConfig(
            model_id="model-b",
            provider="deepseek",
            name="deepseek-chat",
            max_tokens=8192,
            temperature=0.7,
        )
    )
    for tool in tool_registry.list_all()[:5]:
        team.add_tool(tool)
    for skill in skill_registry.list_all()[:4]:
        team.add_skill(skill)
    team_manager._persist()

    for index in range(4):
        task = AgentTask(
            task_id=f"task-{index}",
            agent_id="agent-0",
            team_id=team.team_id,
            title=f"Task {index}",
            description="pagination test",
            priority=2,
        )
        task_engine._tasks[task.task_id] = task
        task_engine._store.save_task(task)

    api_module._sessions.update(
        {
            f"session-{index}": {
                "session_id": f"session-{index}",
                "agent_id": "agent-0",
                "team_id": team.team_id,
            }
            for index in range(4)
        }
    )
    api_module._delegated_tasks.extend(
        {
            "task_id": f"delegation-{index}",
            "team_id": team.team_id,
            "status": "queued",
            "priority": 2,
        }
        for index in range(4)
    )

    return team_manager, team, task_engine


class TestApiPagination:
    def test_list_all_tools_supports_offset_without_explicit_limit(self, paginated_api_state):
        payload = api_module.list_all_tools(limit=0, offset=1)

        assert payload["offset"] == 1
        assert payload["limit"] == 50
        assert payload["total"] >= 2
        assert len(payload["items"]) >= 1

    def test_list_team_models_returns_paginated_envelope(self, paginated_api_state):
        _, team, _ = paginated_api_state

        payload = api_module.list_models(team.team_id, limit=1, offset=1)

        assert payload["total"] == 2
        assert payload["limit"] == 1
        assert payload["offset"] == 1
        assert len(payload["items"]) == 1

    def test_list_team_agents_returns_paginated_envelope(self, paginated_api_state):
        _, team, _ = paginated_api_state

        payload = api_module.list_agents(team.team_id, limit=2, offset=2)

        assert payload["total"] == 5
        assert payload["limit"] == 2
        assert payload["offset"] == 2
        assert len(payload["items"]) == 2

    def test_list_agent_sessions_returns_paginated_envelope(self, paginated_api_state):
        _, team, _ = paginated_api_state

        payload = api_module.list_agent_sessions(team.team_id, "agent-0", limit=2, offset=1)

        assert payload["total"] == 4
        assert payload["limit"] == 2
        assert payload["offset"] == 1
        assert len(payload["items"]) == 2

    def test_list_team_tasks_returns_paginated_envelope(self, paginated_api_state):
        _, team, _ = paginated_api_state

        payload = api_module.list_team_tasks(team.team_id, limit=2, offset=1)

        assert payload["total"] == 4
        assert payload["limit"] == 2
        assert payload["offset"] == 1
        assert len(payload["items"]) == 2

    def test_list_team_delegations_returns_paginated_envelope(self, paginated_api_state):
        _, team, _ = paginated_api_state

        payload = api_module.list_team_delegations(team.team_id, limit=2, offset=1)

        assert payload["total"] == 4
        assert payload["limit"] == 2
        assert payload["offset"] == 1
        assert len(payload["items"]) == 2
