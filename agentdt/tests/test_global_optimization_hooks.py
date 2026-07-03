# -*- coding: utf-8 -*-
"""Global optimization hook smoke tests (G1-1 / G3-3)."""

import os
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src", "backend"))

fastapi = pytest.importorskip("fastapi")


@pytest.mark.asyncio
async def test_plaza_consensus_auto_creates_extraction_pipeline(tmp_path):
    from agents.extraction_store import init_extraction_store
    from agents.plaza_engine import PlazaEngine

    store = init_extraction_store(storage_dir=tmp_path / "pipelines")
    disc = SimpleNamespace(
        id="disc_auto_extract",
        plaza_id="plaza_auto",
        team_id="teamA",
        topic="沉淀客服高峰期 SOP",
        summary="共识：把高峰期分流和回复模板沉淀为可验证技能。",
        plan={"content": "1. 收集高峰票据\n2. 形成回复模板\n3. 验证并发布"},
    )

    await PlazaEngine()._auto_extract_on_consensus(disc)

    pipelines = await store.list_pipelines()
    assert len(pipelines) == 1
    pipe = pipelines[0]
    assert pipe.created_by == "plaza:disc_auto_extract"
    assert "classification:reserve" in pipe.tags
    assert "共识" in pipe.description


def test_trial_evaluate_writes_skill_router_feedback(monkeypatch, tmp_path):
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    from sandbox.api import router as sandbox_router, set_orchestrator
    from sandbox.orchestrator import SECSOrchestrator
    from sandbox.proficiency_store import reset_proficiency_store
    from sandbox.trial_api import router as trial_router

    orch = SECSOrchestrator()
    orch.sync_world(team_id="teamA", agents=[
        {"id": "agent_a", "role": "analyst", "state": "idle",
         "skills": ["ticket_triage"], "tools": []},
    ])
    set_orchestrator(orch)
    prof = reset_proficiency_store(
        usage_dir=tmp_path / "usages",
        prof_dir=tmp_path / "proficiency",
    )

    calls = []

    class FakeSkillRouter:
        def submit_feedback(self, team_id, agent_id, skill_id, action, rating, reason):
            calls.append({
                "team_id": team_id,
                "agent_id": agent_id,
                "skill_id": skill_id,
                "action": action,
                "rating": rating,
                "reason": reason,
            })
            return {"status": "ok"}

    import agents.skill_router as skill_router

    monkeypatch.setattr(skill_router, "get_skill_router", lambda: FakeSkillRouter())

    app = FastAPI()
    app.include_router(sandbox_router)
    app.include_router(trial_router)
    client = TestClient(app)

    created = client.post("/api/v1/twin-trials", json={
        "team_id": "teamA",
        "task_goal": {"name": "router feedback"},
        "mode": "what_if",
        "max_steps": 10,
    }).json()
    trial_id = created["trial_id"]

    prof.append_usages(trial_id, [
        {"agent_id": "agent_a", "skill_name": "ticket_triage", "outcome": "success", "reward_delta": 0.2},
        {"agent_id": "agent_a", "skill_name": "ticket_triage", "outcome": "success", "reward_delta": 0.1},
        {"agent_id": "agent_a", "skill_name": "ticket_triage", "outcome": "failure", "reward_delta": -0.1},
    ])

    r = client.post(f"/api/v1/twin-trials/{trial_id}/evaluate")
    assert r.status_code == 200
    assert calls == [{
        "team_id": "teamA",
        "agent_id": "agent_a",
        "skill_id": "ticket_triage",
        "action": "rate",
        "rating": 4,
        "reason": f"twin_trial:{trial_id} 成功率 2/3",
    }]
