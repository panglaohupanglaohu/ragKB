# -*- coding: utf-8 -*-
"""Agent-skill binding regression tests."""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from agents import api as api_module
from agents.models import AgentProfile, SkillDefinition
from agents.skill_extractor import SkillExtractorEngine, SkillReviewItem
from agents.skill_library import init_skill_library
from agents.skill_registry import SkillRegistry
from agents.tool_registry import ToolRegistry


@pytest.fixture
def isolated_api_state(monkeypatch, team_manager):
    tool_registry = ToolRegistry()
    tool_registry.load_defaults()

    skill_registry = SkillRegistry()
    skill_registry.load_defaults()

    init_skill_library(team_manager=team_manager, skill_registry=skill_registry)
    monkeypatch.setattr(api_module, "_team_manager", team_manager)
    monkeypatch.setattr(api_module, "_tool_registry", tool_registry)
    monkeypatch.setattr(api_module, "_skill_registry", skill_registry)

    team = team_manager.create_team(name="绑定测试团队", team_id="team-bind")
    agent = AgentProfile(agent_id="agent-bind", name="绑定代理", role="developer")
    team.add_agent(agent)
    team_manager._persist()
    return team_manager, team, agent


class DummyResult:
    def __init__(self, response: str = "ok"):
        self.response = response
        self.tool_invocations = []


class DummyHarness:
    def __init__(self):
        self.calls = []

    async def chat(self, content, **kwargs):
        self.calls.append({"content": content, **kwargs})
        return DummyResult(response="done")


