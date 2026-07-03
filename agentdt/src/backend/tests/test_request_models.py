# -*- coding: utf-8 -*-
"""Regression coverage for recently migrated Pydantic request models."""

from __future__ import annotations

from pathlib import Path

from pydantic import ValidationError
import pytest

import agent_team_api as agent_team_api_module
from agents import api as api_module
from agents.models import AgentProfile, ModelConfig
from agents.k8s_webhook_handler import (
    DryRunLabelInjectionRequest,
    dry_run_label_injection,
)
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

    team = team_manager.create_team(name="Request Model 测试团队", team_id="team-request-models")
    team.add_agent(
        AgentProfile(
            agent_id="agent-0",
            name="Agent 0",
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
    for tool in tool_registry.list_all()[:2]:
        team.add_tool(tool)
    for skill in skill_registry.list_all()[:2]:
        team.add_skill(skill)
    team_manager._persist()

    return team_manager, team, task_engine


class TestAgentTeamEvolutionRequestModels:
    def test_auto_triage_request_enforces_top_n_bounds(self):
        with pytest.raises(ValidationError):
            agent_team_api_module.AutoTriageRequest(top_n=0)
        with pytest.raises(ValidationError):
            agent_team_api_module.AutoTriageRequest(top_n=11)

        model = agent_team_api_module.AutoTriageRequest(top_n=3)
        assert model.top_n == 3

    def test_dataset_generate_request_enforces_count_bounds(self):
        with pytest.raises(ValidationError):
            agent_team_api_module.DatasetGenerateRequest(count=0)
        with pytest.raises(ValidationError):
            agent_team_api_module.DatasetGenerateRequest(count=31)

        model = agent_team_api_module.DatasetGenerateRequest(skill_id="skill-a", count=12)
        assert model.count == 12

    def test_dataset_import_request_enforces_max_examples_bounds(self):
        with pytest.raises(ValidationError):
            agent_team_api_module.DatasetImportKBRequest(max_examples=0)
        with pytest.raises(ValidationError):
            agent_team_api_module.DatasetImportKBRequest(max_examples=51)

        model = agent_team_api_module.DatasetImportKBRequest(skill_id="skill-a", max_examples=25)
        assert model.max_examples == 25


class TestAgentConfigRequestModels:
    def test_edit_tool_request_updates_selected_fields(self, paginated_api_state):
        _, team, _ = paginated_api_state
        tool_id = next(iter(team.tools))

        result = api_module.edit_tool(
            team.team_id,
            tool_id,
            api_module.EditToolRequest(name="Renamed Tool", requires_approval=True),
        )

        assert result["name"] == "Renamed Tool"
        assert result["requires_approval"] is True

    def test_edit_skill_request_bumps_version_on_instruction_change(self, paginated_api_state):
        _, team, _ = paginated_api_state
        skill_id = next(iter(team.skills))
        original_version = getattr(team.skills[skill_id], "version", 0)

        result = api_module.edit_skill(
            team.team_id,
            skill_id,
            api_module.EditSkillRequest(instructions="updated instructions"),
        )

        assert result["version"] == original_version + 1

    def test_digital_twin_move_request_requires_both_fields(self):
        with pytest.raises(ValidationError):
            api_module.DigitalTwinMoveRequest(agent_id="agent-1")
        with pytest.raises(ValidationError):
            api_module.DigitalTwinMoveRequest(room_id="room-1")

    def test_digital_twin_interact_request_accepts_from_alias(self):
        req = api_module.DigitalTwinInteractRequest.model_validate(
            {"from": "agent-a", "to": "agent-b", "type": "handoff", "content": "payload"}
        )

        assert req.from_ == "agent-a"
        assert req.to == "agent-b"
        assert req.content == "payload"

    @pytest.mark.asyncio
    async def test_submit_task_returns_queued_task_when_backend_unavailable(
        self,
        paginated_api_state,
        monkeypatch,
    ):
        _, team, _ = paginated_api_state

        async def fake_token_factory_ready(_log_prefix):
            return False

        monkeypatch.setattr(api_module, "_check_token_factory_ready", fake_token_factory_ready)
        monkeypatch.setattr(api_module, "_has_execution_backend", lambda _: False)
        monkeypatch.setattr(api_module, "_seed_task_pipeline", lambda task: None)
        monkeypatch.setattr(api_module, "_write_task_init_handoff", lambda *args, **kwargs: None)
        monkeypatch.setattr(api_module, "_start_harness_monitor", lambda *args, **kwargs: None)

        result = await api_module.submit_task(
            team.team_id,
            api_module.SubmitTaskRequest(
                title="Queued task",
                metadata={"_engine_auto_execute": False},
            ),
        )

        assert result["title"] == "Queued task"
        assert result["team_id"] == team.team_id
        assert result["metadata"]["token_factory_error"] == "LLM 推理后端不可用，任务已创建但未启动执行"

    @pytest.mark.asyncio
    async def test_run_claude_for_task_starts_active_step_session(
        self,
        paginated_api_state,
        monkeypatch,
    ):
        _, team, task_engine = paginated_api_state
        task = AgentTask(
            task_id="workflow-task",
            team_id=team.team_id,
            title="Workflow task",
            metadata={
                "workflow": [
                    {
                        "index": 0,
                        "key": "develop",
                        "label": "开发",
                        "agent_id": "agent-0",
                        "agent_role": "developer",
                        "status": "active",
                    }
                ]
            },
        )
        task_engine._tasks[task.task_id] = task
        started = {}
        monitored = []

        def fake_start_session(session_id, prompt, cfg, agent, task_id):
            started.update(
                {
                    "session_id": session_id,
                    "prompt": prompt,
                    "agent_id": agent.agent_id,
                    "task_id": task_id,
                }
            )

        monkeypatch.setattr(api_module, "_start_claude_session", fake_start_session)
        monkeypatch.setattr(api_module, "_start_harness_monitor", lambda *args: monitored.append(args))

        result = await api_module.run_claude_for_task(team.team_id, task.task_id)

        assert result["status"] == "started"
        assert result["session_id"]
        assert task.metadata["workflow"][0]["session_id"] == result["session_id"]
        assert started["session_id"] == result["session_id"]
        assert started["agent_id"] == "agent-0"
        assert monitored == [(task.task_id, team.team_id)]


class TestWebhookDryRunRequestModel:
    @pytest.mark.asyncio
    async def test_dry_run_label_injection_uses_pydantic_request(self):
        body = DryRunLabelInjectionRequest.model_validate(
            {
                "metadata": {
                    "name": "pod-1",
                    "labels": {"team": "platform"},
                },
                "namespace": "prod",
                "namespaceAnnotations": {"cost.opencost.io/environment": "production"},
            }
        )

        result = await dry_run_label_injection(body)

        assert result["pod_name"] == "pod-1"
        assert result["namespace"] == "prod"
        assert result["existing_labels"]["team"] == "platform"
        assert result["resolved_labels"]["environment"] == "production"
