# -*- coding: utf-8 -*-
"""Plaza task artifact and evolution bridge tests."""

from __future__ import annotations

import json
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
            assert artifacts["trace_context"]["task_id"] == "task-artifacts"

    def test_attach_task_execution_artifacts_includes_patch_preview(self):
        with TemporaryDirectory() as tmpdir:
            repo_root = Path(api_module.__file__).resolve().parents[3]
            rel_path = "storage/test_artifact_diff_preview.txt"
            current_file = repo_root / rel_path
            current_file.parent.mkdir(parents=True, exist_ok=True)
            backup_file = Path(tmpdir) / "before.txt"
            backup_file.write_text("old line\n", encoding="utf-8")
            current_file.write_text("new line\n", encoding="utf-8")
            try:
                task = AgentTask(
                    task_id="task-diff-preview",
                    team_id="team-build",
                    title="生成 diff 证据",
                    metadata={
                        "source": "plaza",
                        "pipeline_dir": tmpdir,
                        "workflow": [
                            {
                                "key": "deploy",
                                "status": "completed",
                                "deliverable_paths": [rel_path],
                                "deploy_result": {
                                    "developer": {
                                        "applied": [{"path": rel_path}],
                                        "backup": [{"path": rel_path, "backup": str(backup_file)}],
                                        "skipped": [],
                                        "failed": [],
                                    },
                                    "deployer": {"applied": [], "backup": [], "skipped": [], "failed": []},
                                },
                            }
                        ],
                    },
                )

                artifacts = api_module._attach_task_execution_artifacts(task)

                assert rel_path in artifacts["diff_by_file"]
                assert "-old line" in "\n".join(artifacts["diff_by_file"][rel_path])
                assert "+new line" in artifacts["patch_preview"]
                assert task.metadata["patch_preview"] == artifacts["patch_preview"]
            finally:
                if current_file.exists():
                    current_file.unlink()

    def test_attach_task_execution_artifacts_preserves_trace_context(self):
        with TemporaryDirectory() as tmpdir:
            task = AgentTask(
                task_id="task-trace-context",
                team_id="team-build",
                title="追踪上下文",
                metadata={
                    "source": "plaza",
                    "plaza_id": "plaza-1",
                    "discussion_id": "disc-1",
                    "discussion_topic": "trace me",
                    "plan_revision": 4,
                    "plan_item_index": 1,
                    "evolution_item_ids": ["evo-1", "evo-2"],
                    "trace_context": {"custom": "value"},
                    "pipeline_dir": tmpdir,
                    "workflow": _build_success_workflow(tmpdir),
                },
            )

            artifacts = api_module._attach_task_execution_artifacts(task)

            assert artifacts["trace_context"]["task_id"] == "task-trace-context"
            assert artifacts["trace_context"]["discussion_id"] == "disc-1"
            assert artifacts["trace_context"]["evolution_item_ids"] == ["evo-1", "evo-2"]
            assert artifacts["trace_context"]["custom"] == "value"
            trace_file = Path(tmpdir) / "trace_summary.json"
            assert trace_file.exists()
            persisted = json.loads(trace_file.read_text(encoding="utf-8"))
            assert persisted["trace_context"]["task_id"] == "task-trace-context"
            assert persisted["trace_context"]["evolution_item_ids"] == ["evo-1", "evo-2"]


