# -*- coding: utf-8 -*-
"""Regression tests for the shared plan-loop runtime."""

from __future__ import annotations

import pytest

from agents.chat_harness import ExecutionPlan, ProviderConfig
from agents.runtime import plan_loop as plan_loop_module


class _FakeToolResult:
    def __init__(self, success: bool = True, output: str = "", error: str = ""):
        self.success = success
        self.output = output
        self.error = error


class _FakeExecutor:
    def __init__(self, result: _FakeToolResult):
        self.result = result
        self.calls = []

    async def execute(self, tool_name, tool_args, **kwargs):
        self.calls.append(
            {
                "tool_name": tool_name,
                "tool_args": tool_args,
                "kwargs": kwargs,
            }
        )
        return self.result


class _FakeHarness:
    def __init__(self):
        self.chat_calls = []
        self.stream_calls = []

    async def chat(self, prompt, **kwargs):
        self.chat_calls.append({"prompt": prompt, **kwargs})
        return type("Turn", (), {"response": "总结完成"})()

    async def stream_chat(self, prompt, **kwargs):
        self.stream_calls.append({"prompt": prompt, **kwargs})
        yield {"type": "message_delta", "text": "总结"}
        yield {"type": "message_stop", "stop_reason": "completed"}


@pytest.mark.asyncio
async def test_run_plan_loop_executes_steps_and_uses_synthesis_prompt(monkeypatch):
    executor = _FakeExecutor(_FakeToolResult(success=True, output="file contents"))
    harness = _FakeHarness()
    events = []

    monkeypatch.setattr("agents.tool_executor.get_tool_executor", lambda: executor)

    def build_plan(prompt, available_tools=None):
        plan = ExecutionPlan(goal=prompt)
        plan.add_step(
            "tool_call",
            "读取文件",
            tool_name="read_file",
            tool_args={"path": "README.md"},
        )
        plan.add_step("respond", "回复用户")
        return plan

    result = await plan_loop_module.run_plan_loop(
        harness,
        prompt="请读取 README",
        plan_builder=build_plan,
        agent_id="agent-1",
        team_id="team-1",
        session_id="sess-1",
        system_prompt="system",
        tools=[{"type": "function", "function": {"name": "read_file"}}],
        on_event=lambda event_type, payload: events.append((event_type, payload)),
    )

    assert executor.calls[0]["tool_name"] == "read_file"
    assert result.observations[0]["tool"] == "read_file"
    assert result.final_response == "总结完成"
    assert "[read_file] ✅: file contents" in harness.chat_calls[0]["prompt"]
    assert harness.chat_calls[0]["session_id"] == "sess-1"
    assert [event[0] for event in events[:3]] == ["plan_start", "step_start", "tool_result"]
    assert events[-1][0] == "loop_end"


@pytest.mark.asyncio
async def test_stream_plan_loop_skips_after_iteration_cap_and_streams_synthesis(monkeypatch):
    executor = _FakeExecutor(_FakeToolResult(success=True, output="first tool ok"))
    harness = _FakeHarness()
    callback_events = []

    monkeypatch.setattr("agents.tool_executor.get_tool_executor", lambda: executor)

    def build_plan(prompt, available_tools=None):
        plan = ExecutionPlan(goal=prompt)
        plan.add_step(
            "tool_call",
            "第一步",
            tool_name="read_file",
            tool_args={"path": "README.md"},
        )
        plan.add_step(
            "tool_call",
            "第二步",
            tool_name="write_file",
            tool_args={"path": "tmp.txt", "content": "x"},
        )
        return plan

    events = [
        event
        async for event in plan_loop_module.stream_plan_loop(
            harness,
            prompt="请执行计划",
            plan_builder=build_plan,
            agent_id="agent-2",
            team_id="team-2",
            session_id="sess-2",
            system_prompt="system",
            max_iterations=1,
            on_event=lambda event_type, payload: callback_events.append((event_type, payload)),
        )
    ]

    skipped = [
        event for event in events
        if event["type"] == "step_complete"
        and event["step"]["status"] == "skipped"
    ]

    assert skipped
    assert skipped[0]["step"]["error"] == "Iteration cap reached"
    assert harness.stream_calls
    assert "[read_file] ✅: first tool ok" in harness.stream_calls[0]["prompt"]
    assert events[-1]["type"] == "message_stop"
    assert callback_events[0][0] == "plan_start"
    assert callback_events[-1][0] == "loop_end"


@pytest.mark.asyncio
async def test_chat_harness_agent_loop_methods_delegate_to_shared_plan_runtime(monkeypatch):
    from agents.chat_harness import ChatHarness

    captured = {"run": None, "stream": None}

    async def fake_run_plan_loop(harness, **kwargs):
        captured["run"] = kwargs
        return type("LoopResult", (), {"iterations": 2})()

    async def fake_stream_plan_loop(harness, **kwargs):
        captured["stream"] = kwargs
        yield {"type": "message_stop", "stop_reason": "completed"}

    monkeypatch.setattr("agents.runtime.run_plan_loop", fake_run_plan_loop)
    monkeypatch.setattr("agents.runtime.stream_plan_loop", fake_stream_plan_loop)

    harness = ChatHarness(default_config=ProviderConfig())
    result = await harness.agent_loop(
        "做个计划",
        tools=[{"type": "function", "function": {"name": "read_file"}}],
        max_iterations=3,
        on_event=lambda *_args: None,
    )
    chunks = [
        chunk
        async for chunk in harness.agent_loop_stream(
            "做个流式计划",
            max_iterations=4,
            on_event=lambda *_args: None,
        )
    ]

    assert result.iterations == 2
    assert captured["run"]["max_iterations"] == 3
    assert captured["run"]["tools"][0]["function"]["name"] == "read_file"
    assert callable(captured["run"]["on_event"])
    assert captured["stream"]["max_iterations"] == 4
    assert callable(captured["stream"]["on_event"])
    assert chunks[-1]["type"] == "message_stop"
