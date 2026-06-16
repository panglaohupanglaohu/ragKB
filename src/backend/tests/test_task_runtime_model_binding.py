# -*- coding: utf-8 -*-
"""Task runtime model binding and auto-start regression tests."""

from __future__ import annotations

import asyncio
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from agents import api as api_module
from agents.models import AgentProfile, ModelConfig, SkillDefinition
from agents.skill_evolver import SkillEvolver
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


def test_agent_loop_context_disambiguates_cost_ri(monkeypatch):
    with TemporaryDirectory() as tmpdir:
        tm = TeamManager(store=TeamStore(path=Path(tmpdir) / "teams.json"))
        team = tm.create_team("AWS 运维团队", team_id="aws-runtime")
        skill = SkillDefinition(
            skill_id="ri-skill",
            name="云成本治理与 RI 购买建议",
            description="将扩容计划映射到账单预测、预算阈值、RI/Savings Plan 和治理目标。",
            instructions="估算实例、存储、跨 AZ 流量和快照成本；给出 RI/Savings Plan 购买建议。",
            visibility="trait",
            version=2,
            quality_score=0.9,
        )
        agent = AgentProfile(
            agent_id="cost-agent",
            name="成本优化成员",
            role="账单分析、RI/Savings Plan、成本治理目标制定",
            system_prompt="你是 AWS 运维团队的成本优化成员。",
            skills=[skill.skill_id],
        )
        team.add_skill(skill)
        team.add_agent(agent)
        tm._persist()
        monkeypatch.setattr(api_module, "_team_manager", tm)
        monkeypatch.setattr(api_module, "_get_skill_library", lambda: None)

        effective_prompt, system_prompt = api_module._build_agent_loop_prompt_and_system(
            prompt="如何RI",
            team_id=team.team_id,
            agent=agent,
            system_prompt="",
        )

    assert "Reserved Instance" in effective_prompt
    assert "AWS Reserved Instance" in system_prompt
    assert "云成本治理与 RI 购买建议" in system_prompt
    assert "不要解释成编程领域的 RI" in system_prompt


def test_agent_capability_profile_resolves_team_local_trait_skill(monkeypatch):
    with TemporaryDirectory() as tmpdir:
        tm = TeamManager(store=TeamStore(path=Path(tmpdir) / "teams.json"))
        team = tm.create_team("AWS 运维团队", team_id="aws-runtime")
        skill = SkillDefinition(
            skill_id="ri-skill",
            name="云成本治理与 RI 购买建议",
            description="RI/Savings Plan 成本治理",
            instructions="把 RI 解释为 AWS Reserved Instance。",
            visibility="trait",
            version=2,
            quality_score=0.92,
        )
        agent = AgentProfile(
            agent_id="cost-agent",
            name="成本优化成员",
            role="账单分析、RI/Savings Plan、成本治理目标制定",
            skills=[skill.skill_id],
        )
        team.add_skill(skill)
        team.add_agent(agent)
        tm._persist()

        monkeypatch.setattr(api_module, "_team_manager", tm)
        monkeypatch.setattr(api_module, "_get_skill_library", lambda: None)
        monkeypatch.setattr(api_module, "_get_agent_metrics", lambda agent_id: {})

        class FakeVerifier:
            _results = {}

        monkeypatch.setattr(api_module, "_get_skill_verifier", lambda: FakeVerifier())

        profile = api_module.agent_capability_profile(team.team_id, agent.agent_id)

    assert profile["skill_count"] == 1
    assert profile["skills"][0]["id"] == skill.skill_id
    assert profile["skills"][0]["name"] == "云成本治理与 RI 购买建议"


@pytest.mark.asyncio
async def test_skill_evolver_replaces_llm_fallback_with_cost_ri_instructions():
    skill = SkillDefinition(
        skill_id="ri-skill",
        name="云成本治理与 RI 购买建议",
        description="RI/Savings Plan 成本治理",
        instructions="估算实例、存储、跨 AZ 流量和快照成本。",
    )

    class FakeLibrary:
        def _find_skill(self, team_id, skill_id):
            return skill

    class FakeResult:
        response = "我是 AgentsGroup2026 智能体 (skill_evolver)。\\n⚠️ 当前 LLM 未连接"

    class FakeHarness:
        async def chat(self, **kwargs):
            return FakeResult()

    result = await SkillEvolver(FakeLibrary(), FakeHarness()).evolve_skill(
        "aws-runtime",
        skill.skill_id,
    )

    assert result["llm_degraded"] is True
    assert "AWS Reserved Instance" in result["improved_instructions"]
    assert "当前 LLM 未连接" not in result["improved_instructions"]
