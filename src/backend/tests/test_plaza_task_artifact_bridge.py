# -*- coding: utf-8 -*-
"""Plaza task artifact and evolution bridge tests."""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

import agent_team_api as agent_team_api_module
from agents import api as api_module
from agents import task_engine as task_engine_module
from agents.task_engine import AgentTask, TaskEngine, TaskStatus
from agents.task_store import TaskStore
from channels.system_evolution import EvolutionItem, EvolutionStatus, SystemEvolutionChannel


def _build_success_workflow(artifact_dir: str) -> list:
    return [
        {
            "key": "develop",
            "status": "completed",
            "artifact": f"{artifact_dir}/04_develop/summary.md",
            "deliverable_paths": ["src/backend/main.py"],
            "_summary": {
                "files_changed": ["src/backend/main.py"],
                "verify_checklist": ["import check: `src/backend/main.py`"],
            },
        },
        {
            "key": "test",
            "status": "completed",
            "artifact": f"{artifact_dir}/05_test.md",
            "_summary": {
                "verdict": "PASS",
                "checklist": [],
            },
        },
        {
            "key": "deploy",
            "status": "completed",
            "artifact": f"{artifact_dir}/06_deploy/summary.md",
            "deploy_result": {
                "developer": {"applied": [{"path": "src/backend/main.py"}], "skipped": [], "failed": []},
                "deployer": {"applied": [], "skipped": [], "failed": []},
            },
        },
    ]


def _build_failed_workflow(artifact_dir: str) -> list:
    return [
        {
            "key": "develop",
            "status": "completed",
            "artifact": f"{artifact_dir}/04_develop/summary.md",
            "_summary": {"files_changed": ["src/backend/main.py"]},
        },
        {
            "key": "test",
            "status": "failed",
            "artifact": f"{artifact_dir}/05_test.md",
            "_summary": {
                "verdict": "FAIL",
                "checklist": [{"severity": "FAIL", "detail": "核心回归未通过"}],
            },
        },
    ]


@pytest.fixture
def isolated_task_engine(monkeypatch):
    with TemporaryDirectory() as tmpdir:
        engine = TaskEngine(store=TaskStore(base_dir=Path(tmpdir) / "tasks"))
        monkeypatch.setattr(task_engine_module, "_engine", engine)
        yield engine, tmpdir


class TestTaskArtifacts:
    def test_attach_task_execution_artifacts_collects_workflow_outputs(self):
        with TemporaryDirectory() as tmpdir:
            task = AgentTask(
                task_id="task-artifacts",
                team_id="team-build",
                title="汇总执行产物",
                metadata={
                    "source": "plaza",
                    "pipeline_dir": tmpdir,
                    "workflow": _build_success_workflow(tmpdir),
                },
            )

            artifacts = api_module._attach_task_execution_artifacts(task)

            assert artifacts["artifact_dir"] == tmpdir
            assert artifacts["changed_files"] == ["src/backend/main.py"]
            assert artifacts["test_result"]["verdict"] == "PASS"
            assert artifacts["workflow_summary"]["completed_steps"] == ["develop", "test", "deploy"]
            assert task.metadata["execution_artifacts"]["build_outcome"] == "completed"


class TestPlazaEvolutionSync:
    @pytest.mark.asyncio
    async def test_finalize_completed_plaza_task_promotes_evolution_item(
        self,
        isolated_task_engine,
        monkeypatch,
    ):
        engine, tmpdir = isolated_task_engine
        evolution_engine = SystemEvolutionChannel()
        evolution_engine.initialize()
        evolution_engine.evolution_items["evo-1"] = EvolutionItem(
            id="evo-1",
            title="让 Plaza 任务完成后进入验证",
            status=EvolutionStatus.DISPATCHED.value,
            source_task_ids=["task-success"],
            source_discussion_id="disc-1",
        )
        monkeypatch.setattr(agent_team_api_module, "_evolution_engine", evolution_engine)

        task = AgentTask(
            task_id="task-success",
            team_id="team-build",
            title="成功任务",
            metadata={
                "source": "plaza",
                "discussion_id": "disc-1",
                "pipeline_dir": tmpdir,
                "workflow": _build_success_workflow(tmpdir),
            },
        )
        await engine.submit_task(task)

        finalized = await api_module._finalize_task_terminal_state(task)

        assert finalized is not None
        assert finalized.status == TaskStatus.COMPLETED
        assert finalized.metadata["changed_files"] == ["src/backend/main.py"]
        assert finalized.result["test_result"]["verdict"] == "PASS"

        item = evolution_engine.evolution_items["evo-1"]
        assert item.status == EvolutionStatus.VERIFY_PENDING.value
        assert item.code_changes == ["src/backend/main.py"]
        assert item.artifact_dir == tmpdir
        assert item.build_artifacts["build_outcome"] == "completed"

    @pytest.mark.asyncio
    async def test_finalize_failed_plaza_task_marks_evolution_failed(
        self,
        isolated_task_engine,
        monkeypatch,
    ):
        engine, tmpdir = isolated_task_engine
        evolution_engine = SystemEvolutionChannel()
        evolution_engine.initialize()
        evolution_engine.evolution_items["evo-2"] = EvolutionItem(
            id="evo-2",
            title="失败任务应阻断演进关闭",
            status=EvolutionStatus.DISPATCHED.value,
            source_task_ids=["task-fail"],
            source_discussion_id="disc-2",
        )
        monkeypatch.setattr(agent_team_api_module, "_evolution_engine", evolution_engine)

        task = AgentTask(
            task_id="task-fail",
            team_id="team-build",
            title="失败任务",
            metadata={
                "source": "plaza",
                "discussion_id": "disc-2",
                "pipeline_dir": tmpdir,
                "workflow": _build_failed_workflow(tmpdir),
            },
        )
        await engine.submit_task(task)

        finalized = await api_module._finalize_task_terminal_state(task)

        assert finalized is not None
        assert finalized.status == TaskStatus.FAILED
        assert finalized.error == "workflow_failed:test"
        assert finalized.metadata["test_result"]["verdict"] == "FAIL"

        item = evolution_engine.evolution_items["evo-2"]
        assert item.status == EvolutionStatus.FAILED.value
        assert item.build_error == "workflow_failed:test"
        assert item.build_artifacts["build_outcome"] == "failed"