class TestPlazaEvolutionSync:
    @pytest.mark.asyncio
    async def test_finalize_completed_plaza_task_auto_closes_evolution_item(
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
        assert item.status == EvolutionStatus.CLOSED.value
        assert item.code_changes == ["src/backend/main.py"]
        assert item.artifact_dir == tmpdir
        assert item.build_artifacts["build_outcome"] == "completed"
        assert item.verify_result == "passed"
        assert item.closed_at is not None

    @pytest.mark.asyncio
    async def test_finalize_completed_task_keeps_explicit_verify_pending(
        self,
        isolated_task_engine,
        monkeypatch,
    ):
        engine, tmpdir = isolated_task_engine
        evolution_engine = SystemEvolutionChannel()
        evolution_engine.initialize()
        evolution_engine.evolution_items["evo-verify"] = EvolutionItem(
            id="evo-verify",
            title="需要显式验证",
            status=EvolutionStatus.DISPATCHED.value,
            verify_test_name="manual-check",
            source_task_ids=["task-verify"],
            source_discussion_id="disc-verify",
        )
        monkeypatch.setattr(agent_team_api_module, "_evolution_engine", evolution_engine)

        task = AgentTask(
            task_id="task-verify",
            team_id="team-build",
            title="成功但待验证",
            metadata={
                "source": "plaza",
                "discussion_id": "disc-verify",
                "pipeline_dir": tmpdir,
                "workflow": _build_success_workflow(tmpdir),
            },
        )
        await engine.submit_task(task)

        finalized = await api_module._finalize_task_terminal_state(task)

        assert finalized is not None
        item = evolution_engine.evolution_items["evo-verify"]
        assert item.status == EvolutionStatus.VERIFY_PENDING.value
        assert item.verify_result == "pending"
        assert item.verify_detail == "Awaiting verify test: manual-check"

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

    @pytest.mark.asyncio
    async def test_task_trace_summary_endpoint_returns_linked_evolution_items(
        self,
        isolated_task_engine,
        monkeypatch,
        team_manager,
    ):
        engine, tmpdir = isolated_task_engine
        evolution_engine = SystemEvolutionChannel()
        evolution_engine.initialize()
        evolution_engine.evolution_items["evo-trace"] = EvolutionItem(
            id="evo-trace",
            title="追踪项",
            status=EvolutionStatus.CLOSED.value,
            source_task_ids=["task-trace-endpoint"],
            source_discussion_id="disc-trace",
        )
        monkeypatch.setattr(agent_team_api_module, "_evolution_engine", evolution_engine)
        team_manager.create_team(name="追踪团队", team_id="team-build")
        monkeypatch.setattr(api_module, "_team_manager", team_manager)

        task = AgentTask(
            task_id="task-trace-endpoint",
            team_id="team-build",
            title="追踪端点",
            metadata={
                "source": "plaza",
                "plaza_id": "plaza-trace",
                "discussion_id": "disc-trace",
                "evolution_item_ids": ["evo-trace"],
                "trace_context": {"custom": "linked"},
                "pipeline_dir": tmpdir,
                "workflow": _build_success_workflow(tmpdir),
            },
        )
        await engine.submit_task(task)
        await api_module._finalize_task_terminal_state(task)

        summary = api_module.get_task_trace_summary("team-build", "task-trace-endpoint")

        assert summary["task_id"] == "task-trace-endpoint"
        assert summary["trace_context"]["discussion_id"] == "disc-trace"
        assert summary["trace_context"]["custom"] == "linked"
        assert summary["trace_event_count"] >= 2
        assert {event["type"] for event in summary["recent_trace_events"]} >= {
            "task_finalized",
            "evolution_synced",
        }
        assert summary["linked_evolution_items"] == [
            {
                "id": "evo-trace",
                "status": EvolutionStatus.CLOSED.value,
                "title": "追踪项",
                "verify_test_name": None,
                "verify_result": "passed",
                "verify_detail": "Auto-verified from task test results",
                "retry_count": 0,
                "max_retries": 3,
            }
        ]

    @pytest.mark.asyncio
    async def test_task_trace_events_endpoint_returns_persisted_events(
        self,
        isolated_task_engine,
        monkeypatch,
        team_manager,
    ):
        engine, tmpdir = isolated_task_engine
        team_manager.create_team(name="追踪团队", team_id="team-build")
        monkeypatch.setattr(api_module, "_team_manager", team_manager)
        monkeypatch.setattr(agent_team_api_module, "_evolution_engine", SystemEvolutionChannel())

        task = AgentTask(
            task_id="task-trace-events",
            team_id="team-build",
            title="追踪事件端点",
            metadata={
                "source": "plaza",
                "discussion_id": "disc-events",
                "pipeline_dir": tmpdir,
                "workflow": _build_success_workflow(tmpdir),
            },
        )
        await engine.submit_task(task)
        api_module._emit_pipeline_event(task.task_id, "pipeline_started", {"team_id": "team-build"})
        await api_module._finalize_task_terminal_state(task)

        payload = api_module.get_task_trace_events("team-build", "task-trace-events")

        assert payload["task_id"] == "task-trace-events"
        assert payload["count"] >= 2
        assert payload["events"][0]["type"] == "pipeline_started"
        assert payload["events"][0]["trace_context"]["discussion_id"] == "disc-events"
        trace_file = Path(tmpdir) / "trace_events.jsonl"
        assert trace_file.exists()

    @pytest.mark.asyncio
    async def test_discussion_trace_summary_endpoint_returns_all_linked_tasks(
        self,
        isolated_task_engine,
        monkeypatch,
        team_manager,
    ):
        engine, tmpdir = isolated_task_engine
        team_manager.create_team(name="追踪团队", team_id="team-build")
        monkeypatch.setattr(api_module, "_team_manager", team_manager)
        monkeypatch.setattr(agent_team_api_module, "_evolution_engine", SystemEvolutionChannel())

        task_a = AgentTask(
            task_id="task-discussion-a",
            team_id="team-build",
            title="讨论任务 A",
            metadata={
                "source": "plaza",
                "discussion_id": "disc-shared",
                "pipeline_dir": str(Path(tmpdir) / "a"),
                "workflow": _build_success_workflow(str(Path(tmpdir) / "a")),
            },
        )
        task_b = AgentTask(
            task_id="task-discussion-b",
            team_id="team-build",
            title="讨论任务 B",
            metadata={
                "source": "plaza",
                "discussion_id": "disc-shared",
                "pipeline_dir": str(Path(tmpdir) / "b"),
                "workflow": _build_success_workflow(str(Path(tmpdir) / "b")),
            },
        )
        task_other = AgentTask(
            task_id="task-discussion-other",
            team_id="team-build",
            title="无关任务",
            metadata={
                "source": "plaza",
                "discussion_id": "disc-other",
                "pipeline_dir": str(Path(tmpdir) / "other"),
                "workflow": _build_success_workflow(str(Path(tmpdir) / "other")),
            },
        )
        await engine.submit_batch([task_a, task_b, task_other])
        await api_module._finalize_task_terminal_state(task_a)
        await api_module._finalize_task_terminal_state(task_b)
        await api_module._finalize_task_terminal_state(task_other)

        payload = api_module.get_discussion_trace_summary("team-build", "disc-shared")

        assert payload["discussion_id"] == "disc-shared"
        assert payload["count"] == 2
        assert {task["task_id"] for task in payload["tasks"]} == {
            "task-discussion-a",
            "task-discussion-b",
        }
        assert all(task["trace_context"]["discussion_id"] == "disc-shared" for task in payload["tasks"])

    @pytest.mark.asyncio
    async def test_recent_trace_summaries_endpoint_filters_by_team_and_source(
        self,
        isolated_task_engine,
        monkeypatch,
        team_manager,
    ):
        engine, tmpdir = isolated_task_engine
        team_manager.create_team(name="追踪团队", team_id="team-build")
        team_manager.create_team(name="其他团队", team_id="team-other")
        monkeypatch.setattr(api_module, "_team_manager", team_manager)
        monkeypatch.setattr(agent_team_api_module, "_evolution_engine", SystemEvolutionChannel())

        plaza_task = AgentTask(
            task_id="task-recent-plaza",
            team_id="team-build",
            title="最近 Plaza 任务",
            metadata={
                "source": "plaza",
                "discussion_id": "disc-recent",
                "pipeline_dir": str(Path(tmpdir) / "plaza"),
                "workflow": _build_success_workflow(str(Path(tmpdir) / "plaza")),
            },
        )
        other_task = AgentTask(
            task_id="task-recent-other",
            team_id="team-other",
            title="其他来源任务",
            metadata={
                "source": "manual",
                "pipeline_dir": str(Path(tmpdir) / "manual"),
                "workflow": _build_success_workflow(str(Path(tmpdir) / "manual")),
            },
        )
        await engine.submit_batch([plaza_task, other_task])
        await api_module._finalize_task_terminal_state(plaza_task)
        await api_module._finalize_task_terminal_state(other_task)

        payload = api_module.get_recent_trace_summaries(limit=10, team_id="team-build", source="plaza")

        assert payload["count"] == 1
        assert payload["traces"][0]["task_id"] == "task-recent-plaza"
        assert payload["traces"][0]["trace_context"]["discussion_id"] == "disc-recent"
