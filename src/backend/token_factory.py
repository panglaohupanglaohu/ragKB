"""Token Factory API — LLM inference infrastructure health & management.

Provides endpoints for:
- Health check (Ollama, DeepSeek, Claude Code connectivity)
- SSH tunnel management (remote GPU)
- Ollama probe & ensure-ready
- Claude Code connectivity test
"""
from __future__ import annotations

import json
import logging
import os
import subprocess
import time
from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException

logger = logging.getLogger("token_factory")

router = APIRouter(prefix="/api/v1/token-factory", tags=["Token Factory"])

_CONFIG_DIR = Path(__file__).resolve().parents[3] / "config"
_SETTINGS_PATH = _CONFIG_DIR / "settings.json"


def _load_settings() -> dict:
    try:
        if _SETTINGS_PATH.exists():
            return json.loads(_SETTINGS_PATH.read_text())
    except Exception:
        pass
    return {}


def _check_http(url: str, timeout: float = 3.0) -> tuple:
    """Check if an HTTP endpoint is reachable. Returns (ok: bool, latency_ms: float, error: str)."""
    import http.client
    import ssl
    from urllib.parse import urlparse

    parsed = urlparse(url)
    conn = None
    try:
        t0 = time.monotonic()
        if parsed.scheme == "https":
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            conn = http.client.HTTPSConnection(parsed.hostname, parsed.port or 443, timeout=timeout, context=ctx)
        else:
            conn = http.client.HTTPConnection(parsed.hostname, parsed.port or 80, timeout=timeout)
        conn.request("GET", parsed.path or "/")
        resp = conn.get_response()
        resp.read()
        lat = (time.monotonic() - t0) * 1000
        return resp.status < 500, lat, ""
    except Exception as e:
        return False, 0, str(e)
    finally:
        if conn:
            try:
                conn.close()
            except Exception:
                pass


def _check_process(pid: int) -> bool:
    """Check if a process with given PID is running."""
    try:
        os.kill(pid, 0)
        return True
    except (OSError, ProcessLookupError):
        return False


@router.get("/health")
async def health() -> Dict[str, Any]:
    """Return health status of all LLM providers."""
    settings = _load_settings()
    sandbox = settings.get("sandbox", {})
    tunnel = settings.get("tunnel", {})
    ollama_cfg = settings.get("ollama", {})
    deepseek_cfg = settings.get("deepseek", {})
    claude_cfg = settings.get("claude_code", {})

    # Check Ollama
    ollama_url = ollama_cfg.get("url", "http://127.0.0.1:11434")
    ollama_ok, ollama_lat, ollama_err = _check_http(f"{ollama_url}/api/tags")

    # Check DeepSeek
    ds_url = deepseek_cfg.get("base_url", "https://api.deepseek.com")
    ds_ok, ds_lat, ds_err = _check_http(f"{ds_url}/v1/models") if ds_url else (False, 0, "not configured")

    # Check Claude Code
    cc_url = claude_cfg.get("base_url", "http://127.0.0.1:11435")
    cc_ok, cc_lat, cc_err = _check_http(cc_url) if cc_url else (False, 0, "not configured")

    # SSH Tunnel
    tunnel_state = "unknown"
    tunnel_pid = tunnel.get("pid", None)
    if tunnel_pid:
        tunnel_state = "running" if _check_process(tunnel_pid) else "stopped"
    else:
        tunnel_state = "not_started"

    proxy_port = ollama_cfg.get("proxy_port", 11435)
    proxy_ok, proxy_lat, _ = _check_http(f"http://127.0.0.1:{proxy_port}") if proxy_port else (False, 0, "")

    return {
        "ready": bool(ollama_ok or ds_ok or cc_ok),
        "providers": {
            "ollama_local": {
                "reachable": ollama_ok,
                "latency_ms": round(ollama_lat, 2),
                "error": ollama_err,
                "url": ollama_url,
            },
            "deepseek": {
                "reachable": ds_ok,
                "latency_ms": round(ds_lat, 2),
                "error": ds_err,
                "url": ds_url,
            },
            "claude_code": {
                "ok": cc_ok or proxy_ok,
                "latency_ms": round(cc_lat or proxy_lat, 2),
                "error": cc_err,
                "url": cc_url,
            },
        },
        "tunnel": {
            "state": tunnel_state,
            "pid": tunnel_pid,
        },
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }


