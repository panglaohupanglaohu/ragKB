"""
Tests for CSRF token endpoint + middleware
Verifies token generation, validation, expiry, and state-changing request protection.
"""
import time
import pytest
from fastapi.testclient import TestClient


def _register_user(client: TestClient, username_prefix: str = "csrf_user") -> str:
    username = f"{username_prefix}_{int(time.time() * 1000)}"
    resp = client.post(
        "/api/v1/auth/register",
        json={"username": username, "password": "password123"},
    )
    assert resp.status_code == 200
    return username


@pytest.fixture
def csrf_setup():
    """Import the CSRF helpers directly from main.py"""
    import sys
    from pathlib import Path

    backend_dir = Path(__file__).resolve().parents[3] / "src" / "backend"
    sys.path.insert(0, str(backend_dir))

    from main import _generate_csrf_token, _validate_csrf_token, _CSRF_TOKENS

    # Clean up before each test
    _CSRF_TOKENS.clear()
    yield
    _CSRF_TOKENS.clear()


class TestCsrfGeneration:
    def test_generate_returns_token(self, csrf_setup):
        from main import _generate_csrf_token
        token = _generate_csrf_token()
        assert len(token) > 0
        assert isinstance(token, str)

    def test_generated_token_is_valid(self, csrf_setup):
        from main import _generate_csrf_token, _validate_csrf_token
        token = _generate_csrf_token()
        assert _validate_csrf_token(token) is True

    def test_invalid_token_rejected(self, csrf_setup):
        from main import _validate_csrf_token
        assert _validate_csrf_token("not-a-real-token") is False

    def test_empty_token_rejected(self, csrf_setup):
        from main import _validate_csrf_token
        assert _validate_csrf_token("") is False

    def test_expired_token_rejected(self, csrf_setup):
        from main import _generate_csrf_token, _validate_csrf_token, _CSRF_TOKENS, _CSRF_TTL
        token = _generate_csrf_token()
        # Manually age the token past TTL
        _CSRF_TOKENS[token] = time.time() - _CSRF_TTL - 1
        assert _validate_csrf_token(token) is False
        assert token not in _CSRF_TOKENS  # Should be cleaned up

    def test_tokens_are_unique(self, csrf_setup):
        from main import _generate_csrf_token
        token1 = _generate_csrf_token()
        token2 = _generate_csrf_token()
        assert token1 != token2


class TestCsrfEndpoint:
    @pytest.fixture
    def client(self):
        # This test needs the full app. Try importing from the backend.
        import sys
        from pathlib import Path
        backend_dir = Path(__file__).resolve().parents[3] / "src" / "backend"
        sys.path.insert(0, str(backend_dir))
        from main import app
        return TestClient(app)

    def test_csrf_endpoint_returns_token(self, client):
        resp = client.get("/api/v1/auth/csrf-token")
        assert resp.status_code == 200
        data = resp.json()
        assert "csrf_token" in data
        assert len(data["csrf_token"]) > 0

    def test_post_without_csrf_returns_403(self, client):
        _register_user(client, "csrf_missing")
        resp = client.post("/api/v1/agent-config/tools/web_search/execute",
                           json={"arguments": {"query": "test"}},
                           headers={"Content-Type": "application/json"})
        assert resp.status_code == 403

    def test_post_with_valid_csrf_succeeds(self, client):
        _register_user(client, "csrf_valid")
        # Get a token first
        token_resp = client.get("/api/v1/auth/csrf-token")
        token = token_resp.json()["csrf_token"]

        # Use it in a POST
        resp = client.post("/api/v1/agent-config/tools/web_search/execute",
                           json={"arguments": {"query": "test"}},
                           headers={
                               "Content-Type": "application/json",
                               "x-csrf-token": token,
                           })
        # Should not be 401/403 (may be other errors like missing data, but auth + CSRF passed)
        assert resp.status_code != 403
        assert resp.status_code != 401

    def test_csrf_not_required_for_get(self, client):
        resp = client.get("/api/v1/health")
        assert resp.status_code == 200

    def test_csrf_not_required_for_auth_endpoints(self, client):
        resp = client.post("/api/v1/auth/login",
                           json={"username": "test", "password": "test123"})
        # Should not be 403 (may be 401 for bad credentials, but not CSRF rejection)
        assert resp.status_code != 403

    def test_logout_returns_200(self, client):
        resp = client.post("/api/v1/auth/logout")
        assert resp.status_code == 200
        assert "已登出" in resp.json()["message"]

    def test_register_rate_limit(self, client):
        """Attempt rapid registrations, should be rate-limited after 5 attempts."""
        import time
        results = []
        for i in range(7):
            resp = client.post("/api/v1/auth/register",
                               json={"username": f"testuser_{int(time.time()*1000)}_{i}",
                                      "password": "testpassword123"})
            results.append(resp.status_code)
        # At least one of the later attempts should be 429
        assert 429 in results[-3:], f"Expected rate limiting, got: {results}"

    def test_login_rate_limit(self, client):
        """Attempt rapid failed logins, should be rate-limited."""
        results = []
        for _ in range(7):
            resp = client.post("/api/v1/auth/login",
                               json={"username": "nonexistent_user", "password": "wrong"})
            results.append(resp.status_code)
        # Later attempts should be rate-limited
        assert 429 in results[-3:], f"Expected rate limiting, got: {results}"


