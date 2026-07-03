"""Agent execution EvidenceRun regressions."""

from __future__ import annotations

import pytest

from agents import evidence_store as evidence_store_module
from agents.evidence_store import EvidenceQuery, EvidenceStore
from agents.task_engine import AgentTask, TaskEngine
from agents.tool_executor import ToolExecutor


class FakeTaskStore:
    def __init__(self) -> None:
        self.tasks = {}

    def load_all(self):
        return {}

    def save_task(self, task: AgentTask) -> None:
        self.tasks[task.task_id] = task

    def delete_task(self, task_id: str) -> None:
        self.tasks.pop(task_id, None)


@pytest.mark.asyncio
async def test_tool_executor_records_tool_call_evidence(monkeypatch, tmp_path):
    evidence_store = EvidenceStore(str(tmp_path / "evidence_runs"))
    monkeypatch.setattr(evidence_store_module, "_evidence_store", evidence_store)

    result = await ToolExecutor().execute(
        "list_directory",
        {"path": str(tmp_path), "request_id": "req-tool"},
        agent_id="agent-001",
    )

    assert result.success is True
    runs = await evidence_store.query_evidence(EvidenceQuery(evidence_type="tool_call"))
    assert len(runs) == 1
    assert runs[0].status == "passed"
    assert runs[0].agent_id == "agent-001"
    assert runs[0].request_id == "req-tool"
    assert runs[0].runtime["tool_name"] == "list_directory"
    assert runs[0].command == "list_directory"


@pytest.mark.asyncio
async def test_task_engine_records_completion_evidence(monkeypatch, tmp_path):
    evidence_store = EvidenceStore(str(tmp_path / "evidence_runs"))
    monkeypatch.setattr(evidence_store_module, "_evidence_store", evidence_store)
    engine = TaskEngine(store=FakeTaskStore())
    task = AgentTask(
        task_id="task-001",
        agent_id="agent-001",
        team_id="cloud_ops",
        title="Optimize cloud cost",
        metadata={"request_id": "req-task"},
    )

    await engine.submit_task(task)
    await engine.complete_task("task-001", result={"ok": True})

    runs = await evidence_store.query_evidence(EvidenceQuery(evidence_type="agent_task"))
    assert len(runs) == 1
    assert runs[0].status == "passed"
    assert runs[0].team_id == "cloud_ops"
    assert runs[0].agent_id == "agent-001"
    assert runs[0].task_id == "task-001"
    assert runs[0].request_id == "req-task"
    assert runs[0].runtime["component"] == "task_engine"
