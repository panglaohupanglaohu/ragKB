# -*- coding: utf-8 -*-
"""Security regression tests for secret resolution and tool permissions."""

from __future__ import annotations

import json

import pytest

from agents import api as api_module
from agents.chat_harness import ChatHarness, ProviderConfig
from agents.models import AgentProfile
from agents.secret_store import load_default_llm_api_key
from agents.skill_library import init_skill_library
from agents.skill_registry import SkillRegistry
from agents.tool_executor import get_tool_executor
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

    team = team_manager.create_team(name="权限测试团队", team_id="team-perm")
    agent = AgentProfile(agent_id="agent-perm", name="权限代理", role="developer")
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


class CaptureLoopHarness:
    def __init__(self):
        self.last_permission_context = None

    async def agent_loop(self, *args, **kwargs):
        self.last_permission_context = kwargs.get("permission_context")
        return type("Result", (), {"to_dict": lambda self: {"ok": True}})()


def _use_temp_secret_store(monkeypatch, tmp_path):
    from agents import secret_store

    monkeypatch.setattr(secret_store, "_CONFIG_DIR", tmp_path)
    monkeypatch.setattr(secret_store, "_API_KEYS_PATH", tmp_path / ".api_keys.json")


class TestSecretResolution:
    def test_provider_config_prefers_env_over_plaintext(self, monkeypatch, tmp_path):
        _use_temp_secret_store(monkeypatch, tmp_path)
        monkeypatch.setenv("DEEPSEEK_API_KEY", "env-secret")
        settings = {
            "llm": {
                "provider": "deepseek",
                "api_key": "plaintext-secret",
                "api_base_url": "https://api.deepseek.com",
                "model": "deepseek-v4-pro",
            }
        }

        cfg = ProviderConfig.from_settings(settings)

        assert cfg.api_key == "env-secret"

    def test_update_llm_provider_saves_default_secret_store(self, monkeypatch, tmp_path):
        _use_temp_secret_store(monkeypatch, tmp_path)
        harness = ChatHarness(default_config=ProviderConfig())
        monkeypatch.setattr(api_module, "get_chat_harness", lambda: harness)

        api_module.update_llm_provider(
            api_module.LLMProviderConfigRequest(
                provider="deepseek",
                api_key="stored-secret",
                api_base_url="https://api.deepseek.com",
                model="deepseek-v4-pro",
            )
        )

        assert load_default_llm_api_key() == "stored-secret"
        payload = json.loads((tmp_path / ".api_keys.json").read_text(encoding="utf-8"))
        assert payload["__default__"]["llm"] == "stored-secret"


class TestToolPermissions:
    def test_update_permissions_persists_allowed_tools(self, isolated_api_state):
        team_manager, team, agent = isolated_api_state

        result = api_module.update_permissions(
            team.team_id,
            agent.agent_id,
            api_module.UpdatePermissionsRequest(
                permissions=[
                    api_module.PermissionItem(
                        resource="code",
                        access_level="read",
                        allowed_tools=["read_file"],
                    )
                ]
            ),
        )

        assert result["permissions"][0]["allowed_tools"] == ["read_file"]
        reloaded = team_manager._store.load_all()[team.team_id]
        assert reloaded.agents[agent.agent_id].permissions[0].allowed_tools == ["read_file"]

    @pytest.mark.asyncio
    async def test_generate_agent_response_filters_blocked_tools(self, isolated_api_state, monkeypatch):
        _, team, agent = isolated_api_state
        agent.tools = ["read_file", "write_file"]
        agent.permissions = [
            api_module.AgentPermission(resource="code", access_level=api_module.AccessLevel.READ)
        ]
        harness = DummyHarness()
        monkeypatch.setattr(api_module, "get_chat_harness", lambda: harness)

        response, result = await api_module._generate_agent_response(
            agent,
            "读一下文件内容",
            team_id=team.team_id,
        )

        assert response == "done"
        assert result.response == "done"
        assert len(harness.calls) == 1
        tools = harness.calls[0]["tools"]
        assert any(tool["function"]["name"] == "read_file" for tool in tools)
        assert all(tool["function"]["name"] != "write_file" for tool in tools)

    @pytest.mark.asyncio
    async def test_executor_rejects_blocked_tool(self, isolated_api_state, tmp_path):
        _, _, agent = isolated_api_state
        agent.permissions = [
            api_module.AgentPermission(resource="code", access_level=api_module.AccessLevel.READ)
        ]
        permission_context = api_module._build_agent_permission_context(agent)
        executor = get_tool_executor()
        target = tmp_path / "blocked.txt"

        result = await executor.execute(
            "write_file",
            {"path": str(target), "content": "nope"},
            agent_id=agent.agent_id,
            permission_context=permission_context,
        )

        assert result.success is False
        assert "blocked" in result.error.lower()
        assert not target.exists()

    @pytest.mark.asyncio
    async def test_run_agent_loop_passes_permission_context(self, isolated_api_state, monkeypatch):
        _, _, agent = isolated_api_state
        agent.permissions = [
            api_module.AgentPermission(resource="code", access_level=api_module.AccessLevel.READ)
        ]
        harness = CaptureLoopHarness()
        monkeypatch.setattr(api_module, "get_chat_harness", lambda: harness)

        result = await api_module.run_agent_loop(
            api_module.AgentLoopRequest(
                prompt="帮我改文件",
                agent_id=agent.agent_id,
                max_iterations=2,
            )
        )

        assert result == {"ok": True}
        assert harness.last_permission_context is not None
        assert harness.last_permission_context.blocks("write_file") is True
        assert harness.last_permission_context.blocks("read_file") is False
