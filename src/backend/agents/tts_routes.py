# -*- coding: utf-8 -*-
"""TTS route — Edge-TTS (Microsoft Neural) as primary engine.

Edge-TTS provides free, high-quality neural voices with natural emotion.
GPT-SoVITS is kept as optional fallback for custom voice cloning.
"""

from __future__ import annotations

import json
import logging
import os
import re
import signal
import subprocess
from pathlib import Path
from typing import Optional

import httpx
from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(tags=["tts"])

# ── Config ────────────────────────────────────────────────────────────────────
_config_path = Path(__file__).resolve().parents[3] / "config" / "settings.json"


def _load_tts_config() -> dict:
    """Re-read settings.json for live config."""
    try:
        with open(_config_path, "r", encoding="utf-8") as f:
            return json.load(f).get("tts", {})
    except Exception:
        return {}


# ── Edge-TTS voice pool (male-only fallback voices) ─────────────────────────
VOICE_POOL = [
    {"voice": "zh-CN-YunxiNeural", "style": "lively", "desc": "活泼阳光男声"},
    {"voice": "zh-CN-YunjianNeural", "style": "passionate", "desc": "热情成熟男声"},
    {"voice": "zh-CN-YunyangNeural", "style": "professional", "desc": "专业新闻男声"},
]

VOICE_PROFILE_RULES = [
    (("pm", "项目经理"), {"voice": "zh-CN-YunyangNeural", "rate": "+3%", "pitch": "-2Hz"}),
    (("architect", "架构", "architect"), {"voice": "zh-CN-YunjianNeural", "rate": "+2%", "pitch": "-4Hz"}),
    (("researcher", "研究员", "research"), {"voice": "zh-CN-YunxiNeural", "rate": "+4%", "pitch": "+0Hz"}),
    (("developer", "开发", "全栈"), {"voice": "zh-CN-YunjianNeural", "rate": "+8%", "pitch": "+1Hz"}),
    (("tester", "测试"), {"voice": "zh-CN-YunyangNeural", "rate": "+4%", "pitch": "-1Hz"}),
    (("deployer", "运维", "部署"), {"voice": "zh-CN-YunyangNeural", "rate": "+6%", "pitch": "-3Hz"}),
    (("doc", "writer", "文档"), {"voice": "zh-CN-YunxiNeural", "rate": "+1%", "pitch": "+1Hz"}),
    (("policy", "watchdog", "forecast", "thermal", "pue", "darwin"), {"voice": "zh-CN-YunjianNeural", "rate": "+5%", "pitch": "-2Hz"}),
]

DEFAULT_VOICE = "zh-CN-YunxiNeural"
DEFAULT_RATE = "+8%"
DEFAULT_PITCH = "+0Hz"

# Track GPT-SoVITS subprocess (optional)
_tts_process: Optional[subprocess.Popen] = None


# ── Request models ─────────────────────────────────────────────────────────────

class TTSRequest(BaseModel):
    text: str
    text_lang: str = "zh"
    speed_factor: float = 1.0
    voice: str = ""
    agent_name: str = ""
    rate: str = ""
    pitch: str = ""


def _voice_for_agent(agent_name: str) -> str:
    """Deterministic voice assignment based on agent name hash."""
    if not agent_name:
        return DEFAULT_VOICE
    h = sum(ord(c) for c in agent_name)
    return VOICE_POOL[h % len(VOICE_POOL)]["voice"]


def _profile_for_agent(agent_name: str) -> dict:
    lowered = (agent_name or "").lower()
    for keywords, profile in VOICE_PROFILE_RULES:
        if any(keyword in lowered for keyword in keywords):
            return profile
    return {
        "voice": _voice_for_agent(agent_name),
        "rate": DEFAULT_RATE,
        "pitch": DEFAULT_PITCH,
    }


def _speechify_text(text: str) -> str:
    """Normalize LLM output into something that sounds spoken instead of written."""
    spoken = text.strip()
    spoken = re.sub(r"`([^`]+)`", r"\1", spoken)
    spoken = re.sub(r"\*\*([^*]+)\*\*", r"\1", spoken)
    spoken = re.sub(r"\*([^*]+)\*", r"\1", spoken)
    spoken = re.sub(r"^[\-•\d.\s]+", "", spoken, flags=re.MULTILINE)
    spoken = spoken.replace("SLA", "服务等级目标")
    spoken = spoken.replace("CI/CD", "持续集成和持续部署")
    spoken = spoken.replace("traceId", "追踪标识")
    spoken = spoken.replace("WebSocket", "Web Socket")
    spoken = re.sub(r"\s*[:：]\s*", "，", spoken)
    spoken = re.sub(r"\s*[;；]\s*", "。", spoken)
    spoken = re.sub(r"\n+", "。", spoken)
    spoken = re.sub(r"[ ]{2,}", " ", spoken)
    spoken = re.sub(r"[。]{2,}", "。", spoken)
    return spoken.strip("。 ") + "。"


