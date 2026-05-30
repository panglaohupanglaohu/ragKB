# -*- coding: utf-8 -*-
"""
AgentsGroup2026 — Standalone Agent Management + Evolution + Chat Server

A self-contained FastAPI application extracted from AgentsGroup2026 that provides:
  - Agent team management (create/configure/manage agents)
  - System evolution engine (audit → dispatch → verify → close)
  - Bridge chat (LLM-powered conversational interface)
  - OpenClaw integration (connect external agents)

Usage:
    cd src/backend && python main.py --port 8080
"""

from __future__ import annotations

import argparse
import hashlib
import hmac
import json
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, Optional

import uvicorn
from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# ── Logging ──
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s  %(message)s")
logger = logging.getLogger("agentsgroup")

# ── App ──
app = FastAPI(
    title="AgentsGroup2026",
    description="Standalone Agent Management, Evolution & Chat Platform",
    version="1.0.0",
)

_DEFAULT_CORS_ORIGINS = (
    "http://localhost:5173,"
    "http://127.0.0.1:5173,"
    "http://localhost:8080,"
    "http://127.0.0.1:8080"
)
_allowed_origins = [
    origin.strip()
    for origin in os.getenv("AG_ALLOWED_ORIGINS", _DEFAULT_CORS_ORIGINS).split(",")
    if origin.strip()
]
_allow_credentials = os.getenv("AG_CORS_ALLOW_CREDENTIALS", "1").lower() not in {"0", "false", "no"}
if "*" in _allowed_origins and _allow_credentials:
    logger.warning("AG_ALLOWED_ORIGINS contains '*' with credentials; disabling credentials for CORS")
    _allow_credentials = False

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_credentials=_allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ══════════════════════════════════════════════════════════════════
# Request / Response Models
# ══════════════════════════════════════════════════════════════════

class BridgeChatRequest(BaseModel):
    message: str
    session_id: str = "default"
    lang: str = "zh"
    agent_id: str = "default_agent"
    source: str = "bridge_chat"


class HealthResponse(BaseModel):
    status: str = "ok"
    version: str = "1.0.0"
    services: Dict[str, bool] = {}
    details: Dict[str, Any] = {}


class LoginRequest(BaseModel):
    username: str
    password: str


class RegisterRequest(BaseModel):
    username: str
    password: str


# ══════════════════════════════════════════════════════════════════
# Global State
# ══════════════════════════════════════════════════════════════════

_team_manager = None
_chat_channel = None
_STRICT_STARTUP = os.getenv("AG_STRICT_STARTUP", "1").lower() not in {"0", "false", "no"}


def _handle_startup_failure(name: str, exc: Exception, *, critical: bool) -> None:
    """Log startup failures and fail fast for core modules in strict mode."""
    level = "critical" if critical else "optional"
    logger.warning("⚠️ %s startup failed (%s): %s", name, level, exc)
    if critical and _STRICT_STARTUP:
        raise RuntimeError(f"Core startup module failed: {name}") from exc


# ══════════════════════════════════════════════════════════════════
# Startup
# ══════════════════════════════════════════════════════════════════

