# -*- coding: utf-8 -*-
"""Startup validator regressions for auth-protected runtime APIs."""

from __future__ import annotations

import httpx
import pytest

from startup_validator import CheckStatus, StartupValidator


def _json_response(payload, status_code: int = 200) -> httpx.Response:
    return httpx.Response(status_code, json=payload)


@pytest.mark.asyncio
async def test_startup_validator_treats_auth_protected_runtime_routes_as_reachable():
    protected_paths = {
        "/api/v1/agent-teams/overview",
        "/api/v1/agent-teams/evolution/status",
        "/api/v1/agent-teams/evolution/summary",
        "/api/v1/agent-config/teams",
        "/api/v1/agent-config/agents",
        "/api/v1/bridge-chat/status",
    }

    def handler(request: httpx.Request) -> httpx.Response:
        path = request.url.path
        if path == "/api/v1/health":
            return _json_response(
                {
                    "status": "ok",
                    "services": {
                        "evolution": True,
                        "bridge_chat": True,
                        "agent_config": True,
                    },
                }
            )
        if path == "/api/v1/info":
            return _json_response(
                {
                    "name": "AgentsGroup2026",
                    "version": "test",
                    "capabilities": ["agent_management"],
                    "endpoints": {"health": "/api/v1/health"},
                }
            )
        if path == "/api/v1/auth/me":
            return _json_response({"authenticated": False, "username": "guest"})
        if path in protected_paths:
            return _json_response({"detail": "auth required"}, status_code=401)
        if path in {"/", "/login.html", "/plaza.html", "/system-evolution.html", "/agent-team-config.html"}:
            return httpx.Response(200, text="<html></html>", headers={"content-type": "text/html"})
        return _json_response({"detail": "not found"}, status_code=404)

    validator = StartupValidator("http://testserver")
    await validator.client.aclose()
    validator.client = httpx.AsyncClient(
        transport=httpx.MockTransport(handler),
        timeout=10.0,
    )

    try:
        report = await validator.run_all()
    finally:
        await validator.close()

    assert report.failed == 0
    assert report.warnings == 0
    by_name = {check.name: check for check in report.checks}
    assert by_name["api_endpoints"].status is CheckStatus.PASS
    assert by_name["agent_config"].status is CheckStatus.PASS
    assert by_name["bridge_chat"].status is CheckStatus.PASS
    assert by_name["evolution_engine"].status is CheckStatus.PASS
    assert by_name["agent_config"].metadata["auth_protected"] is True
    assert by_name["bridge_chat"].metadata["auth_protected"] is True
