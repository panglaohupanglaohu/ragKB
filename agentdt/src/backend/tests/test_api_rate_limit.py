# -*- coding: utf-8 -*-
"""Regression tests for generic API rate limiting buckets."""

from __future__ import annotations

import sys
import uuid
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

BACKEND_DIR = Path(__file__).resolve().parents[3] / "src" / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

import main  # noqa: E402
from datacenter_api import _service  # noqa: E402


@pytest.fixture(scope="module")
def client():
    with TestClient(main.app) as test_client:
        yield test_client


@pytest.fixture(autouse=True)
def isolate_rate_limits(monkeypatch):
    monkeypatch.setattr(main, "_RATE_LIMIT_API", {})
    monkeypatch.setattr(main, "_RATE_LIMIT_SENSITIVE", {})
    monkeypatch.setattr(main, "_RATE_LIMIT_LOGIN", {})
    monkeypatch.setattr(main, "_RATE_LIMIT_IP", {})
    _service.reset()


def _csrf_headers(client: TestClient) -> dict[str, str]:
    token = client.get("/api/v1/auth/csrf-token").json()["csrf_token"]
    return {"x-csrf-token": token}


def _authenticate(client: TestClient, prefix: str = "ratelimit_user") -> str:
    client.cookies.clear()
    username = f"{prefix}_{uuid.uuid4().hex[:8]}"
    resp = client.post(
        "/api/v1/auth/register",
        json={"username": username, "password": "password123"},
    )
    assert resp.status_code == 200
    return username


def test_generic_api_rate_limit_caps_write_requests(client: TestClient, monkeypatch):
    monkeypatch.setattr(main, "_RATE_API_LIMIT", 3)
    monkeypatch.setattr(main, "_RATE_LIMIT_SENSITIVE_PATHS", {})
    monkeypatch.setattr(main, "_RATE_LIMIT_SENSITIVE_PREFIXES", {})
    _authenticate(client, "ratelimit_generic")

    statuses = []
    for _ in range(4):
        resp = client.post("/api/v1/datacenter/evolve", json={"title": "x"}, headers=_csrf_headers(client))
        statuses.append(resp.status_code)

    assert statuses[:3] == [200, 200, 200]
    assert statuses[3] == 429


def test_sensitive_api_uses_tighter_bucket(client: TestClient, monkeypatch):
    monkeypatch.setattr(main, "_RATE_API_LIMIT", 10)
    monkeypatch.setattr(main, "_RATE_SENSITIVE_LIMIT", 2)
    monkeypatch.setattr(
        main,
        "_RATE_LIMIT_SENSITIVE_PATHS",
        {
            "/api/v1/datacenter/loop/tick": 2,
        },
    )
    _authenticate(client, "ratelimit_sensitive")

    statuses = []
    for _ in range(3):
        resp = client.post("/api/v1/datacenter/loop/tick", headers=_csrf_headers(client))
        statuses.append(resp.status_code)

    assert statuses[:2] == [200, 200]
    assert statuses[2] == 429
    assert client.post("/api/v1/datacenter/evolve", json={"title": "ok"}, headers=_csrf_headers(client)).status_code == 200


def test_auth_and_read_routes_are_exempt_from_api_bucket(client: TestClient, monkeypatch):
    monkeypatch.setattr(main, "_RATE_API_LIMIT", 1)
    monkeypatch.setattr(main, "_RATE_LIMIT_SENSITIVE_PATHS", {})
    monkeypatch.setattr(main, "_RATE_LIMIT_SENSITIVE_PREFIXES", {})

    assert client.get("/api/v1/health").status_code == 200
    assert client.get("/api/v1/health").status_code == 200

    register = client.post(
        "/api/v1/auth/register",
        json={"username": f"ratelimit_user_exempt_case_{uuid.uuid4().hex[:8]}", "password": "password123"},
    )
    assert register.status_code == 200