@app.on_event("startup")
async def startup():
    """Initialize all subsystems."""
    global _team_manager, _chat_channel

    logger.info("🚀 AgentsGroup2026 starting...")

    # 1. Register channels (evolution + chat)
    try:
        from channels.marine_base import get_default_registry
        from channels.system_evolution import SystemEvolutionChannel
        from channels.bridge_chat import BridgeChatChannel

        registry = get_default_registry()

        # System Evolution
        evo = SystemEvolutionChannel()
        registry.register(evo)
        evo.initialize()
        logger.info("✅ SystemEvolutionChannel registered")

        # Bridge Chat
        channel_registry = {}
        for ch_name in registry.list_channels():
            ch = registry.get(ch_name)
            if ch:
                channel_registry[ch_name] = ch
        _chat_channel = BridgeChatChannel(channel_registry=channel_registry)
        registry.register(_chat_channel)
        _chat_channel.initialize()
        logger.info("✅ BridgeChatChannel registered")
    except Exception as e:
        _handle_startup_failure("channels", e, critical=True)

    # 2. Agent Team API (evolution endpoints)
    try:
        from agent_team_api import router as agent_team_router, set_teams
        from channels.marine_base import get_default_registry

        registry = get_default_registry()
        evo_engine = registry.get("system_evolution")
        set_teams(
            build_team=None,
            execution_team=None,
            scheduler=None,
            evolution_engine=evo_engine,
        )
        app.include_router(agent_team_router)
        logger.info("✅ Agent Team API mounted (/api/v1/agent-teams)")
    except Exception as e:
        _handle_startup_failure("agent_team_api", e, critical=True)

    # 3. Agent Config API (teams, agents, tools, skills, tasks, sessions)
    try:
        from agents.api import router as agent_config_router, init_agent_config
        from agents.team_manager import TeamManager
        from agents.teams.build_team import create_build_team

        _team_manager = TeamManager()
        build_team_obj = create_build_team()
        _team_manager._teams[build_team_obj.team_id] = build_team_obj

        # AI 编程团队
        try:
            from agents.teams.ai_coding_team import create_ai_coding_team
            ai_coding_obj = create_ai_coding_team()
            _team_manager._teams[ai_coding_obj.team_id] = ai_coding_obj
        except Exception as e:
            logger.warning(f"⚠️ AI Coding team not loaded: {e}")

        # Try energy team (optional)
        try:
            from agents.teams.energy_team import create_energy_team
            energy_team_obj = create_energy_team()
            _team_manager._teams[energy_team_obj.team_id] = energy_team_obj
        except Exception as e:
            logger.warning(f"⚠️ Energy team not loaded: {e}")

        # 公有云 xOPs 团队 (optional)
        try:
            from agents.teams.xops_team import create_xops_team
            xops_team_obj = create_xops_team()
            _team_manager._teams[xops_team_obj.team_id] = xops_team_obj
        except Exception as e:
            logger.warning(f"⚠️ xOPs team not loaded: {e}")

        init_agent_config(_team_manager)
        app.include_router(agent_config_router)
        logger.info(
            "✅ Agent Config API mounted (/api/v1/agent-config) "
            f"— teams: {len(_team_manager.list_teams())}, "
            f"agents: {sum(len(t.agents) for t in _team_manager.list_teams())}"
        )

        # 4. 智能体广场 API
        try:
            from agents.plaza_routes import router as plaza_router
            from agents.plaza_engine import get_plaza_engine
            from agents.chat_harness import ChatHarness

            plaza_engine = get_plaza_engine()
            # 注入 ChatHarness.chat 函数
            from agents.api import get_chat_harness
            harness = get_chat_harness()
            plaza_engine.set_chat_fn(harness.chat)

            # 注册广场监控 Channel
            try:
                from monitoring.plaza_monitor import PlazaMonitorChannel
                from channels.marine_base import get_default_registry

                monitor_ch = PlazaMonitorChannel()
                registry = get_default_registry()
                registry.register(monitor_ch)
                monitor_ch.initialize()

                # 注入到 plaza_routes
                from agents.plaza_routes import set_plaza_monitor
                set_plaza_monitor(monitor_ch)

                logger.info("✅ PlazaMonitorChannel registered & injected")
            except Exception as me:
                logger.warning(f"⚠️ PlazaMonitorChannel registration failed: {me}")

            app.include_router(plaza_router, prefix="/api/v1/agent-config")
            logger.info("✅ 智能体广场 API mounted (/api/v1/agent-config/plaza)")
        except Exception as e:
            _handle_startup_failure("plaza_api", e, critical=True)

        # 4b. TTS 语音合成代理 (GPT-SoVITS)
        try:
            from agents.tts_routes import router as tts_router
            app.include_router(tts_router, prefix="/api/v1")
            logger.info("✅ TTS API mounted (/api/v1/tts)")
        except Exception as e:
            logger.warning(f"⚠️ TTS API failed: {e}")

        # 4c. 萃取管线 API
        try:
            from agents.extraction_routes import router as extraction_router
            app.include_router(extraction_router)
            logger.info("✅ Extraction Pipeline API mounted (/api/v1/extraction)")
        except Exception as e:
            logger.warning(f"⚠️ Extraction Pipeline API failed: {e}")

        # 4d. SkillRouter 技能路由 API
        try:
            from agents.skill_library import get_skill_library
            from agents.skill_router import init_skill_router
            from agents.skill_router_routes import router as skill_router_api
            init_skill_router(skill_library=get_skill_library(), team_manager=_team_manager)
            app.include_router(skill_router_api)
            logger.info("✅ SkillRouter API mounted (/api/v1/skill-router)")
        except Exception as e:
            logger.warning(f"⚠️ SkillRouter API failed: {e}")

        # 4e. 技能萃取 WebSocket
        try:
            from agents.skill_extract_ws import skill_extract_ws_endpoint
            app.add_api_websocket_route("/ws/skill-extract/{team_id}", skill_extract_ws_endpoint)
            logger.info("✅ Skill Extract WebSocket mounted (/ws/skill-extract/{team_id})")
        except Exception as e:
            logger.warning(f"⚠️ Skill Extract WebSocket failed: {e}")

    except Exception as e:
        _handle_startup_failure("agent_config_api", e, critical=True)

    # 5. SECS 沙箱系统 API
    try:
        from sandbox.api import router as sandbox_router, set_orchestrator
        from sandbox.channel import SandboxChannel
        from channels.marine_base import get_default_registry

        sandbox_ch = SandboxChannel()
        sandbox_ch.initialize()
        registry = get_default_registry()
        registry.register(sandbox_ch)
        set_orchestrator(sandbox_ch.get_orchestrator())
        app.include_router(sandbox_router)
        logger.info("✅ SECS Sandbox API mounted (/api/v1/sandbox)")
    except Exception as e:
        _handle_startup_failure("secs_sandbox_api", e, critical=False)

    # 6. 启动验证路由
    try:
        from startup_check import get_startup_check_router
        app.include_router(get_startup_check_router())
        logger.info("✅ Startup Check API mounted (/api/v1/startup-check)")
    except Exception as e:
        logger.warning(f"⚠️ Startup Check API failed: {e}")

    logger.info("🎉 AgentsGroup2026 ready")

    # 6. 异步执行启动验证（不阻塞启动）
    try:
        import asyncio
        from startup_check import run_startup_check

        async def _delayed_check():
            await asyncio.sleep(2)  # 等待所有服务就绪
            await run_startup_check(base_url="http://localhost:8080")

        asyncio.create_task(_delayed_check())
        logger.info("🔍 Startup validation scheduled (delayed 2s)")
    except Exception as e:
        logger.warning(f"⚠️ Startup validation scheduling failed: {e}")


