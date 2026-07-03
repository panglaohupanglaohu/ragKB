# -*- coding: utf-8 -*-
"""Regression tests for the shared tool-loop runtime migration."""

from __future__ import annotations

import asyncio
import inspect

import pytest

from agents import api as api_module
from agents.agent_loop import AgentLoop
from agents.chat_harness import ChatHarness, ProviderConfig
from agents.execution_registry import ToolPermissionContext
from agents.runtime import tool_loop as tool_loop_module
from channels.evolution_executor import EvolutionExecutor


class _BudgetCheck:
    allowed = True
    events = []


class _BudgetGuard:
    def check(self, **kwargs):
        return _BudgetCheck()

    def record_usage(self, record):
        return None


def test_agent_loop_run_delegates_to_shared_runtime(monkeypatch):
    captured = {}

    def fake_run_tool_loop_sync_with_provider(**kwargs):
        captured.update(kwargs)
        return {"ok": True, "summary": "done", "files_changed": ["src/backend/main.py"], "iterations": 2, "log": []}

    monkeypatch.setattr("agents.agent_loop.run_tool_loop_sync_with_provider", fake_run_tool_loop_sync_with_provider)

    loop = AgentLoop(
        api_key="test-key",
        api_base_url="https://example.com/v1",
        model="deepseek-v4-pro",
        role="developer",
        system_prompt="system prompt",
        max_iterations=7,
    )

    result = loop.run("请修复测试")

    assert result["ok"] is True
    assert captured["prompt"] == "请修复测试"
    assert captured["role"] == "developer"
    assert captured["system_prompt"] == "system prompt"
    assert captured["api_key"] == "test-key"
    assert captured["api_base_url"] == "https://example.com/v1"
    assert captured["model"] == "deepseek-v4-pro"
    assert captured["max_iterations"] == 7


def test_api_tool_loop_uses_shared_runtime(monkeypatch):
    captured = {}

    def fake_run_tool_loop_sync_with_provider(**kwargs):
        captured.update(kwargs)
        return {
            "ok": True,
            "summary": "patched",
            "files_changed": ["src/backend/api.py"],
            "iterations": 3,
            "log": [{"name": "patch_file", "ok": True}],
        }

    monkeypatch.setattr("agents.runtime.run_tool_loop_sync_with_provider", fake_run_tool_loop_sync_with_provider)

    session = {"lines": []}
    api_module._run_tool_loop(
        session,
        "请打补丁",
        "developer",
        api_key="key",
        api_base_url="https://example.com/v1",
        model="deepseek-v4-pro",
        max_iterations=4,
    )

    assert captured["prompt"] == "请打补丁"
    assert captured["role"] == "developer"
    assert captured["api_key"] == "key"
    assert session["loop_ok"] is True
    assert session["loop_summary"] == "patched"
    assert session["files_changed"] == ["src/backend/api.py"]
    assert session["status"] == "completed"


def test_evolution_executor_uses_shared_runtime(monkeypatch):
    captured = {}

    def fake_run_tool_loop_sync_with_provider(**kwargs):
        captured.update(kwargs)
        return {"ok": True, "summary": "done", "files_changed": [], "iterations": 1, "log": []}

    monkeypatch.setattr("agents.runtime.run_tool_loop_sync_with_provider", fake_run_tool_loop_sync_with_provider)

    executor = EvolutionExecutor()
    result = executor._run_agent_loop(
        {"api_key": "k", "api_base_url": "https://example.com/v1", "model": "deepseek-v4-pro"},
        "system prompt",
        "user prompt",
        lambda *_: None,
    )

    assert result["ok"] is True
    assert captured["prompt"] == "user prompt"
    assert captured["role"] == "developer"
    assert captured["model"] == "deepseek-v4-pro"
    assert captured["system_prompt"] == "system prompt"


@pytest.mark.asyncio
async def test_shared_runtime_filters_and_blocks_disallowed_tools(monkeypatch):
    responses = [
        {
            "choices": [
                {
                    "message": {
                        "content": "",
                        "tool_calls": [
                            {
                                "id": "call-1",
                                "function": {
                                    "name": "write_file",
                                    "arguments": "{\"path\": \"src/backend/x.py\", \"content\": \"print(1)\"}",
                                },
                            }
                        ],
                    },
                    "finish_reason": "tool_calls",
                }
            ],
            "usage": {},
        },
        {
            "choices": [
                {
                    "message": {"content": "已拒绝未授权工具并结束。"},
                    "finish_reason": "stop",
                }
            ],
            "usage": {},
        },
    ]
    dispatch_calls = []
    events = []

    async def fake_chat_completion(self, *args, **kwargs):
        return responses.pop(0)

    monkeypatch.setattr(tool_loop_module, "get_budget_guard", lambda: _BudgetGuard())
    monkeypatch.setattr(tool_loop_module.LLMClient, "chat_completion", fake_chat_completion)
    monkeypatch.setattr(
        tool_loop_module,
        "dispatch_tool_call",
        lambda name, args_json: dispatch_calls.append((name, args_json)) or {"ok": True},
    )

    result = await tool_loop_module.run_tool_loop(
        prompt="请直接修改文件",
        config=ProviderConfig(api_key="k", api_base_url="https://example.com/v1", model="deepseek-v4-pro"),
        role="developer",
        system_prompt="你是开发 agent",
        permission_context=ToolPermissionContext.from_lists(deny_names=["write_file"]),
        on_event=lambda kind, payload: events.append((kind, payload)),
    )

    loop_start = next(payload for kind, payload in events if kind == "loop_start")
    assert "write_file" not in loop_start["tools"]
    assert loop_start["runtime_id"]
    assert loop_start["loop_kind"] == "tool_loop"
    assert loop_start["sequence"] == 1
    assert dispatch_calls == []
    assert result.ok is True
    assert result.runtime_id == loop_start["runtime_id"]
    assert result.log[0]["name"] == "write_file"
    assert result.log[0]["ok"] is False
    assert [payload["sequence"] for _, payload in events] == list(range(1, len(events) + 1))


def test_runtime_entrypoints_delegate_to_shared_runtimes():
    agent_loop_run = inspect.getsource(AgentLoop.run)
    api_tool_loop = inspect.getsource(api_module._run_tool_loop)
    evolution_loop = inspect.getsource(EvolutionExecutor._run_agent_loop)
    harness_agent_loop = inspect.getsource(ChatHarness.agent_loop)
    harness_agent_loop_stream = inspect.getsource(ChatHarness.agent_loop_stream)

    assert "run_tool_loop_sync_with_provider" in agent_loop_run
    assert "run_tool_loop_sync_with_provider" in api_tool_loop
    assert "run_tool_loop_sync_with_provider" in evolution_loop
    assert "run_plan_loop" in harness_agent_loop
    assert "stream_plan_loop" in harness_agent_loop_stream

    assert "dispatch_tool_call" not in agent_loop_run
    assert "dispatch_tool_call" not in api_tool_loop
    assert "dispatch_tool_call" not in evolution_loop
    assert "build_plan_from_prompt" in harness_agent_loop
    assert "build_plan_from_prompt" in harness_agent_loop_stream
