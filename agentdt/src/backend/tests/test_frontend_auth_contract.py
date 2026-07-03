# -*- coding: utf-8 -*-
"""Frontend auth/CSRF contract checks for cookie-only mode."""

from __future__ import annotations

import re
from pathlib import Path

FRONTEND_DIR = Path(__file__).resolve().parents[3] / "src" / "frontend"

STATE_CHANGING_FILES = [
    FRONTEND_DIR / "js" / "agent-detail.js",
    FRONTEND_DIR / "js" / "tasks-view.js",
    FRONTEND_DIR / "js" / "wizard.js",
    FRONTEND_DIR / "js" / "agent-team-config.js",
    FRONTEND_DIR / "js" / "token-factory.js",
    FRONTEND_DIR / "js" / "plaza.js",
    FRONTEND_DIR / "datacenter-ratchet-evolution.html",
]

FORBIDDEN_TOKEN_PATTERNS = [
    re.compile(r"localStorage\.getItem\(\s*['\"]ag-token['\"]\s*\)"),
    re.compile(r"localStorage\.setItem\(\s*['\"]ag-token['\"]\s*,"),
    re.compile(r"sessionStorage\.getItem\(\s*['\"]ag-token['\"]\s*\)"),
    re.compile(r"Authorization\s*:\s*['\"]Bearer "),
]

RAW_MUTATION_FETCH = re.compile(r"(?<![_a-zA-Z0-9])fetch\([^)]*\{[^}]*method:\s*['\"](?:POST|PUT|DELETE|PATCH)['\"]", re.S)


def test_frontend_no_longer_reads_or_writes_ag_token():
    for path in FRONTEND_DIR.rglob("*.js"):
        text = path.read_text(encoding="utf-8")
        for pattern in FORBIDDEN_TOKEN_PATTERNS:
            assert not pattern.search(text), f"{path.name} contains forbidden auth token pattern: {pattern.pattern}"

    for path in FRONTEND_DIR.glob("*.html"):
        text = path.read_text(encoding="utf-8")
        for pattern in FORBIDDEN_TOKEN_PATTERNS:
            assert not pattern.search(text), f"{path.name} contains forbidden auth token pattern: {pattern.pattern}"


def test_state_changing_pages_use_csrf_aware_fetch_wrapper():
    for path in STATE_CHANGING_FILES:
        text = path.read_text(encoding="utf-8")
        assert "window._agFetch || fetch" in text, f"{path.name} should declare the shared CSRF-aware fetch wrapper"
        assert not RAW_MUTATION_FETCH.search(text), f"{path.name} still contains a raw state-changing fetch() call"


def test_frontend_sources_do_not_contain_raw_state_changing_fetch_calls():
    for path in FRONTEND_DIR.rglob("*"):
        if path.suffix not in {".js", ".html"}:
            continue
        if "__tests__" in path.parts:
            continue
        text = path.read_text(encoding="utf-8")
        assert not RAW_MUTATION_FETCH.search(text), f"{path.name} still contains a raw state-changing fetch() call"


def test_login_page_uses_shared_api_client_for_auth_flow():
    login_html = (FRONTEND_DIR / "login.html").read_text(encoding="utf-8")
    assert "window.api.request('/api/v1/auth/login'" in login_html
    assert "window.api.request('/api/v1/auth/register'" in login_html
    assert "window.api.setCsrfToken(data.csrf_token);" in login_html
