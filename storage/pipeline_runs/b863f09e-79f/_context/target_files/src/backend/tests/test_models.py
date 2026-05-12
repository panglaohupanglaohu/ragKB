# -*- coding: utf-8 -*-
"""数据模型单元测试 — AgentProfile, AgentTeam, ModelConfig 等."""

from __future__ import annotations

import json

from agents.models import (
    AccessLevel,
    AgentChannelConfig,
    AgentPermission,
    AgentPersonality,
    AgentProfile,
    AgentState,
    AgentTeam,
    AgentTemplateType,
    ModelConfig,
    SkillCategory,
    SkillDefinition,
    ToolCategory,
    ToolDefinition,
    Visibility,
)


# ═══════════════════════════════════════════════════
# AgentState 枚举测试
# ═══════════════════════════════════════════════════

class TestAgentState:
    """AgentState 枚举测试."""

    def test_all_states_exist(self):
        states = set(s.value for s in AgentState)
        assert "idle" in states
        assert "working" in states
        assert "paused" in states
        assert "error" in states
        assert "stopped" in states

    def test_state_count(self):
        assert len(list(AgentState)) == 5


# ═══════════════════════════════════════════════════
# AgentProfile 测试
# ═══════════════════════════════════════════════════

class TestAgentProfile:
    """AgentProfile 数据类测试."""

    def test_minimal_creation(self):
        agent = AgentProfile(
            agent_id="agent-001",
            name="TestAgent",
            role="developer",
        )
        assert agent.agent_id == "agent-001"
        assert agent.name == "TestAgent"
        assert agent.role == "developer"
        assert agent.state == AgentState.IDLE
        assert agent.template_type == AgentTemplateType.CUSTOM

    def test_full_creation(self):
        personality = AgentPersonality(
            tone="friendly",
            language="en-US",
            expertise_areas=["python", "testing"],
            response_style="verbose",
            creativity=0.8,
        )
        agent = AgentProfile(
            agent_id="agent-002",
            name="FullAgent",
            role="engineer",
            description="A fully configured test agent",
            template_type=AgentTemplateType.DEVELOPER,
            state=AgentState.WORKING,
            model_id="model-deepseek-v4",
            system_prompt="You are a test agent.",
            personality=personality,
        )
        assert agent.agent_id == "agent-002"
        assert agent.personality.tone == "friendly"
        assert agent.personality.creativity == 0.8
        assert agent.personality.response_style == "verbose"

    def test_to_dict_roundtrip(self):
        agent = AgentProfile(
            agent_id="agent-003",
            name="Roundtrip",
            role="analyst",
        )
        d = agent.to_dict()
        assert d["agent_id"] == "agent-003"
        assert d["name"] == "Roundtrip"
        assert d["role"] == "analyst"
        assert d["state"] == "idle"

    def test_to_dict_is_json_serializable(self):
        agent = AgentProfile(
            agent_id="agent-004",
            name="Serializable",
            role="coordinator",
        )
        d = agent.to_dict()
        json_str = json.dumps(d)
        restored = json.loads(json_str)
        assert restored["agent_id"] == "agent-004"


# ═══════════════════════════════════════════════════
# AgentTeam 测试
# ═══════════════════════════════════════════════════

class TestAgentTeam:
    """AgentTeam 数据类测试."""

    def test_create_team(self):
        team = AgentTeam(
            team_id="team-001",
            name="Test Team",
            description="A test team",
        )
        assert team.team_id == "team-001"
        assert team.name == "Test Team"
        assert team.visibility == Visibility.PRIVATE

    def test_add_agent_to_team(self):
        agent = AgentProfile(
            agent_id="agent-005",
            name="Member",
            role="engineer",
        )
        team = AgentTeam(
            team_id="team-002",
            name="MemberTeam",
        )
        team.agents.append(agent)
        assert len(team.agents) == 1
        assert team.agents[0].agent_id == "agent-005"

    def test_to_dict(self):
        team = AgentTeam(
            team_id="team-003",
            name="DictTeam",
            description="Testing to_dict",
        )
        d = team.to_dict()
        assert d["team_id"] == "team-003"
        assert d["name"] == "DictTeam"
        assert "agents" in d

    def test_to_dict_is_json_serializable(self):
        team = AgentTeam(
            team_id="team-004",
            name="JsonTeam",
        )
        d = team.to_dict()
        json_str = json.dumps(d)
        restored = json.loads(json_str)
        assert restored["team_id"] == "team-004"


# ═══════════════════════════════════════════════════
# ModelConfig 测试
# ═══════════════════════════════════════════════════

