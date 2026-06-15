# -*- coding: utf-8 -*-
"""Task runtime model binding and auto-start regression tests."""

from __future__ import annotations

import asyncio
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from agents import api as api_module
from agents.models import AgentProfile, ModelConfig
from agents.task_engine import AgentTask, TaskEngine, TaskStatus
from agents.task_store import TaskStore
from agents.team_manager import TeamManager
from agents.team_store import TeamStore


def test_task_runtime_prefers_agent_team_model(monkeypatch):
    with TemporaryDirectory() as tmpdir:
        tm = TeamManager(store=TeamStore(path=Path(tmpdir) / "teams.json"))
        team = tm.create_team("AWS 运维团队", team_id="aws-runtime")
        model = ModelConfig(
            model_id="codebuddy",
            provider="codebuddy",
            name="deepseek-v4-pro",
            api_key="team-codebuddy-key",
            api_base_url=" https://copilot.tencent.com/v2/",
            max_tokens=4096,
            temperature=0.7,
            is_default=True,
        )
        agent = AgentProfile(
            agent_id="ops-leader",
            name="运维 Leader",
            role="project_manager",
            model_id=model.model_id,
        )
        team.add_model(model)
        team.add_agent(agent)
        tm._persist()

        monkeypatch.setattr(api_module, "_team_manager", tm)
        monkeypatch.setattr(
            api_module,
            "_harness_provider_credentials",
            lambda: ("bad-global-key", "https://api.deepseek.com", "deepseek-chat", "deepseek"),
        )

        api_key, base_url, model_name = api_module._get_deepseek_credentials(
            agent=agent,
            team_id=team.team_id,
        )

    assert api_key == "team-codebuddy-key"
    assert base_url == "https://copilot.tencent.com/v2"
    assert model_name == "deepseek-v4-pro"


@pytest.mark.asyncio
async def test_manual_dispatch_task_is_not_auto_enqueued():
    with TemporaryDirectory() as tmpdir:
        engine = TaskEngine(store=TaskStore(base_dir=Path(tmpdir)), max_concurrency=1)
        executed = []

        async def executor(task):
            executed.append(task.task_id)
            return {"ok": True}

        engine.set_executor(executor)
        await engine.start()
        try:
            task = AgentTask(
                team_id="aws-runtime",
                title="只派发不执行",
                metadata={"_engine_auto_execute": False},
            )
            await engine.submit_task(task)
            await asyncio.sleep(0.05)

            stored = engine.get_task(task.task_id)
            assert stored is not None
            assert stored.status == TaskStatus.PENDING
            assert executed == []
        finally:
            await engine.stop()


def test_llm_auth_error_completes_with_degraded_output():
    session = {"lines": []}

    api_module._complete_session_with_llm_degraded_output(
        session,
        "ElasticSearch/OpenSearch 伸缩任务",
        "API 错误: 401 Authorization Required",
    )

    assert session["status"] == "completed"
    assert session["exit_code"] == 0
    assert session["llm_degraded"] is True
    assert "降级执行草稿" in "".join(session["lines"])