@pytest.fixture
def isolated_auth_store(monkeypatch, tmp_path):
    import main

    previous_users = dict(main._USERS)
    previous_tokens = dict(main._TOKENS)
    previous_csrf = dict(main._CSRF_TOKENS)

    monkeypatch.setattr(main, "_USER_STORE", tmp_path / "users.json")
    monkeypatch.setattr(main, "_AUTH_COOKIE_ONLY", False)
    monkeypatch.setattr(main, "_AUTH_RETURN_TOKEN_JSON", True)
    monkeypatch.setattr(main, "_RATE_LIMIT_LOGIN", {})
    monkeypatch.setattr(main, "_RATE_LIMIT_IP", {})
    main._USERS.clear()
    main._TOKENS.clear()
    main._CSRF_TOKENS.clear()

    yield main

    main._USERS.clear()
    main._USERS.update(previous_users)
    main._TOKENS.clear()
    main._TOKENS.update(previous_tokens)
    main._CSRF_TOKENS.clear()
    main._CSRF_TOKENS.update(previous_csrf)


class TestCookieAuthModes:
    @pytest.fixture
    def client(self):
        import sys
        from pathlib import Path
        backend_dir = Path(__file__).resolve().parents[3] / "src" / "backend"
        sys.path.insert(0, str(backend_dir))
        from main import app
        return TestClient(app)

    def test_register_cookie_only_mode_omits_token_json(self, client, isolated_auth_store, monkeypatch):
        monkeypatch.setattr(isolated_auth_store, "_AUTH_COOKIE_ONLY", True)

        resp = client.post(
            "/api/v1/auth/register",
            json={"username": "cookie_user", "password": "password123"},
        )

        assert resp.status_code == 200
        payload = resp.json()
        assert payload["auth_mode"] == "cookie-only"
        assert payload["token_json_enabled"] is False
        assert "token" not in payload
        assert resp.headers["x-ag-auth-mode"] == "cookie-only"
        assert resp.cookies.get("ag-token")

    def test_login_default_mode_returns_deprecated_token_json(self, client, isolated_auth_store):
        client.post(
            "/api/v1/auth/register",
            json={"username": "compat_user", "password": "password123"},
        )

        resp = client.post(
            "/api/v1/auth/login",
            json={"username": "compat_user", "password": "password123"},
        )

        assert resp.status_code == 200
        payload = resp.json()
        assert payload["auth_mode"] == "cookie+token"
        assert payload["token_json_enabled"] is True
        assert payload["token"]
        assert resp.headers["x-ag-token-json"] == "deprecated"

    def test_logout_revokes_token_and_clears_auth_status(self, client, isolated_auth_store):
        login_resp = client.post(
            "/api/v1/auth/register",
            json={"username": "logout_user", "password": "password123"},
        )
        token = login_resp.json()["token"]

        me_before = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert me_before.json()["authenticated"] is True

        logout_resp = client.post(
            "/api/v1/auth/logout",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert logout_resp.status_code == 200
        assert logout_resp.json()["revoked"] is True

        me_after = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert me_after.json()["authenticated"] is False

    def test_auth_me_exposes_cookie_mode_metadata(self, client, isolated_auth_store, monkeypatch):
        monkeypatch.setattr(isolated_auth_store, "_AUTH_COOKIE_ONLY", True)
        client.post(
            "/api/v1/auth/register",
            json={"username": "meta_user", "password": "password123"},
        )

        resp = client.get("/api/v1/auth/me")
        payload = resp.json()

        assert payload["authenticated"] is True
        assert payload["auth_mode"] == "cookie-only"
        assert payload["cookie_only"] is True
        assert payload["token_json_enabled"] is False

    def test_protected_api_requires_auth(self, client):
        resp = client.get("/api/v1/agent-config/plaza")
        assert resp.status_code == 401
        assert "重新登录" in resp.json()["detail"]

    def test_protected_api_allows_cookie_auth(self, client, isolated_auth_store):
        client.post(
            "/api/v1/auth/register",
            json={"username": "protected_user", "password": "password123"},
        )
        resp = client.get("/api/v1/agent-config/teams")
        assert resp.status_code != 401
