# -*- coding: utf-8 -*-
"""
AgentsGroup2026 — Centralized Configuration

Reads environment variables with sensible defaults.
All application constants should live here, not scattered across modules.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict

# Load .env file if python-dotenv is available
try:
    from dotenv import load_dotenv
    _env_path = Path(__file__).resolve().parent.parent.parent / ".env"
    if _env_path.exists():
        load_dotenv(_env_path)
except ImportError:
    pass


# ── Server ──
HOST: str = os.getenv("AG_HOST", "0.0.0.0")
PORT: int = int(os.getenv("AG_PORT", "8080"))
RELOAD: bool = os.getenv("AG_RELOAD", "").lower() in {"1", "true", "yes"}

# ── CORS ──
_DEFAULT_CORS_ORIGINS = (
    "http://localhost:5173,"
    "http://127.0.0.1:5173,"
    "http://localhost:8080,"
    "http://127.0.0.1:8080"
)
ALLOWED_ORIGINS: list[str] = [
    o.strip()
    for o in os.getenv("AG_ALLOWED_ORIGINS", _DEFAULT_CORS_ORIGINS).split(",")
    if o.strip()
]
CORS_ALLOW_CREDENTIALS: bool = os.getenv("AG_CORS_ALLOW_CREDENTIALS", "1").lower() not in {"0", "false", "no"}

# ── Auth ──
PBKDF2_ITERATIONS: int = int(os.getenv("AG_PBKDF2_ITERATIONS", "260000"))
TOKEN_TTL: int = 86400 * 7  # 7 days
CSRF_TTL: int = 3600  # 1 hour
ALLOW_DEFAULT_ADMIN: bool = os.getenv("AG_ALLOW_DEFAULT_ADMIN", "").lower() in {"1", "true", "yes"}
RATE_LOGIN_LIMIT: int = int(os.getenv("AG_RATE_LOGIN_LIMIT", "5"))
RATE_LIMIT_WINDOW: int = int(os.getenv("AG_RATE_LIMIT_WINDOW", "60"))
RATE_API_LIMIT: int = int(os.getenv("AG_RATE_API_LIMIT", "60"))
RATE_SENSITIVE_LIMIT: int = int(os.getenv("AG_RATE_SENSITIVE_LIMIT", "20"))

# ── Startup ──
STRICT_STARTUP: bool = os.getenv("AG_STRICT_STARTUP", "1").lower() not in {"0", "false", "no"}

# ── Pagination ──
DEFAULT_PAGE_SIZE: int = 50
MAX_PAGE_SIZE: int = 200

# ── Paths ──
BACKEND_DIR: Path = Path(__file__).resolve().parent
PROJECT_ROOT: Path = BACKEND_DIR.parents[1]
FRONTEND_DIR: Path = PROJECT_ROOT / "src" / "frontend"
USER_STORE_PATH: Path = PROJECT_ROOT / "config" / "users.json"

# ── Logging ──
LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

# ── Version ──
VERSION: str = "1.0.0"