class TestModelConfig:
    """ModelConfig 数据类测试."""

    def test_default_creation(self):
        model = ModelConfig(
            model_id="model-deepseek-v4",
            provider="deepseek",
            name="deepseek-v4-flash",
        )
        assert model.model_id == "model-deepseek-v4"
        assert model.provider == "deepseek"
        assert model.max_tokens == 65536
        assert model.temperature == 0.7
        assert model.is_default is False
        assert model.enabled is True

    def test_custom_config(self):
        model = ModelConfig(
            model_id="model-custom",
            provider="openai",
            name="gpt-4o-mini",
            max_tokens=128000,
            temperature=0.3,
            is_default=True,
            api_key="sk-test",
            api_base_url="https://api.openai.com/v1",
        )
        assert model.max_tokens == 128000
        assert model.temperature == 0.3
        assert model.is_default is True
        assert model.api_key == "sk-test"

    def test_to_dict(self):
        model = ModelConfig(
            model_id="model-dict",
            provider="anthropic",
            name="claude-sonnet",
        )
        d = model.to_dict()
        assert d["model_id"] == "model-dict"
        assert d["provider"] == "anthropic"
        assert d["is_default"] is False


# ═══════════════════════════════════════════════════
# ToolDefinition 测试
# ═══════════════════════════════════════════════════

class TestToolDefinition:
    """ToolDefinition 测试."""

    def test_create_tool(self):
        tool = ToolDefinition(
            tool_id="tool-read-file",
            name="Read File",
            description="Read file contents",
            category=ToolCategory.GENERAL,
        )
        assert tool.tool_id == "tool-read-file"
        assert tool.name == "Read File"
        assert tool.category == ToolCategory.GENERAL
        assert tool.enabled is True

    def test_tool_with_config(self):
        tool = ToolDefinition(
            tool_id="tool-web-search",
            name="Web Search",
            description="Search the web",
            category=ToolCategory.GENERAL,
            requires_approval=True,
            config={"api_endpoint": "https://search.example.com"},
        )
        assert tool.requires_approval is True
        assert tool.config["api_endpoint"] == "https://search.example.com"

    def test_to_dict(self):
        tool = ToolDefinition(
            tool_id="tool-dict",
            name="Dict Tool",
            description="A dict test",
            category=ToolCategory.GENERAL,
        )
        d = tool.to_dict()
        assert d["tool_id"] == "tool-dict"
        assert d["name"] == "Dict Tool"


# ═══════════════════════════════════════════════════
# SkillDefinition 测试
# ═══════════════════════════════════════════════════

class TestSkillDefinition:
    """SkillDefinition 测试."""

    def test_create_skill(self):
        skill = SkillDefinition(
            skill_id="skill-greeting",
            name="Greeting",
            description="Greet users",
            category=SkillCategory.GENERAL,
        )
        assert skill.skill_id == "skill-greeting"
        assert skill.name == "Greeting"
        assert skill.category == SkillCategory.GENERAL

    def test_skill_with_instructions(self):
        skill = SkillDefinition(
            skill_id="skill-code-review",
            name="Code Review",
            description="Review code changes",
            category=SkillCategory.RESEARCH,
            instructions="Analyze the code diff carefully.",
            required=True,
        )
        assert skill.instructions == "Analyze the code diff carefully."
        assert skill.required is True

    def test_to_dict(self):
        skill = SkillDefinition(
            skill_id="skill-dict",
            name="DictSkill",
            description="A dict skill",
            category=SkillCategory.GENERAL,
        )
        d = skill.to_dict()
        assert d["skill_id"] == "skill-dict"
        assert d["name"] == "DictSkill"


# ═══════════════════════════════════════════════════
# AgentPermission 测试
# ═══════════════════════════════════════════════════

class TestAgentPermission:
    """AgentPermission 测试."""

    def test_create_permission(self):
        perm = AgentPermission(
            agent_id="agent-001",
            access_level=AccessLevel.READ,
            allowed_tools=["tool-read-file", "tool-grep"],
        )
        assert perm.agent_id == "agent-001"
        assert perm.access_level == AccessLevel.READ
        assert "tool-read-file" in perm.allowed_tools

    def test_defaults(self):
        perm = AgentPermission(agent_id="agent-002")
        assert perm.access_level == AccessLevel.READ
        assert perm.allowed_tools == []


# ═══════════════════════════════════════════════════
# ChannelConfig 测试
# ═══════════════════════════════════════════════════

class TestAgentChannelConfig:
    """AgentChannelConfig 测试."""

    def test_create_channel_config(self):
        cfg = AgentChannelConfig(
            channel="openclaw",
            endpoint="https://sync.example.com",
            sync_interval_seconds=30,
        )
        assert cfg.channel == "openclaw"
        assert cfg.sync_interval_seconds == 30
        assert cfg.enabled is True

    def test_to_dict(self):
        cfg = AgentChannelConfig(
            channel="bridge",
            endpoint="wss://bridge.example.com",
        )
        d = cfg.to_dict()
        assert d["channel"] == "bridge"
        assert d["enabled"] is True
