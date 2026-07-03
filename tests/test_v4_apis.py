# -*- coding: utf-8 -*-
"""v4 API 集成测试 — scenario_api / trial_api 扩展 / evolution_api.

依赖 fastapi（沙箱环境无网络时自动跳过，在本机 venv 中运行）:
    pytest tests/test_v4_apis.py -v
"""

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src", "backend"))

fastapi = pytest.importorskip("fastapi")
from fastapi import FastAPI  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402


@pytest.fixture()
def client():
    """挂载 sandbox + trial + scenario + evolution 路由的测试应用."""
    from sandbox.api import router as sandbox_router, set_orchestrator
    from sandbox.trial_api import router as trial_router
    from sandbox.scenario_api import router as scenario_router
    from sandbox.evolution_api import router as evolution_router
    from sandbox.orchestrator import SECSOrchestrator

    orch = SECSOrchestrator()
    # 注入测试团队世界状态
    orch.sync_world(team_id="teamA", agents=[
        {"id": "a1", "role": "客服专员", "state": "idle",
         "skills": ["ticket_intake", "reply_writing"], "tools": []},
        {"id": "a2", "role": "分类专家", "state": "idle",
         "skills": ["ticket_triage", "kb_search"], "tools": []},
    ])
    set_orchestrator(orch)

    app = FastAPI()
    app.include_router(sandbox_router)
    app.include_router(trial_router)
    app.include_router(scenario_router)
    app.include_router(evolution_router)
    return TestClient(app)


# ── B-1: Scenario API ──────────────────────────────────────

def test_list_scenarios(client):
    r = client.get("/api/v1/scenarios")
    assert r.status_code == 200
    data = r.json()
    assert data["total"] >= 5
    ids = {s["scenario_id"] for s in data["scenarios"]}
    assert "cs_ticket_surge" in ids


def test_get_scenario_detail(client):
    r = client.get("/api/v1/scenarios/cs_ticket_surge")
    assert r.status_code == 200
    spec = r.json()
    assert len(spec["world"]["rooms"]) == 5
    assert len(spec["taskflow"]) == 7


def test_get_scenario_404(client):
    assert client.get("/api/v1/scenarios/nonexistent").status_code == 404


def test_create_scenario_validation_422(client):
    r = client.post("/api/v1/scenarios", json={"spec": {"name": ""}})
    assert r.status_code == 422
    assert "errors" in str(r.json())


def test_scenario_match(client):
    r = client.get("/api/v1/scenarios/cs_ticket_surge/match?team_id=teamA")
    assert r.status_code == 200
    data = r.json()
    assert "match_rate" in data
    assert "missing_skills" in data


# ── B-2: Trial API 扩展 ─────────────────────────────────────

def test_create_trial_with_scenario(client):
    r = client.post("/api/v1/twin-trials", json={
        "team_id": "teamA", "scenario_id": "cs_ticket_surge",
        "task_goal": {"name": "场景试炼"}, "mode": "what_if", "max_steps": 30,
    })
    assert r.status_code == 200
    data = r.json()
    assert data["scenario_id"] == "cs_ticket_surge"
    assert data["generation"] == 0
    assert len(data["rooms"]) == 5


def test_create_trial_with_bad_scenario_404(client):
    r = client.post("/api/v1/twin-trials", json={
        "team_id": "teamA", "scenario_id": "ghost", "mode": "what_if", "max_steps": 30,
    })
    assert r.status_code == 404


def test_trial_lifecycle_with_skill_stats(client):
    """场景试炼 → 步进 → skill-stats → evaluate(skill_breakdown) → feedback."""
    created = client.post("/api/v1/twin-trials", json={
        "team_id": "teamA", "scenario_id": "cs_ticket_surge",
        "task_goal": {"name": "E2E"}, "mode": "what_if", "max_steps": 20,
    }).json()
    trial_id = created["trial_id"]
    session_id = created["session_id"]
    assert session_id

    # 步进若干步（沙箱 session step 接口）
    for _ in range(12):
        client.post(f"/api/v1/sandbox/sessions/{session_id}/step")

    # B-2.2: skill-stats
    r = client.get(f"/api/v1/twin-trials/{trial_id}/skill-stats")
    assert r.status_code == 200
    stats = r.json()
    assert stats["scenario_id"] == "cs_ticket_surge"
    assert isinstance(stats["skills"], list)
    for s in stats["skills"]:
        assert "expected_success_rate" in s
        assert "meets_expectation" in s

    # B-2.3: evaluate 带 skill_breakdown
    r = client.post(f"/api/v1/twin-trials/{trial_id}/evaluate")
    assert r.status_code == 200
    ev = r.json()
    assert "skill_breakdown" in ev
    assert "ratchet" in ev
    assert {"advanced", "generation", "reason"} <= set(ev["ratchet"])
    assert 0 <= ev["total_score"] <= 1

    # SOP 萃取 + B-2.4 真实反哺
    client.post(f"/api/v1/twin-trials/{trial_id}/extract-sop")
    r = client.post(f"/api/v1/twin-trials/{trial_id}/feedback")
    assert r.status_code == 200
    fb = r.json()
    assert fb["reversible"] is True
    assert "skill_versions_created" in fb
    assert "rollback_hint" in fb


