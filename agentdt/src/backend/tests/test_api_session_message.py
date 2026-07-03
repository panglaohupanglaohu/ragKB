from __future__ import annotations

from types import SimpleNamespace

import pytest

from agents import api as api_module
from agents.models import AgentProfile
from agents.skill_library import init_skill_library
from agents.skill_registry import SkillRegistry
from agents.team_manager import TeamManager
from agents.team_store import TeamStore
from agents.tool_registry import ToolRegistry


@pytest.fixture
def session_api_state(monkeypatch, tmp_path):
    team_manager = TeamManager(store=TeamStore(path=tmp_path / "teams.json"))
    tool_registry = ToolRegistry()
    tool_registry.load_defaults()
    skill_registry = SkillRegistry()
    skill_registry.load_defaults()
    init_skill_library(team_manager=team_manager, skill_registry=skill_registry)

    monkeypatch.setattr(api_module, "_team_manager", team_manager)
    monkeypatch.setattr(api_module, "_tool_registry", tool_registry)
    monkeypatch.setattr(api_module, "_skill_registry", skill_registry)
    monkeypatch.setattr(api_module, "_sessions", {})
    monkeypatch.setattr(api_module, "_agent_metrics", {})
    monkeypatch.setattr(api_module, "_agent_logs", {})

    team = team_manager.create_team(name="Session Team", team_id="team-session")
    agent = AgentProfile(agent_id="agent-session", name="Session Agent", role="developer")
    team.add_agent(agent)
    api_module._sessions["session-1"] = {
        "session_id": "session-1",
        "agent_id": agent.agent_id,
        "team_id": team.team_id,
        "messages": [],
    }
    return team, agent


@pytest.mark.asyncio
async def test_send_session_message_appends_reply_and_records_usage_metrics(
    session_api_state,
    monkeypatch,
):
    team, agent = session_api_state
    tool_invocation = SimpleNamespace(tool_name="read_file")
    usage = SimpleNamespace(total_tokens=42)
    turn_result = SimpleNamespace(
        model="model-a",
        provider="provider-a",
        latency_ms=12,
        usage=usage,
        tool_invocations=[tool_invocation],
    )

    async def fake_generate_agent_response(agent_arg, content, session_id, team_id):
        assert agent_arg.agent_id == agent.agent_id
        assert content == "hello"
        assert session_id == "session-1"
        assert team_id == team.team_id
        return "assistant reply", turn_result

    monkeypatch.setattr(api_module, "_generate_agent_response", fake_generate_agent_response)

    result = await api_module.send_session_message(
        team.team_id,
        agent.agent_id,
        "session-1",
        api_module.SessionMessageRequest(content="hello"),
    )

    messages = api_module._sessions["session-1"]["messages"]
    metrics = api_module._agent_metrics[agent.agent_id]
    logs = api_module._agent_logs[agent.agent_id]

    assert result["role"] == "user"
    assert result["content"] == "hello"
    assert [message["role"] for message in messages] == ["user", "assistant"]
    assert messages[1]["content"] == "assistant reply"
    assert messages[1]["model"] == "model-a"
    assert messages[1]["provider"] == "provider-a"
    assert messages[1]["latency_ms"] == 12
    assert metrics["messages_sent"] == 1
    assert metrics["today_llm_calls"] == 1
    assert metrics["today_tokens"] == 42
    assert metrics["month_tokens"] == 42
    assert metrics["total_tokens"] == 42
    assert metrics["tools_invoked"] == 1
    assert any(log["action"] == "message_received" for log in logs)
    assert any(log["action"] == "tools_invoked" and log["detail"] == "read_file" for log in logs)
