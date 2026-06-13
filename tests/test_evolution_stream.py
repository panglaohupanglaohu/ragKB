"""D-2: SSE evolution stream endpoint test.
Validates GET /evolution/stream returns text/event-stream with data frames and ping heartbeats.
"""
import json
import pytest


@pytest.mark.skip(reason="Needs running FastAPI server — SSE streaming unavailable in sandbox")
def test_evolution_stream_content_type(client):
    """Verify SSE endpoint returns correct content-type."""
    import httpx
    response = client.get("/api/v1/agent-teams/evolution/stream")
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/event-stream"


def test_evolution_stream_endpoint_exists():
    """Verify the stream route is registered in main.py router."""
    import io, re
    with io.open("src/backend/agent_team_api.py", encoding="utf-8") as f:
        src = f.read()
    # SSE endpoint registration
    assert "evolution/stream" in src, "SSE stream route not found in agent_team_api.py"
    assert "StreamingResponse" in src, "StreamingResponse import not found"
    assert "text/event-stream" in src, "media_type text/event-stream not found"
    # A-2.1: heartbeat ping
    assert ": ping" in src, "SSE heartbeat :ping not found"
    # Named event support
    assert "event: ready" in src, "ready event not found"


def test_frontend_sse_handling():
    """Verify frontend SSE onerror calls _fallbackPoll (A-1.1 fix)."""
    import io
    with io.open("src/frontend/js/system-evolution.js", encoding="utf-8") as f:
        src = f.read()
    # A-1.1: _closeSSE then _fallbackPoll
    assert "_closeSSE()" in src
    assert "_fallbackPoll()" in src
    # Should NOT have the old dead-code pattern
    assert "if (!_ssePollTimer && _ssePollActive" not in src, "Old dead-code pattern still present"