# ══════════════════════════════════════════════════════════════════
# Auth
# ══════════════════════════════════════════════════════════════════

import secrets
import time as _time
import os as _os

# User store: username -> password hash.
_USER_STORE = Path(__file__).resolve().parents[2] / "config" / "users.json"
_PBKDF2_ITERATIONS = 260_000


def _hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        _PBKDF2_ITERATIONS,
    ).hex()
    return f"pbkdf2_sha256${_PBKDF2_ITERATIONS}${salt}${digest}"


def _verify_password(password: str, stored_hash: str) -> bool:
    try:
        algorithm, iterations, salt, digest = stored_hash.split("$", 3)
        if algorithm != "pbkdf2_sha256":
            return False
        candidate = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt.encode("utf-8"),
            int(iterations),
        ).hex()
        return hmac.compare_digest(candidate, digest)
    except Exception:
        return False


def _load_users() -> Dict[str, str]:
    try:
        if _USER_STORE.exists():
            data = json.loads(_USER_STORE.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                return {str(k): str(v) for k, v in data.items()}
    except Exception as exc:
        logger.warning("⚠️ Failed to load user store: %s", exc)
    return {}


def _save_users(users: Dict[str, str]) -> None:
    _USER_STORE.parent.mkdir(parents=True, exist_ok=True)
    _USER_STORE.write_text(json.dumps(users, ensure_ascii=False, indent=2), encoding="utf-8")


_USERS = _load_users()
_admin_password = _os.environ.get("ADMIN_PASSWORD", "")
if _admin_password:
    _USERS["admin"] = _hash_password(_admin_password)
    _save_users(_USERS)
elif _os.environ.get("AG_ALLOW_DEFAULT_ADMIN", "").lower() in {"1", "true", "yes"}:
    logger.warning("⚠️ AG_ALLOW_DEFAULT_ADMIN enabled; using insecure development admin password")
    _USERS.setdefault("admin", _hash_password("admin123"))
    _save_users(_USERS)
elif "admin" not in _USERS:
    logger.warning("⚠️ ADMIN_PASSWORD is not set; default admin account is disabled")

# Token store: token -> {"username": str, "created_at": float}
_TOKENS: Dict[str, dict] = {}
_TOKEN_TTL = 86400 * 7  # 7 days


def _clean_expired_tokens():
    """Remove expired tokens."""
    now = _time.time()
    expired = [t for t, v in _TOKENS.items() if now - v.get("created_at", 0) > _TOKEN_TTL]
    for t in expired:
        del _TOKENS[t]


def _create_token(username: str) -> str:
    """Create a new token for a user."""
    _clean_expired_tokens()
    token = secrets.token_hex(32)
    _TOKENS[token] = {"username": username, "created_at": _time.time()}
    return token


def _validate_token(token: str) -> str | None:
    """Returns username if valid, None otherwise."""
    entry = _TOKENS.get(token)
    if not entry:
        return None
    if _time.time() - entry.get("created_at", 0) > _TOKEN_TTL:
        del _TOKENS[token]
        return None
    return entry["username"]


@app.post("/api/v1/auth/register")
async def register(req: RegisterRequest):
    """Register a new user."""
    username = req.username.strip()
    if not username or len(username) < 2:
        raise HTTPException(status_code=400, detail="用户名至少需要2个字符")
    if len(req.password) < 8:
        raise HTTPException(status_code=400, detail="密码至少需要8个字符")
    if username in _USERS:
        raise HTTPException(status_code=409, detail="该用户名已被注册")
    _USERS[username] = _hash_password(req.password)
    _save_users(_USERS)
    token = _create_token(username)
    logger.info(f"✅ New user registered: {username}")
    return {"token": token, "username": username}


@app.post("/api/v1/auth/login")
async def login(req: LoginRequest):
    """Simple token-based login."""
    if req.username not in _USERS or not _verify_password(req.password, _USERS[req.username]):
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    token = _create_token(req.username)
    return {"token": token, "username": req.username}


@app.get("/api/v1/auth/me")
async def auth_me(authorization: str = Header(default="")):
    """Check current auth status."""
    token = authorization.replace("Bearer ", "") if authorization else ""
    username = _validate_token(token)
    if username:
        return {"username": username, "authenticated": True}
    return {"username": "guest", "authenticated": False}


# ══════════════════════════════════════════════════════════════════
# Health & Info
# ══════════════════════════════════════════════════════════════════

@app.get("/api/v1/health")
async def health():
    """Health check endpoint."""
    from channels.marine_base import get_default_registry

    registry = get_default_registry()
    sandbox_runtime: Dict[str, Any]
    try:
        from sandbox.python_runner import describe_sandbox_runtime

        sandbox_runtime = describe_sandbox_runtime()
    except Exception as exc:
        sandbox_runtime = {
            "mode": "unknown",
            "ready": False,
            "error": str(exc),
        }
    return HealthResponse(
        status="ok",
        version="1.0.0",
        services={
            "evolution": registry.get("system_evolution") is not None,
            "bridge_chat": registry.get("bridge_chat") is not None,
            "agent_config": _team_manager is not None,
            "sandbox_runtime_ready": bool(sandbox_runtime.get("ready")),
        },
        details={
            "sandbox_runtime": sandbox_runtime,
        },
    )


@app.get("/api/v1/info")
async def info():
    """System info endpoint for external integrations."""
    return {
        "name": "AgentsGroup2026",
        "version": "1.0.0",
        "description": "Standalone Agent Management, Evolution & Chat Platform",
        "capabilities": ["agent_management", "system_evolution", "chat", "openclaw_integration"],
        "api_prefix": "/api/v1",
        "endpoints": {
            "agent_config": "/api/v1/agent-config",
            "agent_teams": "/api/v1/agent-teams",
            "evolution": "/api/v1/agent-teams/evolution",
            "chat": "/api/v1/bridge-chat",
            "health": "/api/v1/health",
        },
    }


# ══════════════════════════════════════════════════════════════════
# Bridge Chat endpoints
# ══════════════════════════════════════════════════════════════════

async def _agent_llm_chat(
    message: str,
    session_id: str = "default",
    agent_id: str = "default_agent",
) -> Optional[Dict[str, Any]]:
    """Try LLM chat with agent context. Returns None if LLM is unavailable."""
    try:
        from agents.chat_harness import get_chat_harness
        from agents.api import _team_manager as tm
    except ImportError:
        return None

    harness = get_chat_harness()
    agent_prompt = ""
    agent_name = agent_id

    if tm:
        for team in tm.list_teams():
            agent = team.get_agent(agent_id)
            if agent:
                agent_prompt = agent.system_prompt or ""
                agent_name = agent.name or agent_id
                break

    ctx_lines = []
    if agent_prompt:
        ctx_lines.append(agent_prompt)
    else:
        ctx_lines.append(f"你是 AgentsGroup2026 系统的智能体 {agent_name}。")
    ctx_lines.append("回答时简洁专业，可中英文混合。")
    ctx_lines.append("如果用户请求涉及系统改进，请提出具体可执行的建议。")
    system_prompt = "\n".join(ctx_lines)

    try:
        result = await harness.chat(
            message,
            agent_id=agent_id,
            session_id=f"chat_{session_id}",
            system_prompt=system_prompt,
        )
        if result.error:
            return None
        reply = result.response.strip()
        if not reply:
            return None

        urgency = "normal"
        urgent_kw = ["紧急", "严重", "critical", "urgent", "emergency", "error"]
        if any(kw in reply.lower() for kw in urgent_kw):
            urgency = "high"

        return {
            "reply": reply,
            "urgency": urgency,
            "source": "agent_llm",
            "agent_id": agent_id,
            "agent_name": agent_name,
            "model": result.model,
            "provider": result.provider,
            "latency_ms": round(result.latency_ms, 1),
            "session_id": session_id,
        }
    except Exception as exc:
        logger.debug("Agent LLM chat failed: %s", exc)
        return None


@app.post("/api/v1/bridge-chat/send")
async def bridge_chat_send(payload: BridgeChatRequest):
    """Handle chat message — LLM first, template fallback.

    When the user mentions task/build keywords, automatically creates
    a task for the build team via TaskEngine.
    """
    # Try LLM chat
    llm_result = await _agent_llm_chat(payload.message, payload.session_id, agent_id=payload.agent_id)

    # Auto-create task when message mentions build/task keywords
    task_id = None
    msg_text = (payload.message or "").strip()
    _build_keywords = [
        "build团队", "Build团队", "build team", "开发任务", "开发团队",
        "构建团队", "提交任务", "分配任务", "创建任务", "新建任务",
        "改进系统", "优化系统", "修复", "升级", "重构",
    ]
    _is_build_request = any(kw in msg_text for kw in _build_keywords)

    if _is_build_request and len(msg_text) >= 4:
        try:
            from agents.api import _te
            from agents.task_engine import AgentTask

            title = msg_text.split("\n")[0][:120]
            task_description = msg_text
            if llm_result and llm_result.get("reply"):
                task_description = (
                    f"{msg_text}\n\n---\n\n"
                    f"## Agent 分析建议 (参考)\n\n{llm_result['reply']}\n"
                )

            engine = _te()
            if not engine._running:
                await engine.start()

            task = AgentTask(
                agent_id="build_pm",
                team_id="build_system",
                title=title,
                description=task_description,
                priority=2,
                metadata={
                    "source": "bridge_chat",
                    "session_id": payload.session_id,
                    "agent_id": payload.agent_id,
                },
            )
            await engine.submit_task(task)
            task_id = task.task_id
            logger.info(f"[Chat] Created task {task_id}: {title[:40]}")
        except Exception as e:
            logger.warning(f"[Chat] Task creation failed: {e}")
            if llm_result:
                llm_result["pipeline_error"] = f"任务创建失败: {str(e)[:200]}"

    if llm_result:
        if task_id:
            llm_result["task_id"] = task_id
        return llm_result

    # Fallback to template-based bridge_chat channel
    try:
        from channels.marine_base import get_default_registry

        registry = get_default_registry()
        chat_ch = registry.get("bridge_chat")
        if not chat_ch:
            return {
                "reply": "Chat channel 未注册，请检查后端配置。",
                "urgency": "normal",
                "source": "error",
            }

        result = await chat_ch.process_event({
            "type": "chat_message",
            "message": payload.message,
            "session_id": payload.session_id,
            "lang": payload.lang,
        })
        result["source"] = "bridge_chat_template"
        if task_id:
            result["task_id"] = task_id
    except Exception as e:
        logger.warning(f"[Chat] Template fallback failed: {e}")
        return {
            "reply": f"系统暂时无法处理请求: {str(e)[:100]}",
            "urgency": "normal",
            "source": "error",
        }
    return result


@app.get("/api/v1/bridge-chat/history")
async def bridge_chat_history(session_id: str = "default", limit: int = 20):
    """Get chat history."""
    from channels.marine_base import get_default_registry

    registry = get_default_registry()
    chat_ch = registry.get("bridge_chat")
    if not chat_ch:
        raise HTTPException(status_code=404, detail="Chat channel not found")
    return {"session_id": session_id, "messages": chat_ch.get_session_history(session_id, limit)}


@app.delete("/api/v1/bridge-chat/session/{session_id}")
async def bridge_chat_clear_session(session_id: str):
    """Clear chat session."""
    from channels.marine_base import get_default_registry

    registry = get_default_registry()
    chat_ch = registry.get("bridge_chat")
    if not chat_ch:
        raise HTTPException(status_code=404, detail="Chat channel not found")
    chat_ch.clear_session(session_id)
    return {"status": "ok", "session_id": session_id}


@app.get("/api/v1/bridge-chat/status")
async def bridge_chat_status():
    """Get chat channel status."""
    from channels.marine_base import get_default_registry

    registry = get_default_registry()
    chat_ch = registry.get("bridge_chat")
    if not chat_ch:
        raise HTTPException(status_code=404, detail="Chat channel not found")
    return chat_ch.get_status()


# ══════════════════════════════════════════════════════════════════
# OpenClaw Integration API
# ══════════════════════════════════════════════════════════════════

class OpenClawConnectRequest(BaseModel):
    """Request to connect an external system via OpenClaw protocol."""
    system_name: str
    system_url: str
    api_token: str = ""
    description: str = ""
    capabilities: list = []


@app.post("/api/v1/openclaw/connect")
async def openclaw_connect(req: OpenClawConnectRequest):
    """Register an external system for OpenClaw integration.

    This enables two-way communication:
    - External system can call AgentsGroup2026 APIs
    - AgentsGroup2026 can push evolution tasks to external system
    """
    return {
        "status": "connected",
        "system_name": req.system_name,
        "integration_id": f"oc_{hash(req.system_url) % 100000:05d}",
        "available_apis": {
            "chat": "/api/v1/bridge-chat/send",
            "evolution": "/api/v1/agent-teams/evolution/*",
            "agent_config": "/api/v1/agent-config/*",
            "health": "/api/v1/health",
        },
        "message": f"System '{req.system_name}' connected. Use the available APIs to integrate.",
    }


@app.get("/api/v1/openclaw/status")
async def openclaw_status():
    """Check OpenClaw integration status."""
    return {
        "protocol": "openclaw/v1",
        "status": "ready",
        "capabilities": [
            "agent_management",
            "system_evolution",
            "chat_improvement",
            "task_dispatch",
            "compliance_rating",
        ],
    }


# ══════════════════════════════════════════════════════════════════
# Static Files (Frontend)
# ══════════════════════════════════════════════════════════════════

# Mount frontend static files
_frontend_dir = Path(__file__).parent.parent / "frontend"
if _frontend_dir.exists():
    app.mount("/js", StaticFiles(directory=str(_frontend_dir / "js")), name="js")
    app.mount("/css", StaticFiles(directory=str(_frontend_dir / "css")), name="css")

    from fastapi.responses import FileResponse

    @app.get("/")
    async def index():
        return FileResponse(str(_frontend_dir / "agent-team-config.html"))

    @app.get("/agent-team-config.html")
    async def agent_config_page():
        return FileResponse(str(_frontend_dir / "agent-team-config.html"))

    @app.get("/{page_name}.html")
    async def frontend_page(page_name: str):
        page = _frontend_dir / f"{page_name}.html"
        if page.exists():
            return FileResponse(str(page))
        raise HTTPException(404, f"Page '{page_name}.html' not found")

    @app.get("/evolution.html")
    async def evolution_page():
        p = _frontend_dir / "datacenter-ratchet-evolution.html"
        if p.exists():
            return FileResponse(str(p))
        raise HTTPException(404, "Evolution page not found")


# ══════════════════════════════════════════════════════════════════
# Entry Point
# ══════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AgentsGroup2026 Server")
    parser.add_argument("--port", type=int, default=8080, help="Port to listen on")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--reload", action="store_true", help="Enable hot reload")
    args = parser.parse_args()

    logger.info(f"Starting AgentsGroup2026 on {args.host}:{args.port}")
    uvicorn.run(
        "main:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        log_level="info",
    )
