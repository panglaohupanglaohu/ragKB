# -*- coding: utf-8 -*-
"""Tests for security response headers and request_id middleware."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

_backend_root = Path(__file__).resolve().parent.parent
if str(_backend_root) not in sys.path:
    sys.path.insert(0, str(_backend_root))

import main


@pytest.fixture
def client():
    return TestClient(main.app, raise_server_exceptions=False)


class TestSecurityHeaders:
    """Verify security headers are present on all responses."""

    def test_x_content_type_options(self, client):
        r = client.get("/api/v1/health")
        assert r.headers.get("x-content-type-options") == "nosniff"

    def test_x_frame_options(self, client):
        r = client.get("/api/v1/health")
        assert r.headers.get("x-frame-options") == "DENY"

    def test_referrer_policy(self, client):
        r = client.get("/api/v1/health")
        assert r.headers.get("referrer-policy") == "strict-origin-when-cross-origin"

    def test_permissions_policy(self, client):
        r = client.get("/api/v1/health")
        assert "camera=()" in r.headers.get("permissions-policy", "")

    def test_hsts_disabled_by_default(self, client):
        r = client.get("/api/v1/health")
        assert "strict-transport-security" not in r.headers


class TestRequestId:
    """Verify request_id middleware behavior."""

    def test_response_has_request_id(self, client):
        r = client.get("/api/v1/health")
        assert "x-request-id" in r.headers
        assert len(r.headers["x-request-id"]) == 16  # secrets.token_hex(8)

    def test_upstream_request_id_forwarded(self, client):
        r = client.get("/api/v1/health", headers={"x-request-id": "upstream-12345"})
        assert r.headers["x-request-id"] == "upstream-12345"

    def test_different_requests_get_different_ids(self, client):
        r1 = client.get("/api/v1/health")
        r2 = client.get("/api/v1/health")
        assert r1.headers["x-request-id"] != r2.headers["x-request-id"]