def test_list_trials_scenario_filter(client):
    client.post("/api/v1/twin-trials", json={
        "team_id": "teamA", "scenario_id": "marketing_campaign",
        "task_goal": {"name": "f1"}, "mode": "what_if", "max_steps": 20,
    })
    r = client.get("/api/v1/twin-trials?scenario_id=marketing_campaign")
    assert r.status_code == 200
    trials = r.json()["trials"]
    assert all(t["scenario_id"] == "marketing_campaign" for t in trials)
    assert len(trials) >= 1


def test_generation_field_roundtrip(client):
    r = client.post("/api/v1/twin-trials", json={
        "team_id": "teamA", "scenario_id": "cs_ticket_surge",
        "task_goal": {"name": "gen1"}, "mode": "what_if", "max_steps": 20,
        "generation": 1, "parent_trial_id": "parent-x",
    })
    assert r.json()["generation"] == 1
    listed = client.get("/api/v1/twin-trials?generation=1").json()["trials"]
    assert any(t["parent_trial_id"] == "parent-x" for t in listed)


def test_routing_strategy_fork_comparison(client):
    """全局 G3-2: 多策略分支可对照，evaluate 返回 routing_comparison / routing_benefit."""
    created = client.post("/api/v1/twin-trials", json={
        "team_id": "teamA",
        "scenario_id": "cs_ticket_surge",
        "task_goal": {"name": "routing-ab"},
        "mode": "what_if",
        "max_steps": 20,
        "routing_strategy": "proficiency_first",
    }).json()
    trial_id = created["trial_id"]
    base_bid = created["branch_id"]
    assert created["routing_strategy"] == "proficiency_first"

    forked = client.post(f"/api/v1/twin-trials/{trial_id}/branches", json={
        "fork_from_branch_id": base_bid,
        "name": "rr-branch",
        "routing_strategy": "round_robin",
    })
    assert forked.status_code == 200
    fork_bid = forked.json()["branch_id"]
    assert forked.json()["routing_strategy"] == "round_robin"

    # 各跑几步，确保 branch_scores 可生成
    for _ in range(4):
        assert client.post(f"/api/v1/twin-trials/{trial_id}/branches/{base_bid}/step").status_code == 200
        assert client.post(f"/api/v1/twin-trials/{trial_id}/branches/{fork_bid}/step").status_code == 200

    branches = client.get(f"/api/v1/twin-trials/{trial_id}/branches").json()["branches"]
    by_id = {b["id"]: b for b in branches}
    assert by_id[base_bid]["routing_strategy"] == "proficiency_first"
    assert by_id[fork_bid]["routing_strategy"] == "round_robin"

    ev = client.post(f"/api/v1/twin-trials/{trial_id}/evaluate").json()
    assert "routing_comparison" in ev
    cmp = ev["routing_comparison"]
    assert cmp["baseline_branch_id"] == base_bid
    assert any(e["branch_id"] == fork_bid and e["routing_strategy"] == "round_robin" for e in cmp["entries"])
    assert "routing_benefit" in cmp


# ── B-3: Evolution API ──────────────────────────────────────

def test_proficiency_endpoint(client):
    r = client.get("/api/v1/twin-evolution/proficiency?team_id=teamA")
    assert r.status_code == 200
    assert "proficiency" in r.json()


def test_evolution_run_404(client):
    assert client.get("/api/v1/twin-evolution/runs/nonexistent").status_code == 404


def test_evolution_runs_list(client):
    r = client.get("/api/v1/twin-evolution/runs?team_id=teamA")
    assert r.status_code == 200
    assert "runs" in r.json()