def _rate_for_text(text: str, base_speed: float = 1.0) -> str:
    """Compute natural speaking rate for conversational discussion."""
    length = len(text.replace(" ", ""))
    if length < 20:
        pct = 0
    elif length < 60:
        pct = 5
    elif length < 150:
        pct = 10
    else:
        pct = 13
    pct += int((base_speed - 1.0) * 25)
    pct = max(-15, min(25, pct))
    return f"+{pct}%" if pct >= 0 else f"{pct}%"


# ── Edge-TTS synthesis ─────────────────────────────────────────────────────────

async def _edge_tts_synthesize(text: str, voice: str, rate: str, pitch: str) -> bytes:
    """Call edge-tts library to synthesize text to MP3 bytes."""
    import edge_tts

    communicate = edge_tts.Communicate(text=text, voice=voice, rate=rate, pitch=pitch)
    audio_chunks = []
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio_chunks.append(chunk["data"])

    if not audio_chunks:
        raise RuntimeError("Edge-TTS returned no audio data")
    return b"".join(audio_chunks)


# ── GPT-SoVITS fallback ───────────────────────────────────────────────────────

async def _gptsovits_synthesize(text: str, cfg: dict, speed: float) -> Optional[bytes]:
    """Fallback to local GPT-SoVITS if available."""
    api_url = cfg.get("api_url", "http://127.0.0.1:9880")
    payload = {
        "text": text,
        "text_lang": cfg.get("text_lang", "zh"),
        "ref_audio_path": cfg.get("ref_audio_path", ""),
        "prompt_text": cfg.get("prompt_text", ""),
        "prompt_lang": cfg.get("prompt_lang", "zh"),
        "speed_factor": speed,
        "media_type": "wav",
        "streaming_mode": False,
        "text_split_method": "cut5",
        "batch_size": 1,
        "temperature": 1.0,
        "top_k": 15,
        "top_p": 1.0,
        "parallel_infer": True,
        "repetition_penalty": 1.35,
    }
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(60.0, connect=5.0)) as client:
            resp = await client.post(f"{api_url}/tts", json=payload)
            if resp.status_code == 200:
                return resp.content
    except Exception as e:
        logger.debug(f"GPT-SoVITS fallback failed: {e}")
    return None


# ── Main TTS endpoint ─────────────────────────────────────────────────────────

@router.post("/tts")
async def tts_synthesize(req: TTSRequest):
    """Synthesize speech using Edge-TTS (primary) or GPT-SoVITS (fallback)."""
    cfg = _load_tts_config()
    engine = cfg.get("engine", "edge-tts")

    text = req.text.strip()
    if not text:
        raise HTTPException(400, "text is required")

    spoken_text = _speechify_text(text)
    profile = _profile_for_agent(req.agent_name)

    voice = req.voice or profile["voice"]
    rate = req.rate or profile["rate"] or _rate_for_text(spoken_text, req.speed_factor)
    pitch = req.pitch or profile["pitch"] or DEFAULT_PITCH

    # Try Edge-TTS first
    if engine != "gpt-sovits-only":
        try:
            audio_data = await _edge_tts_synthesize(spoken_text, voice, rate, pitch)
            return Response(
                content=audio_data,
                media_type="audio/mpeg",
                headers={"Cache-Control": "no-cache", "X-TTS-Engine": "edge-tts", "X-TTS-Voice": voice},
            )
        except Exception as e:
            logger.warning(f"Edge-TTS failed: {e}, trying GPT-SoVITS fallback")

    # Fallback to GPT-SoVITS
    if cfg.get("ref_audio_path"):
        audio_data = await _gptsovits_synthesize(spoken_text, cfg, req.speed_factor)
        if audio_data:
            return Response(
                content=audio_data,
                media_type="audio/wav",
                headers={"Cache-Control": "no-cache", "X-TTS-Engine": "gpt-sovits"},
            )

    raise HTTPException(503, "All TTS engines unavailable")


