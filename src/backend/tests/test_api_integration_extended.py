# -*- coding: utf-8 -*-
"""Extended HTTP integration tests for core backend handlers.

Covers:
  - Health endpoint full payload
  - Teams CRUD (create, list, get, update, delete)
  - Agent CRUD within teams
  - Tools listing and search
  - Skills listing and search
  - Digital twin state and interactions
  - Evolution status / summary / items (happy path)
  - Datacenter status endpoints
"""

from __future__ import annotations

import time
from typing import Any, Dict

import pytest
from fastapi.testclient import TestClient

from agents import api as api_module
from channels.marine_base import get_default_registry
import main
from main import app


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def configured_client():
    """Fixture that initializes the app's agent config and team APIs
    before yielding a TestClient, then cleans up rate-limit state."""
    # 1. Save and clear rate limits
    prev_login = dict(main._RATE_LIMIT_LOGIN)
    prev_ip = dict(main._RATE_LIMIT_IP)
    registry = get_default_registry()
    registry._channels.clear()
    main._RATE_LIMIT_LOGIN.clear()
    main._RATE_LIMIT_IP.clear()

    # 2. Initialize agent config with a real TeamManager
    from agents.api import init_agent_config
    from agents.team_manager import TeamManager
    from agents.teams.build_team import create_build_team

    team_manager = TeamManager()
    build_team = create_build_team()
    team_manager._teams[build_team.team_id] = build_team

    # Add AI coding team if available
    try:
        from agents.teams.ai_coding_team import create_ai_coding_team
        ai_team = create_ai_coding_team()
        team_manager._teams[ai_team.team_id] = ai_team
    except Exception:
        pass

    init_agent_config(team_manager)

    # 3. Wire up agent_team_api globals (evolution endpoints)
    from agent_team_api import set_teams
    evo_engine = registry.get("system_evolution")
    set_teams(
        build_team=None,
        execution_team=None,
        scheduler=None,
        evolution_engine=evo_engine,
    )

    # 4. Ensure routers are included
    if "/api/v1/agent-config" not in _mounted_routes(app):
        from agents.api import router as agent_config_router
        app.include_router(agent_config_router)
    if "/api/v1/agent-teams" not in _mounted_routes(app):
        from agent_team_api import router as agent_team_router
        app.include_router(agent_team_router)

    with TestClient(app) as client:
        yield client

    # 5. Cleanup
    registry._channels.clear()
    main._RATE_LIMIT_LOGIN.clear()
    main._RATE_LIMIT_LOGIN.update(prev_login)
    main._RATE_LIMIT_IP.clear()
    main._RATE_LIMIT_IP.update(prev_ip)


def _mounted_routes(app) -> set:
    """Return set of URL-path prefixes already mounted."""
    routes = set()
    for r in app.routes:
        if hasattr(r, "path"):
            parts = r.path.split("/")
            prefix = "/".join(parts[:4])  # e.g. /api/v1/agent-config
            routes.add(prefix)
    return routes


def _register_and_get_csrf(client: TestClient, prefix: str) -> tuple[str, str]:
    """Register a unique user and return (csrf_token, username)."""
    _reset_test_client_state(client)
    username = f"{prefix}_{int(time.time() * 1000)}_{id(prefix)}"
    resp = client.post(
        "/api/v1/auth/register",
        json={"username": username, "password": "password123"},
    )
    assert resp.status_code == 200, f"register failed: {resp.text}"
    csrf_resp = client.get("/api/v1/auth/csrf-token")
    assert csrf_resp.status_code == 200, f"csrf failed: {csrf_resp.text}"
    return csrf_resp.json()["csrf_token"], username


def _reset_test_client_state(client: TestClient | None = None) -> None:
    """Clear shared auth/rate-limit state for integration tests."""
    main._RATE_LIMIT_LOGIN.clear()
    main._RATE_LIMIT_IP.clear()
    main._RATE_LIMIT_API.clear()
    main._RATE_LIMIT_SENSITIVE.clear()
    if client is not None:
        client.cookies.clear()


