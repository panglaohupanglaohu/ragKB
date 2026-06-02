# -*- coding: utf-8 -*-
"""Regression tests for the datacenter ratchet demo API."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

BACKEND_DIR = Path(__file__).resolve().parents[3] / "src" / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from datacenter_api import _service  # noqa: E402
from main import app  # noqa: E402


@pytest.fixture(scope="module")
def client():
    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_service_state():
    _service.reset()
    _service.reset()


def _csrf_headers(client: TestClient) -> dict[str, str]:
    token = client.get("/api/v1/auth/csrf-token").json()["csrf_token"]
    return {"x-csrf-token": token}


def test_datacenter_status_and_recommendations_exist(client: TestClient):
    status = client.get("/api/v1/datacenter/status")
    recs = client.get("/api/v1/datacenter/recommend?top_n=3")

    assert status.status_code == 200
    assert recs.status_code == 200
    assert status.json()["current_pue"] == pytest.approx(1.85)
    assert len(recs.json()["recommendations"]) == 3


def test_datacenter_loop_tick_and_evolve_update_state(client: TestClient):
    tick = client.post("/api/v1/datacenter/loop/tick", headers=_csrf_headers(client))
    assert tick.status_code == 200
    tick_payload = tick.json()
    assert tick_payload["baseline_pue"] == pytest.approx(1.85)
    assert tick_payload["current_pue"] < tick_payload["baseline_pue"]
    assert tick_payload["verified"] is True

    evolve = client.post(
        "/api/v1/datacenter/evolve",
        json={
            "title": "Closed-loop gain from test",
            "category": "loop",
            "delta_pue": -0.01,
            "delta_kwh_day": 12.0,
        },
        headers=_csrf_headers(client),
    )
    assert evolve.status_code == 200
    assert evolve.json()["heritage"]["title"] == "Closed-loop gain from test"

    heritage = client.get("/api/v1/datacenter/heritage")
    events = client.get("/api/v1/datacenter/events?limit=5")
    history = client.get("/api/v1/datacenter/pue-history?limit=5")

    assert len(heritage.json()["heritage"]) == 1
    assert any(event["kind"] == "darwin_evolve" for event in events.json()["events"])
    assert len(history.json()["history"]) >= 2


def test_datacenter_apply_policy_is_csrf_protected(client: TestClient):
    denied = client.post("/api/v1/datacenter/policies/apply", json={"policy_id": "pol-freecooling", "fitness": 0.91})
    assert denied.status_code == 403

    allowed = client.post(
        "/api/v1/datacenter/policies/apply",
        json={"policy_id": "pol-freecooling", "fitness": 0.91},
        headers=_csrf_headers(client),
    )
    assert allowed.status_code == 200

    status = client.get("/api/v1/datacenter/status").json()
    assert status["policies_applied"] == 1
