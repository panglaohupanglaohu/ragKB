# -*- coding: utf-8 -*-
"""团队管理器单元测试 — TeamManager CRUD 操作."""

from __future__ import annotations

import pytest

from agents.models import (
    AgentProfile,
    AgentTeam,
    ModelConfig,
)


class TestTeamManagerCreate:
    """TeamManager 创建操作测试."""

    def test_create_team(self, team_manager):
        team = team_manager.create_team(
            name="测试团队",
            team_id="team-001",
            description="自动化测试",
        )
        assert team is not None
        assert team.team_id == "team-001"
        assert team.name == "测试团队"
        assert team.description == "自动化测试"

    def test_create_duplicate_team_raises(self, team_manager):
        team_manager.create_team(name="A", team_id="team-001")
        with pytest.raises(ValueError):
            team_manager.create_team(name="B", team_id="team-001")


class TestTeamManagerRead:
    """TeamManager 读取操作测试."""

    def test_get_team(self, team_manager):
        team_manager.create_team(name="T1", team_id="t1")
        team = team_manager.get_team("t1")
        assert team is not None
        assert team.name == "T1"

    def test_get_nonexistent_team(self, team_manager):
        team = team_manager.get_team("nonexistent")
        assert team is None

    def test_list_teams(self, team_manager):
        team_manager.create_team(name="T1", team_id="t1")
        team_manager.create_team(name="T2", team_id="t2")
        teams = team_manager.list_teams()
        assert len(teams) == 2
        names = {t.name for t in teams}
        assert names == {"T1", "T2"}


class TestTeamManagerUpdate:
    """TeamManager 更新操作测试."""

    def test_update_team(self, team_manager):
        team_manager.create_team(name="Old", team_id="t1")
        updated = team_manager.update_team("t1", name="New", description="Updated")
        assert updated is not None
        assert updated.name == "New"
        assert updated.description == "Updated"

    def test_update_team_ignores_immutable(self, team_manager):
        team_manager.create_team(name="OK", team_id="t1")
        # team_id 不在 AgentTeam dataclass 中当作可变字段
        updated = team_manager.update_team("t1", name="StillOK")
        assert updated is not None
        assert updated.team_id == "t1"  # team_id 不可变

    def test_update_nonexistent_team(self, team_manager):
        result = team_manager.update_team("noop", name="X")
        assert result is None


class TestTeamManagerDelete:
    """TeamManager 删除操作测试."""

    def test_delete_team(self, team_manager):
        team_manager.create_team(name="T1", team_id="t1")
        deleted = team_manager.delete_team("t1")
        assert deleted is not None
        assert team_manager.get_team("t1") is None

    def test_delete_nonexistent_team(self, team_manager):
        result = team_manager.delete_team("noop")
        assert result is None


class TestAgentManagement:
    """Agent 管理操作测试."""

    def test_add_agent(self, team_manager, sample_agent_dict):
        team_manager.create_team(name="T1", team_id="t1")
        agent = AgentProfile(
            agent_id="agent-001",
            name="TestAgent",
            role="developer",
            state="idle",
        )
        result = team_manager.add_agent_to_team("t1", agent)
        assert result is True

    def test_get_agent(self, team_manager):
        team_manager.create_team(name="T1", team_id="t1")
        agent = AgentProfile(agent_id="a1", name="A1", role="developer")
        team_manager.add_agent_to_team("t1", agent)

        found = team_manager.get_agent("t1", "a1")
        assert found is not None
        assert found.name == "A1"

    def test_get_agent_nonexistent_team(self, team_manager):
        result = team_manager.get_agent("no-team", "any-agent")
        assert result is None

    def test_list_agents(self, team_manager):
        team_manager.create_team(name="T1", team_id="t1")
        team_manager.add_agent_to_team("t1", AgentProfile(agent_id="a1", name="A1", role="dev"))
        team_manager.add_agent_to_team("t1", AgentProfile(agent_id="a2", name="A2", role="qa"))

        agents = team_manager.list_agents("t1")
        assert len(agents) == 2

    def test_list_agents_empty_team(self, team_manager):
        team_manager.create_team(name="T1", team_id="t1")
        agents = team_manager.list_agents("t1")
        assert agents == []

    def test_list_agents_nonexistent_team(self, team_manager):
        agents = team_manager.list_agents("no-team")
        assert agents == []

    def test_remove_agent(self, team_manager):
        team_manager.create_team(name="T1", team_id="t1")
        agent = AgentProfile(agent_id="a1", name="A1", role="developer")
        team_manager.add_agent_to_team("t1", agent)

        removed = team_manager.remove_agent_from_team("t1", "a1")
        assert removed is not None
        assert removed.name == "A1"
        assert team_manager.get_agent("t1", "a1") is None


class TestModelManagement:
    """Model 管理操作测试."""

    def test_add_model(self, team_manager, sample_model_dict):
        team_manager.create_team(name="T1", team_id="t1")
        model = ModelConfig(
            model_id="model-001",
            name="deepseek-v4",
            provider="deepseek",
        )
        result = team_manager.add_model_to_team("t1", model)
        assert result is True

    def test_add_model_to_nonexistent_team(self, team_manager):
        model = ModelConfig(model_id="m1", name="M1", provider="openai")
        result = team_manager.add_model_to_team("no-team", model)
        assert result is False

    def test_remove_model(self, team_manager):
        team_manager.create_team(name="T1", team_id="t1")
        model = ModelConfig(model_id="m1", name="M1", provider="deepseek")
        team_manager.add_model_to_team("t1", model)

        removed = team_manager.remove_model_from_team("t1", "m1")
        assert removed is not None
        assert removed.name == "M1"


class TestTeamOverview:
    """Team overview 操作测试."""

    def test_get_team_overview(self, team_manager):
        team_manager.create_team(name="T1", team_id="t1")
        team_manager.add_agent_to_team("t1", AgentProfile(agent_id="a1", name="A1", role="developer"))

        overview = team_manager.get_team_overview("t1")
        assert overview is not None
        assert overview["team_id"] == "t1"
        assert overview["name"] == "T1"
        assert overview["agent_count"] == 1

    def test_get_team_overview_nonexistent(self, team_manager):
        overview = team_manager.get_team_overview("no-team")
        assert overview is None


class TestDuplicateAgent:
    """Agent 复制功能测试."""

    def test_duplicate_agent(self, team_manager):
        team_manager.create_team(name="T1", team_id="t1")
        original = AgentProfile(agent_id="a1", name="Original", role="developer")
        team_manager.add_agent_to_team("t1", original)

        clone = team_manager.duplicate_agent("t1", "a1")
        assert clone is not None
        assert "副本" in clone.name
        assert clone.agent_id != original.agent_id
        # 验证克隆已在 team 中
        agents = team_manager.list_agents("t1")
        assert len(agents) == 2

    def test_duplicate_nonexistent_agent(self, team_manager):
        team_manager.create_team(name="T1", team_id="t1")
        result = team_manager.duplicate_agent("t1", "nonexistent")
        assert result is None


class TestSerialization:
    """序列化操作测试."""

    def test_to_dict(self, team_manager):
        team_manager.create_team(name="T1", team_id="t1")
        d = team_manager.to_dict()
        assert "t1" in d
        assert d["t1"]["name"] == "T1"