class TestAgentSkillBinding:
    @pytest.mark.asyncio
    async def test_trait_approval_persists_same_team_agent_binding(
        self,
        isolated_api_state,
        monkeypatch,
    ):
        team_manager, team, agent = isolated_api_state
        item = SkillReviewItem(
            item_id="trait-bind-item",
            team_id=team.team_id,
            draft_name="注入后可见技能",
            draft_slug="injected-visible-skill",
            draft_instructions="执行注入后的绑定验证。",
        )
        engine = SkillExtractorEngine.__new__(SkillExtractorEngine)
        engine._queues = {team.team_id: {item.item_id: item}}
        engine._write_skill_to_tables = AsyncMock()
        engine._broadcast = AsyncMock()
        engine._persist_queue = lambda _team_id: None

        class _ClassificationStore:
            def seed_reserve_from_extraction(self, **_kwargs):
                return None

        from agents import skill_classifier
        monkeypatch.setattr(skill_classifier, "get_classification_store", lambda: _ClassificationStore())

        await engine.approve_item(
            team.team_id,
            item.item_id,
            skill_type="trait",
            target_agent_id=agent.agent_id,
        )

        assert len(agent.skills) == 1
        reloaded = team_manager._store.load_all()[team.team_id]
        assert reloaded.agents[agent.agent_id].skills == agent.skills

    def test_update_agent_skills_materializes_team_skill_and_persists(self, isolated_api_state):
        team_manager, team, agent = isolated_api_state

        result = api_module.update_agent_skills(
            team.team_id,
            agent.agent_id,
            api_module.UpdateSkillsRequest(skill_ids=["code_implementation"]),
        )

        assert len(result["skills"]) == 1
        canonical_skill_id = result["skills"][0]
        assert canonical_skill_id in team.skills
        assert team.skills[canonical_skill_id].name == "code_implementation"
        assert team.skills[canonical_skill_id].instructions

        reloaded = team_manager._store.load_all()[team.team_id]
        assert reloaded.agents[agent.agent_id].skills == [canonical_skill_id]
        assert reloaded.skills[canonical_skill_id].instructions

    @pytest.mark.asyncio
    async def test_generate_agent_response_uses_team_local_skill_instructions_and_required_tools(
        self,
        isolated_api_state,
        monkeypatch,
    ):
        _, team, agent = isolated_api_state
        team.skills["skill-local"] = SkillDefinition(
            skill_id="skill-local",
            name="custom_skill",
            description="本地技能",
            instructions="请先读取文件，再回答用户问题。",
            required_tools=["read_file"],
            source="team_local",
            slug="custom_skill",
        )
        agent.skills = ["skill-local"]
        agent.tools = []

        harness = DummyHarness()
        monkeypatch.setattr(api_module, "get_chat_harness", lambda: harness)

        response, result = await api_module._generate_agent_response(
            agent,
            "现在项目怎么样？",
            team_id=team.team_id,
        )

        assert response == "done"
        assert result.response == "done"
        assert len(harness.calls) == 1
        call = harness.calls[0]
        assert "请先读取文件，再回答用户问题。" in call["system_prompt"]
        assert "custom_skill" in call["system_prompt"]
        assert any(tool["function"]["name"] == "read_file" for tool in call["tools"])

    def test_disable_skill_unbinds_agents_and_persists(self, isolated_api_state):
        team_manager, team, agent = isolated_api_state
        team.skills["skill-local"] = SkillDefinition(
            skill_id="skill-local",
            name="custom_skill",
            instructions="本地技能指令",
            slug="custom_skill",
        )
        agent.skills = ["skill-local"]
        team_manager._persist()

        result = api_module.disable_skill(team.team_id, "skill-local")

        assert result == {"disabled": "skill-local"}
        assert agent.skills == []
        reloaded = team_manager._store.load_all()[team.team_id]
        assert "skill-local" not in reloaded.skills
        assert reloaded.agents[agent.agent_id].skills == []

    def test_delete_skill_unbinds_agents(self, isolated_api_state):
        _, team, agent = isolated_api_state
        team.skills["skill-local"] = SkillDefinition(
            skill_id="skill-local",
            name="custom_skill",
            instructions="本地技能指令",
            slug="custom_skill",
        )
        agent.skills = ["skill-local"]

        result = api_module.delete_skill(team.team_id, "skill-local")

        assert result["status"] == "deleted"
        assert agent.skills == []

    def test_delete_skill_removes_shared_skill_from_all_teams_and_agents(self, isolated_api_state):
        team_manager, team, agent = isolated_api_state
        team.skills["skill-shared"] = SkillDefinition(
            skill_id="skill-shared",
            name="shared_skill",
            instructions="共享技能指令",
            slug="shared_skill",
        )
        agent.skills = ["skill-shared"]

        other_team = team_manager.create_team(name="另一个团队", team_id="team-other")
        other_agent = AgentProfile(agent_id="agent-other", name="另一个代理", role="operator")
        other_team.add_agent(other_agent)
        other_team.skills["skill-shared"] = SkillDefinition(
            skill_id="skill-shared",
            name="shared_skill",
            instructions="共享技能指令",
            slug="shared_skill",
        )
        other_agent.skills = ["skill-shared"]
        team_manager._persist()

        result = api_module.delete_skill(team.team_id, "skill-shared")

        assert result["status"] == "deleted"
        assert set(result["removed_from_teams"]) == {"team-bind", "team-other"}
        assert agent.skills == []
        assert other_agent.skills == []

        reloaded = team_manager._store.load_all()
        assert "skill-shared" not in reloaded["team-bind"].skills
        assert "skill-shared" not in reloaded["team-other"].skills
        assert reloaded["team-bind"].agents["agent-bind"].skills == []
        assert reloaded["team-other"].agents["agent-other"].skills == []

    def test_list_team_skills_includes_effective_builtin_skills_bound_to_agents(self, isolated_api_state):
        _, team, agent = isolated_api_state
        agent.skills = ["code_implementation", "debugging"]

        result = api_module.list_team_skills(team.team_id)

        names = {item["name"] for item in result}
        assert "code_implementation" in names
        assert "debugging" in names
        code_item = next(item for item in result if item["name"] == "code_implementation")
        assert code_item["bound_agent_count"] == 1

    def test_delete_skill_unbinds_builtin_skill_refs_even_without_team_local_copy(self, isolated_api_state):
        _, team, agent = isolated_api_state
        agent.skills = ["code_implementation"]

        result = api_module.delete_skill(team.team_id, "code_implementation")

        assert result["status"] == "deleted"
        assert result["removed_agent_bindings"] == 1
        assert agent.skills == []
