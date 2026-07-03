# -*- coding: utf-8 -*-
"""Digital-twin room move state-machine regression tests."""

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src", "backend"))

fastapi = pytest.importorskip("fastapi")
from fastapi import FastAPI  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402


@pytest.fixture()
def client():
    from agents import api as agent_api
    from sandbox.api import set_orchestrator
    from sandbox.orchestrator import SECSOrchestrator

    orch = SECSOrchestrator()
    orch.world_state.set_room_stages({"intake": 0, "triage": 1, "reply": 2})
    set_orchestrator(orch)

    agent_api._dt_state["rooms"] = []
    agent_api._dt_state["positions"] = {"agent_a": "intake"}
    agent_api._dt_state["interactions"] = []

    app = FastAPI()
    app.include_router(agent_api.router)
    return TestClient(app), agent_api


def test_digital_twin_move_allows_adjacent_room(client):
    http, agent_api = client

    r = http.post(
        "/api/v1/agent-config/digital-twin/move",
        json={"agent_id": "agent_a", "room_id": "triage"},
    )

    assert r.status_code == 200
    assert r.json()["status"] == "moved"
    assert agent_api._dt_state["positions"]["agent_a"] == "triage"


def test_digital_twin_move_rejects_stage_jump_and_keeps_old_room(client):
    http, agent_api = client

    r = http.post(
        "/api/v1/agent-config/digital-twin/move",
        json={"agent_id": "agent_a", "room_id": "reply"},
    )

    assert r.status_code == 409
    detail = r.json()["detail"]
    assert detail["error"] == "stage_violation"
    assert "违反业务阶段顺序" in detail["reason"]
    assert agent_api._dt_state["positions"]["agent_a"] == "intake"
