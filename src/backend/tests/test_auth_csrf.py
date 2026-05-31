"""
Tests for CSRF token endpoint + middleware
Verifies token generation, validation, expiry, and state-changing request protection.
"""
import time
import pytest
from fastapi.testclient import TestClient


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
        resp = client.post("/api/v1/agent-config/tools/web_search/execute",
                           json={"arguments": {"query": "test"}},
                           headers={"Content-Type": "application/json"})
        assert resp.status_code == 403

    def test_post_with_valid_csrf_succeeds(self, client):
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
        # Should not be 403 (may be other errors like missing data, but not CSRF)
        assert resp.status_code != 403

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
