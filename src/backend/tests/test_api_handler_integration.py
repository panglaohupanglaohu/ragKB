# -*- coding: utf-8 -*-
"""HTTP-level regressions for selected agent team and digital twin handlers."""

from __future__ import annotations

import time

import pytest
from fastapi.testclient import TestClient

from agents import api as api_module
from channels.marine_base import get_default_registry
import main
from main import app


@pytest.fixture(scope="module")
def started_client():
    registry = get_default_registry()
    previous_rate_limit_login = dict(main._RATE_LIMIT_LOGIN)
    previous_rate_limit_ip = dict(main._RATE_LIMIT_IP)
    registry._channels.clear()
    main._RATE_LIMIT_LOGIN.clear()
    main._RATE_LIMIT_IP.clear()
    with TestClient(app) as client:
        yield client
    registry._channels.clear()
    main._RATE_LIMIT_LOGIN.clear()
    main._RATE_LIMIT_LOGIN.update(previous_rate_limit_login)
    main._RATE_LIMIT_IP.clear()
    main._RATE_LIMIT_IP.update(previous_rate_limit_ip)


def _register_and_get_csrf(client: TestClient, username_prefix: str) -> str:
    username = f"{username_prefix}_{int(time.time() * 1000)}"
    resp = client.post(
        "/api/v1/auth/register",
        json={"username": username, "password": "password123"},
    )
    assert resp.status_code == 200
    csrf_resp = client.get("/api/v1/auth/csrf-token")
    assert csrf_resp.status_code == 200
    return csrf_resp.json()["csrf_token"]


class TestDigitalTwinHandlerIntegration:
    def test_digital_twin_move_validates_request_body(self, started_client):
        token = _register_and_get_csrf(started_client, "dtmove")

        resp = started_client.post(
            "/api/v1/agent-config/digital-twin/move",
            json={"agent_id": "agent-1"},
            headers={"x-csrf-token": token},
        )

        assert resp.status_code == 422

    def test_digital_twin_interact_accepts_from_alias(self, started_client, monkeypatch):
        monkeypatch.setattr(
            api_module,
            "_dt_state",
            {"rooms": [], "positions": {}, "interactions": []},
        )
        token = _register_and_get_csrf(started_client, "dtinteract")

        resp = started_client.post(
            "/api/v1/agent-config/digital-twin/interact",
            json={
                "from": "planner",
                "to": "builder",
                "type": "handoff",
                "content": "ship it",
            },
            headers={"x-csrf-token": token},
        )

        assert resp.status_code == 200
        payload = resp.json()
        assert payload["from"] == "planner"
        assert payload["to"] == "builder"
        assert payload["content"] == "ship it"


class TestAgentTeamEvolutionHandlerIntegration:
    def test_auto_triage_validates_top_n_bounds(self, started_client):
        token = _register_and_get_csrf(started_client, "autotriage")

        resp = started_client.post(
            "/api/v1/agent-teams/evolution/auto-triage",
            json={"team_id": "build_system", "top_n": 11},
            headers={"x-csrf-token": token},
        )

        assert resp.status_code == 422

    def test_dataset_generate_validates_count_bounds(self, started_client):
        token = _register_and_get_csrf(started_client, "datasetgen")

        resp = started_client.post(
            "/api/v1/agent-teams/evolution/dataset/generate",
            json={"skill_id": "skill-a", "team_id": "build_system", "count": 31},
            headers={"x-csrf-token": token},
        )

        assert resp.status_code == 422
