# -*- coding: utf-8 -*-
"""HTTP smoke coverage for core protected and public API paths."""

from __future__ import annotations

import time

import pytest
from fastapi.testclient import TestClient

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


class TestCoreApiSmoke:
    def test_health_is_public(self, started_client):
        resp = started_client.get("/api/v1/health")

        assert resp.status_code == 200
        payload = resp.json()
        assert payload["status"] == "ok"

    def test_protected_core_routes_require_auth(self, started_client):
        for path in (
            "/api/v1/agent-teams/overview",
            "/api/v1/agent-teams/evolution/status",
            "/api/v1/agent-config/plaza",
            "/api/v1/agent-config/llm/status",
        ):
            resp = started_client.get(path)
            assert resp.status_code == 401, path

    def test_authenticated_core_routes_return_success(self, started_client):
        token = _register_and_get_csrf(started_client, "coreapi")
        headers = {"x-csrf-token": token}

        teams_resp = started_client.get("/api/v1/agent-config/teams", headers=headers)
        assert teams_resp.status_code == 200
        assert isinstance(teams_resp.json(), list)

        overview_resp = started_client.get("/api/v1/agent-teams/overview", headers=headers)
        assert overview_resp.status_code == 200
        overview = overview_resp.json()
        assert "evolution" in overview

        evolution_resp = started_client.get("/api/v1/agent-teams/evolution/status", headers=headers)
        assert evolution_resp.status_code == 200
        assert "status" in evolution_resp.json()

        plaza_list_resp = started_client.get("/api/v1/agent-config/plaza", headers=headers)
        assert plaza_list_resp.status_code == 200
        plaza_list = plaza_list_resp.json()
        assert "items" in plaza_list
        assert "total" in plaza_list

    def test_authenticated_p1_p2_api_shapes(self, started_client):
        token = _register_and_get_csrf(started_client, "p1p2api")
        headers = {"x-csrf-token": token}

        teams_resp = started_client.get("/api/v1/agent-config/teams", headers=headers)
        assert teams_resp.status_code == 200
        teams = teams_resp.json()
        assert teams
        team_id = teams[0]["team_id"]

        team_resp = started_client.get(f"/api/v1/agent-config/teams/{team_id}", headers=headers)
        assert team_resp.status_code == 200
        team_payload = team_resp.json()
        agents_payload = team_payload.get("agents") or {}
        agent_values = list(agents_payload.values()) if isinstance(agents_payload, dict) else agents_payload
        assert agent_values
        agent_id = agent_values[0]["agent_id"]

        profile_resp = started_client.get(
            f"/api/v1/agent-config/teams/{team_id}/agents/{agent_id}/capability-profile",
            headers=headers,
        )
        assert profile_resp.status_code == 200
        profile = profile_resp.json()
        assert profile["agent_id"] == agent_id
        assert "success_rate" in profile
        assert "capability_score" in profile

        reason_resp = started_client.post(
            f"/api/v1/agent-config/teams/{team_id}/tasks/dispatch-reason",
            json={"agent_id": agent_id, "task_description": "smoke"},
            headers=headers,
        )
        assert reason_resp.status_code == 200
        assert reason_resp.json()["reasons"]

        task_resp = started_client.post(
            "/api/v1/agent-config/cost/generate-task",
            json={
                "team_id": team_id,
                "violation_type": "OVER_BUDGET",
                "resource": "smoke",
                "estimated_saving": 12.5,
            },
            headers=headers,
        )
        assert task_resp.status_code == 200
        task_payload = task_resp.json()
        assert task_payload["task_id"].startswith("cost-")
        assert task_payload["metadata"]["source"] == "cost_gate"

        savings_resp = started_client.get("/api/v1/agent-config/cost/savings-report", headers=headers)
        assert savings_resp.status_code == 200
        assert "total_savings" in savings_resp.json()

        audit_resp = started_client.get("/api/v1/agent-config/audit/recent", headers=headers)
        assert audit_resp.status_code == 200
        assert "entries" in audit_resp.json()

        events_resp = started_client.get("/api/v1/agent-config/runtime/events", headers=headers)
        assert events_resp.status_code == 200
        assert "events" in events_resp.json()

    def test_authenticated_plaza_create_returns_discussion_surface(self, started_client):
        token = _register_and_get_csrf(started_client, "plazacreate")
        resp = started_client.post(
            "/api/v1/agent-config/plaza",
            json={
                "name": "Core API Smoke Plaza",
                "description": "http smoke",
                "selected_agents": [],
                "chairperson_agent_id": "",
            },
            headers={"x-csrf-token": token},
        )

        assert resp.status_code == 201
        payload = resp.json()
        assert payload["name"] == "Core API Smoke Plaza"
        assert "id" in payload
        delete_resp = started_client.delete(
            f"/api/v1/agent-config/plaza/{payload['id']}",
            headers={"x-csrf-token": token},
        )
        assert delete_resp.status_code == 200
        assert delete_resp.json() == {"status": "deleted"}

    def test_logout_revokes_protected_core_access(self, started_client):
        token = _register_and_get_csrf(started_client, "logoutcore")
        headers = {"x-csrf-token": token}

        pre_logout = started_client.get("/api/v1/agent-teams/overview", headers=headers)
        assert pre_logout.status_code == 200

        logout_resp = started_client.post("/api/v1/auth/logout", headers=headers)
        assert logout_resp.status_code == 200
        assert logout_resp.json()["revoked"] is True

        post_logout = started_client.get("/api/v1/agent-teams/overview", headers=headers)
        assert post_logout.status_code == 401

    def test_authenticated_evolution_and_discussion_writes_return_expected_shape(self, started_client):
        token = _register_and_get_csrf(started_client, "evolutionwrite")
        headers = {"x-csrf-token": token}

        audit_resp = started_client.post("/api/v1/agent-teams/evolution/audit", headers=headers)
        assert audit_resp.status_code == 200
        audit_payload = audit_resp.json()
        assert "audit_run" in audit_payload
        assert "details" in audit_payload
        assert "compliance_rating" in audit_payload

        cycle_resp = started_client.post("/api/v1/agent-teams/evolution/cycle", headers=headers)
        assert cycle_resp.status_code == 200
        cycle_payload = cycle_resp.json()
        assert set(cycle_payload) >= {"cycle", "audit", "dispatch", "verify", "closed", "summary"}

        plaza_resp = started_client.post(
            "/api/v1/agent-config/plaza",
            json={
                "name": "Core API Evolution Plaza",
                "description": "http write path",
                "selected_agents": [],
                "chairperson_agent_id": "",
            },
            headers=headers,
        )
        assert plaza_resp.status_code == 201
        plaza_id = plaza_resp.json()["id"]

        discussion_resp = started_client.post(
            f"/api/v1/agent-config/plaza/{plaza_id}/discussions",
            json={
                "topic": "Core API discussion",
                "description": "verify summary shape",
                "goal": "exercise write path",
                "moderator_agent_id": "",
                "max_rounds": 1,
            },
            headers=headers,
        )
        assert discussion_resp.status_code == 201
        discussion_payload = discussion_resp.json()
        assert discussion_payload["topic"] == "Core API discussion"
        assert discussion_payload["status"] == "open"

        discussion_id = discussion_payload["id"]
        summary_resp = started_client.get(
            f"/api/v1/agent-config/plaza/{plaza_id}/discussions/{discussion_id}/summary",
            headers=headers,
        )
        assert summary_resp.status_code == 200
        summary_payload = summary_resp.json()
        assert summary_payload["discussion_id"] == discussion_id
        assert summary_payload["topic"] == "Core API discussion"
        assert "plan_revision" in summary_payload

        delete_resp = started_client.delete(
            f"/api/v1/agent-config/plaza/{plaza_id}",
            headers=headers,
        )
        assert delete_resp.status_code == 200
