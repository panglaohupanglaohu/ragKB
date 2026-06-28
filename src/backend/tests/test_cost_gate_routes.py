from __future__ import annotations

import pytest

from agents import cost_gate_routes


class _FakeGate:
    def get_status(self):
        return {
            "name": "cost_gate",
            "version": "1.0",
            "policies": {"resource_types_count": 3},
            "stats": {"total_evaluations": 2},
            "uptime_seconds": 12.5,
        }

    def get_stats(self):
        return {"total_evaluations": 2, "blocked": 1}


@pytest.mark.asyncio
async def test_cost_gate_health_combines_token_and_terraform(monkeypatch):
    monkeypatch.setattr(cost_gate_routes, "_token_gate_stats", lambda: {"evaluations": 4})
    monkeypatch.setattr(cost_gate_routes, "_get_cost_gate", lambda: _FakeGate())

    payload = await cost_gate_routes.cost_gate_health()

    assert payload["status"] == "healthy"
    assert payload["default_semantics"] == "token"
    assert payload["token"] == {
        "status": "healthy",
        "engine": "token_budget",
        "token_stats": {"evaluations": 4},
    }
    assert payload["terraform"]["status"] == "healthy"
    assert payload["terraform"]["policies_count"] == 3


@pytest.mark.asyncio
async def test_cost_gate_stats_combines_token_and_terraform(monkeypatch):
    monkeypatch.setattr(cost_gate_routes, "_token_gate_stats", lambda: {"evaluations": 4})
    monkeypatch.setattr(cost_gate_routes, "_get_cost_gate", lambda: _FakeGate())

    payload = await cost_gate_routes.get_stats()

    assert payload == {
        "default_semantics": "token",
        "token": {"evaluations": 4},
        "terraform": {"total_evaluations": 2, "blocked": 1},
    }


@pytest.mark.asyncio
async def test_cost_gate_health_uses_unavailable_terraform_fallback(monkeypatch):
    monkeypatch.setattr(cost_gate_routes, "_token_gate_stats", lambda: {})

    def unavailable_gate():
        raise RuntimeError("terraform unavailable")

    monkeypatch.setattr(cost_gate_routes, "_get_cost_gate", unavailable_gate)

    payload = await cost_gate_routes.cost_gate_health()

    assert payload["token"] == {"status": "healthy", "engine": "token_budget"}
    assert payload["terraform"] == {
        "status": "unavailable",
        "reason": "terraform unavailable",
    }
