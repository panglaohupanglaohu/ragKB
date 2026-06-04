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
            "/api/v1/agent-config/teams",
            "/api/v1/agent-teams/overview",
            "/api/v1/agent-teams/evolution/status",
            "/api/v1/agent-config/plaza",
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