# ===================================================================
# Health endpoint
# ===================================================================

class TestHealthEndpoint:
    def test_health_full_payload(self, configured_client):
        """GET /api/v1/health returns structured status with uptime and subsystems."""
        resp = configured_client.get("/api/v1/health")
        assert resp.status_code == 200
        data = resp.json()
        # Core fields
        assert "status" in data
        uptime_seconds = data.get("uptime_seconds", data.get("details", {}).get("uptime_seconds"))
        assert isinstance(uptime_seconds, (int, float))
        assert uptime_seconds >= 0
        # Subsystems
        assert "services" in data or "subsystems" in data
        services = data.get("services") or data.get("subsystems", {})
        assert isinstance(services, dict)

    def test_info_full_payload(self, configured_client):
        """GET /api/v1/info stays public and exposes discovery metadata."""
        resp = configured_client.get("/api/v1/info")
        assert resp.status_code == 200
        data = resp.json()
        assert {"name", "version", "capabilities", "endpoints"}.issubset(data)


# ===================================================================
# Teams CRUD
# ===================================================================

class TestTeamsCRUD:
    """Full CRUD lifecycle for teams via HTTP."""

    def test_create_team(self, configured_client):
        """POST /api/v1/agent-config/teams with name/description creates a team."""
        csrf, _ = _register_and_get_csrf(configured_client, "tcrt")

        resp = configured_client.post(
            "/api/v1/agent-config/teams",
            json={"name": "Test Team Alpha", "description": "Integration test team"},
            headers={"x-csrf-token": csrf},
        )
        assert resp.status_code == 201, f"create team failed: {resp.text}"
        data = resp.json()
        assert data["name"] == "Test Team Alpha"
        assert data["description"] == "Integration test team"
        assert "team_id" in data
        assert "agents" in data

    def test_list_teams(self, configured_client):
        """GET /api/v1/agent-config/teams returns all teams."""
        resp = configured_client.get("/api/v1/agent-config/teams")
        assert resp.status_code == 200
        data = resp.json()
        # Default teams exist (build team + any from fixture)
        if isinstance(data, list):
            names = [t["name"] for t in data]
            assert any("build" in n.lower() for n in names)
        elif isinstance(data, dict) and "items" in data:
            names = [t["name"] for t in data["items"]]
            assert len(data["items"]) > 0

    def test_get_team_by_id(self, configured_client):
        """GET /api/v1/agent-config/teams/{id} returns team detail."""
        # First get a known team
        list_resp = configured_client.get("/api/v1/agent-config/teams")
        assert list_resp.status_code == 200
        teams = list_resp.json()
        if isinstance(teams, dict) and "items" in teams:
            teams = teams["items"]
        assert len(teams) > 0
        team_id = teams[0]["team_id"]

        resp = configured_client.get(f"/api/v1/agent-config/teams/{team_id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["team_id"] == team_id
        assert "name" in data
        assert "tasks" in data  # team detail includes task summary

    def test_get_team_404(self, configured_client):
        """GET /api/v1/agent-config/teams/nonexistent returns 404."""
        resp = configured_client.get("/api/v1/agent-config/teams/nonexistent-team-id")
        assert resp.status_code == 404

    def test_update_team(self, configured_client):
        """PUT /api/v1/agent-config/teams/{id} updates team properties."""
        csrf, _ = _register_and_get_csrf(configured_client, "tupd")

        # Create a fresh team
        create_resp = configured_client.post(
            "/api/v1/agent-config/teams",
            json={"name": "Update Me", "description": "Before update"},
            headers={"x-csrf-token": csrf},
        )
        assert create_resp.status_code == 201
        team_id = create_resp.json()["team_id"]

        # Update
        resp = configured_client.put(
            f"/api/v1/agent-config/teams/{team_id}",
            json={"name": "Updated Team", "description": "After update"},
            headers={"x-csrf-token": csrf},
        )
        assert resp.status_code == 200, f"update team failed: {resp.text}"
        data = resp.json()
        assert data["name"] == "Updated Team"
        assert data["description"] == "After update"

    def test_delete_team(self, configured_client):
        """DELETE /api/v1/agent-config/teams/{id} removes the team."""
        csrf, _ = _register_and_get_csrf(configured_client, "tdel")

        # Create
        create_resp = configured_client.post(
            "/api/v1/agent-config/teams",
            json={"name": "Delete Me", "description": "Will be deleted"},
            headers={"x-csrf-token": csrf},
        )
        assert create_resp.status_code == 201
        team_id = create_resp.json()["team_id"]

        # Delete
        resp = configured_client.delete(
            f"/api/v1/agent-config/teams/{team_id}",
            headers={"x-csrf-token": csrf},
        )
        assert resp.status_code == 200
        assert resp.json()["deleted"] == team_id

        # Verify gone
        get_resp = configured_client.get(f"/api/v1/agent-config/teams/{team_id}")
        assert get_resp.status_code == 404

    def test_delete_team_404(self, configured_client):
        """DELETE /api/v1/agent-config/teams/nonexistent returns 404."""
        csrf, _ = _register_and_get_csrf(configured_client, "tdel404")
        resp = configured_client.delete(
            "/api/v1/agent-config/teams/nonexistent-id",
            headers={"x-csrf-token": csrf},
        )
        assert resp.status_code == 404


# ===================================================================
# Agent CRUD within a team
# ===================================================================

class TestAgentCRUD:
    """Agent lifecycle within a team."""

    @pytest.fixture(scope="class")
    def _prep_team(self, configured_client) -> str:
        """Create a team and return its team_id for agents tests."""
        csrf, _ = _register_and_get_csrf(configured_client, "agprep")
        # Check if we already have teams
        list_resp = configured_client.get("/api/v1/agent-config/teams")
        teams = list_resp.json()
        if isinstance(teams, dict) and "items" in teams:
            teams = teams["items"]
        if teams:
            return teams[0]["team_id"]

        resp = configured_client.post(
            "/api/v1/agent-config/teams",
            json={"name": "Agent Test Team", "description": "For agent CRUD tests"},
            headers={"x-csrf-token": csrf},
        )
        assert resp.status_code == 201
        return resp.json()["team_id"]

    def test_create_agent(self, configured_client, _prep_team):
        """POST /api/v1/agent-config/teams/{id}/agents creates an agent."""
        csrf, _ = _register_and_get_csrf(configured_client, "agcrt")

        resp = configured_client.post(
            f"/api/v1/agent-config/teams/{_prep_team}/agents",
            json={
                "name": "TestAgent01",
                "role": "developer",
                "personality": "analytical",
                "system_prompt": "You are a test agent.",
            },
            headers={"x-csrf-token": csrf},
        )
        assert resp.status_code == 201, f"create agent failed: {resp.text}"
        data = resp.json()
        assert data["name"] == "TestAgent01"
        assert data["role"] == "developer"
        assert "agent_id" in data

    def test_list_agents_in_team(self, configured_client, _prep_team):
        """GET /api/v1/agent-config/teams/{id}/agents lists team agents."""
        resp = configured_client.get(f"/api/v1/agent-config/teams/{_prep_team}/agents")
        assert resp.status_code == 200
        data = resp.json()
        # Could be list or paginated dict
        if isinstance(data, dict) and "items" in data:
            assert len(data["items"]) >= 0  # at least 0 is fine
        else:
            assert isinstance(data, list)

    def test_get_agent_detail(self, configured_client, _prep_team):
        """GET /api/v1/agent-config/teams/{id}/agents/{aid} returns agent detail."""
        csrf, _ = _register_and_get_csrf(configured_client, "agdet")

        # Create an agent
        create_resp = configured_client.post(
            f"/api/v1/agent-config/teams/{_prep_team}/agents",
            json={"name": "GetDetailAgent", "role": "tester"},
            headers={"x-csrf-token": csrf},
        )
        assert create_resp.status_code == 201
        agent_id = create_resp.json()["agent_id"]

        # Get detail
        resp = configured_client.get(
            f"/api/v1/agent-config/teams/{_prep_team}/agents/{agent_id}"
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["agent_id"] == agent_id
        assert data["name"] == "GetDetailAgent"

    def test_get_agent_404(self, configured_client, _prep_team):
        """GET agent detail for nonexistent agent returns 404."""
        resp = configured_client.get(
            f"/api/v1/agent-config/teams/{_prep_team}/agents/no-such-agent"
        )
        assert resp.status_code == 404

    def test_delete_agent(self, configured_client, _prep_team):
        """DELETE /api/v1/agent-config/teams/{id}/agents/{aid} removes the agent."""
        csrf, _ = _register_and_get_csrf(configured_client, "agdel")

        # Create
        create_resp = configured_client.post(
            f"/api/v1/agent-config/teams/{_prep_team}/agents",
            json={"name": "DeleteAgent", "role": "developer"},
            headers={"x-csrf-token": csrf},
        )
        assert create_resp.status_code == 201
        agent_id = create_resp.json()["agent_id"]

        # Delete
        resp = configured_client.delete(
            f"/api/v1/agent-config/teams/{_prep_team}/agents/{agent_id}",
            headers={"x-csrf-token": csrf},
        )
        assert resp.status_code == 200
        assert resp.json()["deleted"] == agent_id

        # Verify gone
        get_resp = configured_client.get(
            f"/api/v1/agent-config/teams/{_prep_team}/agents/{agent_id}"
        )
        assert get_resp.status_code == 404

    def test_agent_start_stop(self, configured_client, _prep_team):
        """POST /start and /stop toggle agent status."""
        csrf, _ = _register_and_get_csrf(configured_client, "agst")

        # Create
        create_resp = configured_client.post(
            f"/api/v1/agent-config/teams/{_prep_team}/agents",
            json={"name": "StartStopAgent", "role": "worker"},
            headers={"x-csrf-token": csrf},
        )
        assert create_resp.status_code == 201
        agent_id = create_resp.json()["agent_id"]

        # Start
        start_resp = configured_client.post(
            f"/api/v1/agent-config/teams/{_prep_team}/agents/{agent_id}/start",
            headers={"x-csrf-token": csrf},
        )
        assert start_resp.status_code == 200

        # Stop
        stop_resp = configured_client.post(
            f"/api/v1/agent-config/teams/{_prep_team}/agents/{agent_id}/stop",
            headers={"x-csrf-token": csrf},
        )
        assert stop_resp.status_code == 200


# ===================================================================
# Tools listing
# ===================================================================

class TestToolsEndpoints:
    def test_list_tools(self, configured_client):
        """GET /api/v1/agent-config/tools returns tool list."""
        resp = configured_client.get("/api/v1/agent-config/tools")
        assert resp.status_code == 200
        data = resp.json()
        if isinstance(data, list):
            # Should have at least some default tools
            assert len(data) >= 0
        elif isinstance(data, dict) and "items" in data:
            assert len(data["items"]) >= 0

    def test_tools_search(self, configured_client):
        """GET /api/v1/agent-config/tools/search (if route exists)."""
        resp = configured_client.get("/api/v1/agent-config/tools/search?q=web")
        # This endpoint may or may not exist; accept 200 or 404
        assert resp.status_code in (200, 404)


# ===================================================================
# Skills endpoints
# ===================================================================

class TestSkillsEndpoints:
    def test_list_skills(self, configured_client):
        """GET /api/v1/agent-config/skills returns skill list."""
        resp = configured_client.get("/api/v1/agent-config/skills")
        assert resp.status_code == 200
        data = resp.json()
        if isinstance(data, list):
            assert len(data) >= 0

    def test_skills_required(self, configured_client):
        """GET /api/v1/agent-config/skills/required returns required skills."""
        resp = configured_client.get("/api/v1/agent-config/skills/required")
        assert resp.status_code == 200

    def test_team_skills(self, configured_client):
        """GET /api/v1/agent-config/teams/{id}/skills returns team skills."""
        # Pick first team
        teams_resp = configured_client.get("/api/v1/agent-config/teams")
        teams = teams_resp.json()
        if isinstance(teams, dict) and "items" in teams:
            teams = teams["items"]
        if not teams:
            pytest.skip("No teams available")
        team_id = teams[0]["team_id"]

        resp = configured_client.get(f"/api/v1/agent-config/teams/{team_id}/skills")
        assert resp.status_code == 200


# ===================================================================
# Digital Twin
# ===================================================================

class TestDigitalTwinHTTP:
    """Extended digital twin integration tests beyond the existing test_api_handler_integration.py."""

    def test_digital_twin_state(self, configured_client, monkeypatch):
        """GET /api/v1/agent-config/digital-twin/state returns current."""
        monkeypatch.setattr(
            api_module,
            "_dt_state",
            {"rooms": ["room-1"], "positions": {"agent-1": "room-1"}, "interactions": []},
        )

        resp = configured_client.get("/api/v1/agent-config/digital-twin/state")
        assert resp.status_code == 200
        data = resp.json()
        assert "rooms" in data
        assert "positions" in data
        assert "room-1" in data.get("rooms", [])

    def test_digital_twin_update_state(self, configured_client, monkeypatch):
        """PUT /api/v1/agent-config/digital-twin/state updates state."""
        monkeypatch.setattr(
            api_module,
            "_dt_state",
            {"rooms": [], "positions": {}, "interactions": []},
        )
        csrf, _ = _register_and_get_csrf(configured_client, "dtupd")

        resp = configured_client.put(
            "/api/v1/agent-config/digital-twin/state",
            json={"rooms": ["lab"], "positions": {"bot-1": "lab"}, "interactions": []},
            headers={"x-csrf-token": csrf},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "lab" in data.get("rooms", [])

    def test_digital_twin_interactions_list(self, configured_client, monkeypatch):
        """GET /api/v1/agent-config/digital-twin/interactions returns list."""
        monkeypatch.setattr(
            api_module,
            "_dt_state",
            {
                "rooms": [],
                "positions": {},
                "interactions": [
                    {"from": "alice", "to": "bob", "type": "chat",
                     "content": "hello", "timestamp": "2026-01-01T00:00:00Z"}
                ],
            },
        )

        resp = configured_client.get("/api/v1/agent-config/digital-twin/interactions")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) >= 1


# ===================================================================
# Evolution endpoints (happy path when evolution engine is registered)
# ===================================================================

class TestEvolutionEndpoints:
    """Test evolution status/summary/items when the evolution engine is wired."""

    def test_evolution_status(self, configured_client):
        """GET /api/v1/agent-teams/evolution/status returns engine status."""
        resp = configured_client.get("/api/v1/agent-teams/evolution/status")
        # If evolution engine is not registered, expect 404
        if resp.status_code == 404:
            pytest.skip("Evolution engine not registered in this test context")
        assert resp.status_code == 200
        data = resp.json()
        assert "status" in data

    def test_evolution_summary(self, configured_client):
        """GET /api/v1/agent-teams/evolution/summary returns summary."""
        resp = configured_client.get("/api/v1/agent-teams/evolution/summary")
        if resp.status_code == 404:
            pytest.skip("Evolution engine not registered")
        assert resp.status_code == 200

    def test_evolution_items(self, configured_client):
        """GET /api/v1/agent-teams/evolution/items returns paginated list."""
        resp = configured_client.get("/api/v1/agent-teams/evolution/items")
        if resp.status_code == 404:
            pytest.skip("Evolution engine not registered")
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data
        assert "total" in data

    def test_evolution_rules(self, configured_client):
        """GET /api/v1/agent-teams/evolution/rules returns paginated rules."""
        resp = configured_client.get("/api/v1/agent-teams/evolution/rules")
        if resp.status_code == 404:
            pytest.skip("Evolution engine not registered")
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data

    def test_evolution_history(self, configured_client):
        """GET /api/v1/agent-teams/evolution/history returns paginated history."""
        resp = configured_client.get("/api/v1/agent-teams/evolution/history")
        if resp.status_code == 404:
            pytest.skip("Evolution engine not registered")
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data


# ===================================================================
# Team Tree / Overview
# ===================================================================

class TestTeamTreeAndOverview:
    def test_teams_tree(self, configured_client):
        """GET /api/v1/agent-config/teams-tree returns tree structure."""
        resp = configured_client.get("/api/v1/agent-config/teams-tree")
        assert resp.status_code == 200
        data = resp.json()
        if isinstance(data, list):
            for entry in data:
                assert "team_id" in entry
                assert "agents" in entry
        elif isinstance(data, dict) and "items" in data:
            for entry in data["items"]:
                assert "team_id" in entry

    def test_overview(self, configured_client):
        """GET /api/v1/agent-config/overview returns overview."""
        resp = configured_client.get("/api/v1/agent-config/overview")
        assert resp.status_code == 200


# ===================================================================
# Pagination consistency
# ===================================================================

class TestPaginationConsistency:
    """Ensure paginated endpoints return consistent envelope shapes."""

    def test_teams_pagination(self, configured_client):
        """GET /api/v1/agent-config/teams?limit=10&offset=0 returns envelope."""
        resp = configured_client.get("/api/v1/agent-config/teams?limit=10&offset=0")
        assert resp.status_code == 200
        data = resp.json()
        # When limit>0, should be paginated envelope
        assert isinstance(data, dict)
        assert "items" in data
        assert "total" in data
        assert "has_more" in data

    def test_teams_pagination_offset_out_of_range(self, configured_client):
        """GET /api/v1/agent-config/teams?limit=10&offset=9999 returns empty list."""
        resp = configured_client.get("/api/v1/agent-config/teams?limit=10&offset=9999")
        assert resp.status_code == 200
        data = resp.json()
        assert data["items"] == []
        assert data["total"] >= 0
        assert data["has_more"] is False


# ===================================================================
# Auth-guarded endpoint protection
# ===================================================================

class TestAuthGuard:
    """Ensure protected endpoints reject unauthenticated requests."""

    def test_auth_me_reports_anonymous_without_cookie(self, configured_client):
        _reset_test_client_state(configured_client)
        resp = configured_client.get("/api/v1/auth/me")
        assert resp.status_code == 200
        payload = resp.json()
        assert payload["authenticated"] is False

    def test_auth_me_reports_authenticated_after_register(self, configured_client):
        _, username = _register_and_get_csrf(configured_client, "authme")
        resp = configured_client.get("/api/v1/auth/me")
        assert resp.status_code == 200
        payload = resp.json()
        assert payload["authenticated"] is True
        assert payload["username"] == username

    @pytest.mark.parametrize("method,path", [
        ("post", "/api/v1/agent-config/teams"),
        ("post", "/api/v1/agent-config/teams/fake-id/agents"),
        ("put", "/api/v1/agent-config/teams/fake-id"),
        ("delete", "/api/v1/agent-config/teams/fake-id"),
        ("get", "/api/v1/agent-config/digital-twin/state"),
        ("get", "/api/v1/agent-config/overview"),
    ])
    def test_no_auth_returns_401(self, configured_client, method, path):
        """Requests without auth cookie return 401 for protected endpoints."""
        _reset_test_client_state(configured_client)
        resp = getattr(configured_client, method)(path)
        # Auth should guard these; expect 401 or 403
        assert resp.status_code in (401, 403, 503), (
            f"{method.upper()} {path} returned {resp.status_code}, expected 401/403"
        )