@router.post("/ensure-ready")
async def ensure_ready() -> Dict[str, Any]:
    """Ensure all providers are ready; attempt to start tunnel if configured."""
    h = await health()
    if h["ready"]:
        return {**h, "status": "already_ready"}

    # Try to start tunnel
    settings = _load_settings()
    tunnel = settings.get("tunnel", {})
    if tunnel.get("enabled"):
        try:
            result = subprocess.run(
                ["ssh", "-f", "-N", "-L",
                 f"{tunnel.get('local_port',11434)}:{tunnel.get('remote_host','localhost')}:{tunnel.get('remote_port',11434)}",
                 tunnel.get("ssh_host", "remote-gpu")],
                capture_output=True, text=True, timeout=10,
            )
            if result.returncode == 0:
                time.sleep(1)
                h2 = await health()
                return {**h2, "status": "started", "pid": None}
        except Exception as e:
            logger.warning(f"Tunnel start failed: {e}")

    return {**h, "status": "not_ready"}


@router.post("/tunnel/start")
async def tunnel_start() -> Dict[str, Any]:
    """Start SSH tunnel to remote GPU."""
    settings = _load_settings()
    tunnel = settings.get("tunnel", {})
    if not tunnel:
        raise HTTPException(400, "Tunnel not configured")

    try:
        cmd = [
            "ssh", "-f", "-N",
            "-L", f"{tunnel.get('local_port',11434)}:{tunnel.get('remote_host','localhost')}:{tunnel.get('remote_port',11434)}",
            tunnel.get("ssh_host", "remote-gpu"),
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            return {"status": "started", "message": "SSH tunnel started"}
        return {"status": "failed", "error": result.stderr.strip()}
    except Exception as e:
        return {"status": "failed", "error": str(e)}


@router.post("/tunnel/stop")
async def tunnel_stop() -> Dict[str, Any]:
    """Stop SSH tunnel."""
    settings = _load_settings()
    tunnel = settings.get("tunnel", {})
    port = tunnel.get("local_port", 11434)
    try:
        result = subprocess.run(
            ["lsof", "-ti", f":{port}"], capture_output=True, text=True, timeout=5
        )
        if result.stdout.strip():
            for pid_str in result.stdout.strip().split("\n"):
                try:
                    os.kill(int(pid_str), 9)
                except Exception:
                    pass
            return {"status": "stopped", "message": f"Killed processes on port {port}"}
        return {"status": "already_stopped", "message": "No process found on that port"}
    except Exception as e:
        return {"status": "failed", "error": str(e)}


@router.post("/probe/ollama")
async def probe_ollama() -> Dict[str, Any]:
    """Probe Ollama service and return available models."""
    settings = _load_settings()
    ollama_cfg = settings.get("ollama", {})
    url = ollama_cfg.get("url", "http://127.0.0.1:11434")

    try:
        import http.client
        conn = http.client.HTTPConnection("127.0.0.1", 11434, timeout=5)
        conn.request("GET", "/api/tags")
        resp = conn.get_response()
        data = json.loads(resp.read().decode())
        models = [m.get("name", "") for m in data.get("models", [])]
        return {"status": "ok", "models": models, "count": len(models)}
    except Exception as e:
        return {"status": "error", "error": str(e), "models": []}


@router.post("/probe/claude")
async def probe_claude(prompt: str = "hi") -> Dict[str, Any]:
    """Test Claude Code connectivity via the proxy."""
    settings = _load_settings()
    claude_cfg = settings.get("claude_code", {})
    url = claude_cfg.get("base_url", "http://127.0.0.1:11435")

    result = _check_http(url, timeout=5.0)
    return {
        "status": "ok" if result[0] else "error",
        "latency_ms": round(result[1], 2),
        "error": result[2],
        "url": url,
    }