# ── Config endpoints ──────────────────────────────────────────────────────────

@router.get("/tts/config")
async def tts_get_config():
    """Return current TTS config."""
    cfg = _load_tts_config()
    return {
        "engine": cfg.get("engine", "edge-tts"),
        "api_url": cfg.get("api_url", "http://127.0.0.1:9880"),
        "ref_audio_path": cfg.get("ref_audio_path", ""),
        "text_lang": cfg.get("text_lang", "zh"),
        "speed_factor": cfg.get("speed_factor", 1.0),
        "edge_voice": cfg.get("edge_voice", DEFAULT_VOICE),
        "edge_rate": cfg.get("edge_rate", DEFAULT_RATE),
        "voice_pool": VOICE_POOL,
    }


class TTSConfigUpdate(BaseModel):
    engine: str = "edge-tts"
    api_url: str = "http://127.0.0.1:9880"
    ref_audio_path: str = ""
    prompt_text: str = ""
    prompt_lang: str = "zh"
    text_lang: str = "zh"
    speed_factor: float = 1.0
    edge_voice: str = DEFAULT_VOICE
    edge_rate: str = DEFAULT_RATE


@router.put("/tts/config")
async def tts_update_config(body: TTSConfigUpdate):
    """Update TTS config in settings.json."""
    try:
        with open(_config_path, "r", encoding="utf-8") as f:
            settings = json.load(f)
    except Exception:
        settings = {}

    settings["tts"] = {
        **settings.get("tts", {}),
        "engine": body.engine,
        "api_url": body.api_url,
        "ref_audio_path": body.ref_audio_path,
        "prompt_text": body.prompt_text,
        "prompt_lang": body.prompt_lang,
        "text_lang": body.text_lang,
        "speed_factor": body.speed_factor,
        "edge_voice": body.edge_voice,
        "edge_rate": body.edge_rate,
    }
    with open(_config_path, "w", encoding="utf-8") as f:
        json.dump(settings, f, ensure_ascii=False, indent=2)
    return {"status": "saved"}


@router.get("/tts/status")
async def tts_status():
    """Check TTS service availability."""
    global _tts_process
    cfg = _load_tts_config()

    edge_ok = False
    try:
        import edge_tts  # noqa: F401
        edge_ok = True
    except ImportError:
        pass

    gptsovits_ok = False
    api_url = cfg.get("api_url", "http://127.0.0.1:9880")
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            resp = await client.get(f"{api_url}/")
            gptsovits_ok = resp.status_code < 500
    except Exception:
        pass

    pid = None
    if _tts_process and _tts_process.poll() is None:
        pid = _tts_process.pid

    return {
        "engine": cfg.get("engine", "edge-tts"),
        "edge_tts": {"available": edge_ok, "voice": cfg.get("edge_voice", DEFAULT_VOICE)},
        "gpt_sovits": {"online": gptsovits_ok, "api_url": api_url, "pid": pid},
    }


@router.get("/tts/voices")
async def tts_list_voices():
    """List available Edge-TTS voices."""
    return {"voices": VOICE_POOL, "default": DEFAULT_VOICE}


# ── GPT-SoVITS process management ─────────────────────────────────────────────

@router.post("/tts/start")
async def tts_start_service():
    """Start GPT-SoVITS subprocess (optional)."""
    global _tts_process
    if _tts_process and _tts_process.poll() is None:
        return {"status": "already_running", "pid": _tts_process.pid}

    gpt_sovits_dir = Path.home() / "GPT-SoVITS"
    venv_python = gpt_sovits_dir / "venv" / "bin" / "python"
    if not venv_python.exists():
        raise HTTPException(404, "GPT-SoVITS venv not found")

    try:
        _tts_process = subprocess.Popen(
            [str(venv_python), "api_v2.py", "-a", "127.0.0.1", "-p", "9880",
             "-c", "GPT_SoVITS/configs/tts_infer.yaml"],
            cwd=str(gpt_sovits_dir),
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            preexec_fn=os.setsid,
        )
        return {"status": "started", "pid": _tts_process.pid}
    except Exception as e:
        raise HTTPException(500, str(e))


@router.post("/tts/stop")
async def tts_stop_service():
    """Stop GPT-SoVITS subprocess."""
    global _tts_process
    if _tts_process and _tts_process.poll() is None:
        os.killpg(os.getpgid(_tts_process.pid), signal.SIGTERM)
        _tts_process = None
        return {"status": "stopped"}
    return {"status": "not_running"}
