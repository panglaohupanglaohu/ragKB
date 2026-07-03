"""System evolution item evidence detail regressions."""

from __future__ import annotations

import pytest
from fastapi import HTTPException

import agent_team_api as agent_team_api_module
from agent_team_api import EvolutionCloseRequest, EvolutionCompleteRequest
from agents import evidence_store as evidence_store_module
from agents.evidence_store import EvidenceRun, EvidenceStore
from channels.system_evolution import EvolutionItem, EvolutionStatus, SystemEvolutionChannel


@pytest.mark.asyncio
async def test_evolution_item_detail_includes_evidence_runs(monkeypatch, tmp_path):
    evidence_store = EvidenceStore(str(tmp_path / "evidence_runs"))
    monkeypatch.setattr(evidence_store_module, "_evidence_store", evidence_store)
    channel = SystemEvolutionChannel()
    item = EvolutionItem(
        id="EVO-test-01",
        title="Add evidence detail",
        status=EvolutionStatus.VERIFIED.value,
        build_task_id="task-001",
        verify_result="passed",
        verify_detail="pytest passed",
    )
    channel.evolution_items[item.id] = item
    monkeypatch.setattr(agent_team_api_module, "_evolution_engine", channel)
    evidence_store.append_evidence_sync(EvidenceRun.create(
        evidence_type="evolution_verify",
        status="passed",
        evolution_item_id=item.id,
        task_id="task-001",
        command="system_evolution.verify:test",
        exit_code=0,
        runtime={"mode": "in_process", "component": "system_evolution"},
    ))

    detail = await agent_team_api_module.evolution_item_detail(item.id)

    assert detail["id"] == item.id
    assert detail["evidence_runs"]
    assert detail["evidence_runs"][0]["evidence_type"] == "evolution_verify"
    assert detail["evidence_runs"][0]["command"] == "system_evolution.verify:test"


@pytest.mark.asyncio
async def test_evolution_close_item_records_reason_and_conclusion(monkeypatch):
    channel = SystemEvolutionChannel()
    item = EvolutionItem(
        id="EVO-test-02",
        title="Close with proof",
        status=EvolutionStatus.VERIFIED.value,
        verify_result="passed",
    )
    channel.evolution_items[item.id] = item
    monkeypatch.setattr(agent_team_api_module, "_evolution_engine", channel)

    result = await agent_team_api_module.evolution_close_item(
        item.id,
        EvolutionCloseRequest(reason="human reviewed diff", verify_conclusion="tests passed"),
    )

    assert result["closed"] == [item.id]
    assert item.status == EvolutionStatus.CLOSED.value
    assert item.close_reason == "human reviewed diff"
    assert item.close_verify_conclusion == "tests passed"


@pytest.mark.asyncio
async def test_evolution_complete_requires_and_records_build_evidence(monkeypatch):
    channel = SystemEvolutionChannel()
    item = EvolutionItem(
        id="EVO-test-03",
        title="Complete with artifacts",
        status=EvolutionStatus.IN_PROGRESS.value,
    )
    channel.evolution_items[item.id] = item
    monkeypatch.setattr(agent_team_api_module, "_evolution_engine", channel)

    with pytest.raises(HTTPException) as exc:
        await agent_team_api_module.evolution_mark_complete(item.id, EvolutionCompleteRequest())
    assert exc.value.status_code == 400
    assert item.status == EvolutionStatus.IN_PROGRESS.value

    result = await agent_team_api_module.evolution_mark_complete(
        item.id,
        EvolutionCompleteRequest(
            code_changes=["src/backend/channels/system_evolution.py"],
            artifact_dir="storage/evolution_runs/EVO-test-03",
        ),
    )

    assert result["new_status"] == EvolutionStatus.VERIFY_PENDING.value
    assert item.status == EvolutionStatus.VERIFY_PENDING.value
    assert item.code_changes == ["src/backend/channels/system_evolution.py"]
    assert item.artifact_dir == "storage/evolution_runs/EVO-test-03"
