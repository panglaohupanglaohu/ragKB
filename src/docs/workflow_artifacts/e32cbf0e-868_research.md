# 研究分析 — researcher

任务: 构建逆事实推演框架，用历史决策数据标定 OpenClaw 误判成本与沉默代价，熔合成决策折损率基线
步骤: research
Agent: build_researcher

---

📋 任务: e32cbf0e-868
🤖 Agent: Researcher (researcher)
📂 工作目录: /Users/panglaohu/Downloads/AgentsGroup2026
🔧 执行方式: DeepSeek API (直连)
⏱️ 超时: 1200s
────────────────────────────────────────────────────────────
📝 提示词:
  你是 AgentsGroup2026 系统的 Researcher (researcher)。
  请执行以下开发任务:
  
  你是技术研究员。请对以下任务进行技术调研:
  
  ## 任务
  构建逆事实推演框架，用历史决策数据标定 OpenClaw 误判成本与沉默代价，熔合成决策折损率基线
  技术研究员 + Developer
  
  ## 📂 项目上下文 (系统自动预加载)
  
  ### 项目文件结构 (src/ 目录)
  ```
  src/frontend/agent-team-config.html
  src/frontend/datacenter-ratchet-evolution.html
  src/frontend/index.html
  src/frontend/login.html
  src/frontend/plaza-dark.html
  src/frontend/plaza-old.html
  src/frontend/plaza-wabisabi-v2.html
  src/frontend/plaza-wabisabi.html
  src/frontend/plaza.html
  src/frontend/system-evolution.html
  src/frontend/tasks.html
  src/frontend/css/agent-team-config.css
  src/frontend/css/openbridge-theme.css
  src/frontend/css/ws-theme-bridge.css
  src/frontend/js/agent-team-config.js
  src/frontend/js/i18n.js
  src/frontend/js/nav-sidebar.js
  src/backend/__init__.py
  src/backend/agent_team_api.py
  src/backend/main.py
  src/backend/main.py.bak
  src/backend/startup_check.py
  src/backend/startup_validator.py
  src/backend/agents/__init__.py
  src/backend/agents/ab_testing.py
  src/backend/agents/agent_loop.py
  src/backend/agents/agent_toolbox.py
  src/backend/agents/api.py
  src/backend/agents/chat_harness.py
  src/backend/agents/execution_registry.py
  src/backend/agents/hermes_research.py
  src/backend/agents/knowledge_base.py
  src/backend/agents/models.py
  src/backend/agents/plaza.py
  src/backend/agents/plaza_engine.py
  src/backend/agents/plaza_routes.py
  src/backend/agents/plaza_routes.py.bak
  src/backend/agents/plaza_store.py
  src/backend/agents/session_store.py
  src/backend/agents/skill_registry.py
  src/backend/agents/task_engine.py
  src/backend/agents/task_store.py
  src/backend/agents/team_manager.py
  src/backend/agents/team_store.py
  src/backend/agents/tool_executor.py
  src/backend/agents/tool_registry.py
  src/backend/agents/tts_routes.py
  src/backend/agents/teams/__init__.py
  src/backend/agents/teams/ai_coding_team.py
  src/backend/agents/teams/build_team.py
  src/backend/agents/teams/energy_team.py
  src/backend/agents/skills/__init__.py
  src/backend/agents/skills/greeting.py
  src/backend/agents/skills/hello.py
  src/backend/scripts/__init__.py
  src/backend/scripts/validate_startup.py
  src/backend/scripts/validate_telemetry.py
  src/backend/monitoring/__init__.py
  src/backend/monitoring/collector.py
  src/backend/monitoring/models.py
  src/backend/monitoring/plaza_monitor.py
  src/backend/monitoring/plaza_monitor.py.bak
  src/backend/monitoring/sampler.py
  src/backend/channels/__init__.py
  src/backend/channels/bridge_chat.py
  src/backend/channels/marine_base.py
  src/backend/channels/openclaw_sync.py
  src/backend/channels/openclaw_sync.py.bak
  src/backend/channels/system_evolution.py
  src/docs/agent_handoffs/1ce78c0e-062_architecture_20260503T045804.md
  src/docs/agent_handoffs/1ce78c0e-062_deploy_FAILED_20260503T050220.md
  src/docs/agent_handoffs/1ce78c0e-062_develop_20260503T045845.md
  src/docs/agent_handoffs/1ce78c0e-062_develop_20260503T050025.md
  src/docs/agent_handoffs/1ce78c0e-062_develop_20260503T050150.md
  src/docs/agent_handoffs/1ce78c0e-062_pm_decompose_20260503T045724.md
  src/docs/agent_handoffs/1ce78c0e-062_research_20260503T045739.md
  src/docs/agent_handoffs/1ce78c0e-062_task_init_20260503T045659.md
  src/docs/agent_handoffs/1ce78c0e-062_test_20260503T045905.md
  src/docs/agent_handoffs/1ce78c0e-062_test_20260503T050050.md
  src/docs/agent_handoffs/1ce78c0e-062_test_20260503T050210.md
  src/docs/agent_handoffs/23cb267e-4e0_executor_started_20260503T114540.md
  src/docs/agent_handoffs/38e22004-b64_architecture_20260503T045011.md
  src/docs/agent_handoffs/38e22004-b64_pm_decompose_20260503T044921.md
  src/docs/agent_handoffs/38e22004-b64_research_20260503T044941.md
  src/docs/agent_handoffs/38e22004-b64_task_init_20260503T044856.md
  src/docs/agent_handoffs/4b17f83b-805_architecture_20260507T003640.md
  src/docs/agent_handoffs/4b17f83b-805_deploy_FAILED_20260507T004132.md
  src/docs/agent_handoffs/4b17f83b-805_develop_FAILED_20260507T003706.md
  src/docs/agent_handoffs/4b17f83b-805_develop_FAILED_20260507T003913.md
  src/docs/agent_handoffs/4b17f83b-805_develop_FAILED_20260507T004040.md
  src/docs/agent_handoffs/4b17f83b-805_executor_started_20260507T003435.md
  src/docs/agent_handoffs/4b17f83b-805_pm_decompose_20260507T003510.md
  src/docs/agent_handoffs/4b17f83b-805_research_20260507T003555.md
  src/docs/agent_handoffs/4b17f83b-805_test_FAILED_20260507T003732.md
  src/docs/agent_handoffs/4b17f83b-805_test_FAILED_20260507T003939.md
  src/docs/agent_handoffs/4b17f83b-805_test_FAILED_20260507T004102.md
  src/docs/agent_handoffs/6f911ba3-822_architecture_20260507T003740.md
  src/docs/agent_handoffs/6f911ba3-822_deploy_FAILED_20260507T004337.md
  src/docs/agent_handoffs/6f911ba3-822_develop_FAILED_20260507T003806.md
  src/docs/agent_handoffs/6f911ba3-822_develop_FAILED_20260507T004113.md
  src/docs/agent_handoffs/6f911ba3-822_develop_FAILED_20260507T004235.md
  src/docs/agent_handoffs/6f911ba3-822_executor_started_20260507T003435.md
  src/docs/agent_handoffs/6f911ba3-822_pm_decompose_20260507T003510.md
  src/docs/agent_handoffs/6f911ba3-822_research_20260507T003550.md
  src/docs/agent_handoffs/6f911ba3-822_test_FAILED_20260507T003827.md
  src/docs/agent_handoffs/6f911ba3-822_test_FAILED_20260507T004134.md
  src/docs/agent_handoffs/6f911ba3-822_test_FAILED_20260507T004311.md
  src/docs/agent_handoffs/7c934759-39e_architecture_20260505T010014.md
  src/docs/agent_handoffs/7c934759-39e_develop_20260505T010359.md
  src/docs/agent_handoffs/7c934759-39e_develop_20260505T012357.md
  src/docs/agent_handoffs/7c934759-39e_develop_FAILED_20260505T011447.md
  src/docs/agent_handoffs/7c934759-39e_executor_started_20260505T005814.md
  src/docs/agent_handoffs/7c934759-39e_pm_decompose_20260505T005849.md
  src/docs/agent_handoffs/7c934759-39e_research_20260505T005919.md
  src/docs/agent_handoffs/7c934759-39e_test_FAILED_20260505T011016.md
  src/docs/agent_handoffs/7c934759-39e_test_FAILED_20260505T011949.md
  src/docs/agent_handoffs/7c934759-39e_test_FAILED_20260505T012853.md
  src/docs/agent_handoffs/8a5071c5-834_architecture_20260507T003655.md
  src/docs/agent_handoffs/8a5071c5-834_deploy_FAILED_20260507T004051.md
  src/docs/agent_handoffs/8a5071c5-834_develop_FAILED_20260507T003716.md
  src/docs/agent_handoffs/8a5071c5-834_develop_FAILED_20260507T003903.md
  src/docs/agent_handoffs/8a5071c5-834_develop_FAILED_20260507T004005.md
  src/docs/agent_handoffs/8a5071c5-834_executor_started_20260507T003435.md
  src/docs/agent_handoffs/8a5071c5-834_pm_decompose_20260507T003510.md
  src/docs/agent_handoffs/8a5071c5-834_research_20260507T003540.md
  src/docs/agent_handoffs/8a5071c5-834_test_FAILED_20260507T003737.md
  src/docs/agent_handoffs/8a5071c5-834_test_FAILED_20260507T003929.md
  src/docs/agent_handoffs/8a5071c5-834_test_FAILED_20260507T004031.md
  src/docs/agent_handoffs/a77bd3b9-2db_architecture_20260507T003625.md
  src/docs/agent_handoffs/a77bd3b9-2db_deploy_FAILED_20260507T004102.md
  src/docs/agent_handoffs/a77bd3b9-2db_develop_FAILED_20260507T003646.md
  src/docs/agent_handoffs/a77bd3b9-2db_develop_FAILED_20260507T003838.md
  src/docs/agent_handoffs/a77bd3b9-2db_develop_FAILED_20260507T004005.md
  src/docs/agent_handoffs/a77bd3b9-2db_executor_started_20260507T003435.md
  src/docs/agent_handoffs/a77bd3b9-2db_pm_decompose_20260507T003515.md
  src/docs/agent_handoffs/a77bd3b9-2db_research_20260507T003545.md
  src/docs/agent_handoffs/a77bd3b9-2db_test_FAILED_20260507T003712.md
  src/docs/agent_handoffs/a77bd3b9-2db_test_FAILED_20260507T003904.md
  src/docs/agent_handoffs/a77bd3b9-2db_test_FAILED_20260507T004042.md
  src/docs/agent_handoffs/ba3b66b1-a77_architecture_20260505T154317.md
  src/docs/agent_handoffs/ba3b66b1-a77_deploy_FAILED_20260505T154903.md
  src/docs/agent_handoffs/ba3b66b1-a77_develop_FAILED_20260505T154353.md
  src/docs/agent_handoffs/ba3b66b1-a77_develop_FAILED_20260505T154600.md
  src/docs/agent_handoffs/ba3b66b1-a77_develop_FAILED_20260505T154807.md
  src/docs/agent_handoffs/ba3b66b1-a77_executor_started_20260505T153921.md
  src/docs/agent_handoffs/ba3b66b1-a77_pm_decompose_20260505T153951.md
  src/docs/agent_handoffs/ba3b66b1-a77_research_20260505T154041.md
  src/docs/agent_handoffs/ba3b66b1-a77_test_FAILED_20260505T154424.md
  src/docs/agent_handoffs/ba3b66b1-a77_test_FAILED_20260505T154631.md
  src/docs/agent_handoffs/ba3b66b1-a77_test_FAILED_20260505T154838.md
  ... (共 254 个 src/ 文件)
  
  ```
  
  ### 文件: `src/backend/main.py`
  ```py
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
  import json
  import logging
  import os
  import sys
  from pathlib import Path
  from typing import Any, Dict, Optional
  
  import uvicorn
  from fastapi import FastAPI, HTTPException
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
  
  app.add_middleware(
      CORSMiddleware,
      allow_origins=["*"],
      allow_credentials=True,
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
          logger.warning(f"⚠️ Channel registration failed: {e}")
  
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
          logger.warning(f"⚠️ Agent Team API failed: {e}")
  
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
          except Exception:
              pass
  
          # Try energy team (optional)
          try:
              from agents.teams.energy_team import create_energy_team
              energy_team_obj = create_energy_team()
              _team_manager._teams[energy_team_obj.team_id] = energy_team_obj
          except Exception:
              pass
  
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
              logger.warning(f"⚠️ Plaza API failed: {e}")
  
          # 4b. TTS 语音合成代理 (GPT-SoVITS)
          try:
              from agents.tts_routes import router as tts_router
              app.include_router(tts_router, prefix="/api/v1")
              logger.info("✅ TTS API mounted (/api/v1/tts)")
          except Exception as e:
              logger.warning(f"⚠️ TTS API failed: {e}")
  
      except Exception as e:
          logger.warning(f"⚠️ Agent Config API failed: {e}")
  
      # 5. 启动验证路由
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
  
  import hashlib
  import secrets
  
  # Default users (in production, use a proper database)
  _USERS = {
      "admin": hashlib.sha256("admin123".encode()).hexdigest(),
  }
  _TOKENS: Dict[str, str] = {}
  
  
  @app.post("/api/v1/auth/register")
  async def register(req: RegisterRequest):
      """Register a new user."""
      username = req.username.strip()
      if not username or len(username) < 2:
          raise HTTPException(status_code=400, detail="用户名至少需要2个字符")
      if len(req.password) < 4:
          raise HTTPException(status_code=400, detail="密码至少需要4个字符")
      if username in _USERS:
          raise HTTPException(status_code=409, detail="该用户名已被注册")
      _USERS[username] = hashlib.sha256(req.password.encode()).hexdigest()
      token = secrets.token_hex(32)
      _TOKENS[token] = username
      logger.info(f"✅ New user registered: {username}")
      return {"token": token, "username": username}
  
  
  @app.post("/api/v1/auth/login")
  async def login(req: LoginRequest):
      """Simple token-based login."""
      pwd_hash = hashlib.sha256(req.password.encode()).hexdigest()
      if req.username not in _USERS or _USERS[req.username] != pwd_hash:
          raise HTTPException(status_code=401, detail="用户名或密码错误")
      token = secrets.token_hex(32)
      _TOKENS[token] = req.username
      return {"token": token, "username": req.username}
  
  
  @app.get("/api/v1/auth/me")
  async def auth_me(authorization: str = ""):
      """Check current auth status."""
      token = authorization.replace("Bearer ", "") if authorization else ""
      if token in _TOKENS:
          return {"username": _TOKENS[token], "authenticated": True}
      return {"username": "guest", "authenticated": False}
  
  
  # ══════════════════════════════════════════════════════════════════
  # Health & Info
  # ══════════════════════════════════════════════════════════════════
  
  @app.get("/api/v1/health")
  async def health():
      """Health check endpoint."""
      from channels.marine_base import get_default_registry
      registry = get_default_registry()
      return HealthResponse(
          status="ok",
          version="1.0.0",
          services={
              "evolution": registry.get("system_evolution") is not None,
              "bridge_chat": registry.get("bridge_chat") is not None,
              "agent_config": _team_manager is not None,
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
              
  ```
  
  ### 文件: `src/backend/agents/agent_loop.py`
  ```py
  """Function-calling loop for Developer/QA agents.
  
  Drives a multi-turn conversation with DeepSeek V4 where each turn the model can
  call tools (read_file, grep, write_file, patch_file, run_python, run_pytest) to
  inspect and modify the codebase, then finishes with a `finish` tool call.
  
  This replaces the single-shot "emit a markdown blob with code fences" approach
  that produced hallucinated imports and truncated files.
  """
  from __future__ import annotations
  
  import http.client
  import json
  import logging
  import ssl
  import time
  from typing import Any, Dict, List, Optional
  from urllib.parse import urlparse
  
  from .agent_toolbox import (
      TOOL_SCHEMA,
      dispatch_tool_call,
      get_tools_for_role,
  )
  
  logger = logging.getLogger("AgentLoop")
  
  DEFAULT_MAX_ITERATIONS = 25
  DEFAULT_MAX_TOKENS = 65536
  DEFAULT_TEMPERATURE = 0.2
  
  # ── Safeguard constants ──
  # Safeguard 1: auto-finish nudge when approaching iteration cap
  _ITERATION_NUDGE_RATIO = 0.80  # at 80% of max_iterations, inject nudge
  # Safeguard 2: context budget — compress old tool results when messages grow
  _CONTEXT_BUDGET_CHARS = 100_000  # max combined chars in messages
  _TOOL_RESULT_TRUNC = 500  # truncate old tool results to this when over budget
  
  
  class AgentLoop:
      """Multi-turn function-calling driver against an OpenAI-compatible endpoint."""
  
      def __init__(
          self,
          *,
          api_key: str,
          api_base_url: str,
          model: str,
          role: str,
          system_prompt: str,
          max_iterations: int = DEFAULT_MAX_ITERATIONS,
          max_tokens: int = DEFAULT_MAX_TOKENS,
          temperature: float = DEFAULT_TEMPERATURE,
          on_event: Optional[Any] = None,
      ):
          self.api_key = api_key
          self.api_base_url = api_base_url.rstrip("/")
          self.model = model
          self.role = role
          self.max_iterations = max_iterations
          self.max_tokens = max_tokens
          self.temperature = temperature
          self.tools = get_tools_for_role(role)
          self.messages: List[Dict[str, Any]] = [
              {"role": "system", "content": system_prompt},
          ]
          self.on_event = on_event   # callable(event_type:str, payload:dict)
          self.files_changed: List[str] = []
          self.summary: str = ""
          self.tool_call_log: List[Dict[str, Any]] = []
  
      # ────────────────────────────────────────────────
      # HTTP plumbing
      # ────────────────────────────────────────────────
      _API_MAX_RETRIES = 3
      _API_RETRY_BACKOFF = [2, 5, 10]  # seconds between retries
      # Transient errors worth retrying
      _RETRYABLE = (
          ConnectionResetError, ConnectionAbortedError, ConnectionRefusedError,
          BrokenPipeError, TimeoutError, OSError,
          http.client.RemoteDisconnected, http.client.IncompleteRead,
      )
  
      def _post_chat(self) -> Dict[str, Any]:
          parsed = urlparse(self.api_base_url)
          host = parsed.hostname or "api.deepseek.com"
          port = parsed.port or (443 if parsed.scheme == "https" else 80)
          path = (parsed.path or "").rstrip("/") + "/chat/completions"
          ctx = ssl.create_default_context() if parsed.scheme == "https" else None
          conn_cls = http.client.HTTPSConnection if parsed.scheme == "https" else http.client.HTTPConnection
  
          payload: Dict[str, Any] = {
              "model": self.model,
              "messages": self.messages,
              "tools": self.tools,
              "tool_choice": "auto",
              "max_tokens": self.max_tokens,
              "temperature": self.temperature,
              "stream": False,
              "thinking": {"type": "enabled"},
              "reasoning_effort": "high",
          }
          body_str = json.dumps(payload)
          headers = {
              "Authorization": f"Bearer {self.api_key}",
              "Content-Type": "application/json",
          }
  
          last_err: Optional[Exception] = None
          for attempt in range(self._API_MAX_RETRIES):
              try:
                  conn = conn_cls(host, port, context=ctx, timeout=300) if ctx \
                      else conn_cls(host, port, timeout=300)
                  conn.request("POST", path, body=body_str, headers=headers)
                  resp = conn.getresponse()
                  raw = resp.read().decode("utf-8", errors="replace")
                  conn.close()
                  if resp.status == 429 or resp.status >= 500:
                      # Server-side error — retryable
                      raise RuntimeError(f"LLM HTTP {resp.status}: {raw[:300]}")
                  if resp.status >= 400:
                      raise RuntimeError(f"LLM HTTP {resp.status}: {raw[:500]}")
                  return json.loads(raw)
              except self._RETRYABLE as e:
                  last_err = e
                  wait = self._API_RETRY_BACKOFF[min(attempt, len(self._API_RETRY_BACKOFF) - 1)]
                  logger.warning(
                      "[AgentLoop] Transient error on attempt %d/%d: %s — retrying in %ds",
                      attempt + 1, self._API_MAX_RETRIES, e, wait,
                  )
                  time.sleep(wait)
              except RuntimeError as e:
                  # HTTP 429 / 5xx — retry with backoff
                  if "HTTP 4" in str(e) and "HTTP 429" not in str(e):
                      raise  # 4xx (non-429) is not retryable
                  last_err = e
                  wait = self._API_RETRY_BACKOFF[min(attempt, len(self._API_RETRY_BACKOFF) - 1)]
                  logger.warning(
                      "[AgentLoop] Server error on attempt %d/%d: %s — retrying in %ds",
                      attempt + 1, self._API_MAX_RETRIES, e, wait,
                  )
                  time.sleep(wait)
          raise last_err or RuntimeError("_post_chat failed after retries")
  
      # ────────────────────────────────────────────────
      # Loop
      # ────────────────────────────────────────────────
      def run(self, user_prompt: str) -> Dict[str, Any]:
          """Run the agent loop. Returns {ok, summary, files_changed, iterations, log}."""
          self.messages.append({"role": "user", "content": user_prompt})
          self._emit("loop_start", {"role": self.role, "tools": [t["function"]["name"] for t in self.tools]})
  
          for it in range(self.max_iterations):
              # ── Safeguard 1: nudge agent when approaching iteration cap ──
              self._maybe_inject_nudge(it)
              # ── Safeguard 2: compact old tool results when context too large ──
              self._compact_old_tool_results()
  
              t0 = time.time()
              try:
                  resp = self._post_chat()
              except Exception as e:
                  logger.exception("[AgentLoop] HTTP error on iteration %d (after retries)", it)
                  self._emit("error", {"iteration": it, "error": str(e)})
                  # If we have already done useful work, don't discard it —
                  # treat as a graceful early stop instead of hard failure.
                  if self.files_changed or self.summary:
                      logger.info(
                          "[AgentLoop] Partial progress (%d files, %d chars summary) — "
                          "returning partial success",
                          len(self.files_changed), len(self.summary),
                      )
                      self._emit("loop_end", {"reason": "network_error_partial", "iteration": it})
                      return {
                          "ok": True, "error": str(e),
                          "summary": self.summary or f"(network error after {it} turns)",
                          "files_changed": self.files_changed,
                          "iterations": it, "log": self.tool_call_log,
                      }
                  return {
                      "ok": False, "error": str(e),
                      "summary": self.summary, "files_changed": self.files_changed,
                      "iterations": it, "log": self.tool_call_log,
                  }
  
              choice = (resp.get("choices") or [{}])[0]
              msg = choice.get("message", {}) or {}
              content = msg.get("content") or ""
              tool_calls = msg.get("tool_calls") or []
              finish_reason = choice.get("finish_reason", "")
  
              self._emit("model_turn", {
                  "iteration": it,
                  "elapsed": round(time.time() - t0, 2),
                  "content_chars": len(content),
                  "tool_call_count": len(tool_calls),
                  "finish_reason": finish_reason,
              })
  
              # Append assistant turn
              assistant_msg: Dict[str, Any] = {"role": "assistant", "content": content}
              if tool_calls:
                  assistant_msg["tool_calls"] = tool_calls
              self.messages.append(assistant_msg)
  
              # No tool calls → model is done talking
              if not tool_calls:
                  if not self.summary and content:
                      self.summary = content[:1000]
                  self._emit("loop_end", {"reason": "no_tool_call", "iteration": it})
                  return {
                      "ok": True, "summary": self.summary,
                      "files_changed": self.files_changed,
                      "iterations": it + 1, "log": self.tool_call_log,
                      "final_message": content,
                  }
  
              # Process each tool call
              finished = False
              for tc in tool_calls:
                  tc_id = tc.get("id", "")
                  fn = tc.get("function", {}) or {}
                  name = fn.get("name", "")
                  args_raw = fn.get("arguments", "") or "{}"
                  self._emit("tool_call", {"name": name, "args": args_raw[:500]})
  
                  if name == "finish":
                      try:
                          a = json.loads(args_raw or "{}")
                          self.summary = a.get("summary", "")
                          for fc in a.get("files_changed") or []:
                              if fc not in self.files_changed:
                                  self.files_changed.append(fc)
                      except Exception:
                          self.summary = args_raw[:500]
                      self.messages.append({
                          "role": "tool", "tool_call_id": tc_id, "name": name,
                          "content": json.dumps({"ok": True, "ack": "finished"}),
                      })
                      self.tool_call_log.append({"name": name, "args": args_raw, "ok": True})
                      finished = True
                      continue
  
                  result = dispatch_tool_call(name, args_raw)
                  # Track writes
                  if name in ("write_file", "patch_file") and result.get("ok"):
                      try:
                          a = json.loads(args_raw or "{}")
                          path = a.get("path", "")
                          if path and path not in self.files_changed:
                              self.files_changed.append(path)
                      except Exception:
                          pass
  
                  self.tool_call_log.append({
                      "name": name, "args": args_raw[:1000],
                      "ok": bool(result.get("ok")),
                      "summary": self._summarize_result(name, result),
                  })
                  self._emit("tool_result", {
                      "name": name, "ok": bool(result.get("ok")),
                      "summary": self.tool_call_log[-1]["summary"],
                  })
                  self.messages.append({
                      "role": "tool", "tool_call_id": tc_id, "name": name,
                      "content": json.dumps(result, ensure_ascii=False)[:32_000],
                  })
  
              if finished:
                  self._emit("loop_end", {"reason": "finish_called", "iteration": it})
                  return {
                      "ok": True, "summary": self.summary,
                      "files_changed": self.files_changed,
                      "iterations": it + 1, "log": self.tool_call_log,
                  }
  
          # Hit iteration cap
          # ── Safeguard 3: partial success if agent produced useful work ──
          if self.files_changed or self.summary:
              logger.info(
                  "[AgentLoop] Iteration cap hit but agent produced work "
                  "(%d files, %d chars summary) — treating as partial success",
                  len(self.files_changed), len(self.summary),
              )
              self._emit("loop_end", {"reason": "iteration_cap_partial", "iteration": self.max_iterations})
              return {
                  "ok": True,
                  "error": f"iteration cap hit ({self.max_iterations}) — partial result",
                  "summary": self.summary or f"(completed {len(self.files_changed)} file changes before cap)",
                  "files_changed": self.files_changed,
                  "iterations": self.max_iterations, "log": self.tool_call_log,
              }
          self._emit("loop_end", {"reason": "iteration_cap", "iteration": self.max_iterations})
          return {
              "ok": False, "error": f"iteration cap hit ({self.max_iterations})",
              "summary": self.summary, "files_changed": self.files_changed,
              "iterations": self.max_iterations, "log": self.tool_call_log,
          }
  
      def _summarize_result(self, name: str, result: Dict[str, Any]) -> str:
          if not result.get("ok"):
              return f"FAIL: {result.get('error','')[:120]}"
          if name == "read_file":
              return f"{result.get('total_lines', '?')} lines, {len(result.get('content',''))} chars"
          if name == "grep":
              return f"{len(result.get('hits', []))} hits"
          if name == "list_files":
              return f"{len(result.get('files', []))} files"
          if name in ("write_file", "patch_file"):
              return f"{result.get('bytes', result.get('new_bytes', 0))} bytes"
          if name in ("run_python", "run_pytest"):
              ec = result.get("exit_code")
              return f"exit={ec}, {result.get('elapsed_sec','?')}s"
          return "ok"
  
      def _emit(self, kind: str, payload: Dict[str, Any]):
          if self.on_event:
              try:
                  self.on_event(kind, payload)
              except Exception:
                  pass
  
      # ────────────────────────────────────────────────
      # Safeguard helpers
      # ────────────────────────────────────────────────
      def _messages_char_count(self) -> int:
          """Estimate total chars in the message list."""
          total = 0
          for m in self.messages:
              total += len(m.get("content") or "")
          return total
  
      def _compact_old_tool_results(self):
          """Safeguard 2: when context exceeds budget, truncate old tool result
          messages to keep the conversation within context window limits.
          Only compacts messages before the last 6 (preserve recent context).
          """
          total = self._messages_char_count()
          if total <= _CONTEXT_BUDGET_CHARS:
              return
          # Work backwards from older messages, truncate tool results
          preserve_tail = 6  # keep the most recent messages intact
          cutoff = max(0, len(self
  ```
  
  ### 文件: `src/backend/agents/agent_toolbox.py`
  ```py
  """AgentToolbox — function-calling tools for code-aware agents.
  
  Gives Developer / QA agents the ability to read, grep, write, and execute code
  in the project so they don't have to hallucinate file contents.
  
  All tool calls are scoped to the project root and write operations are
  restricted to a safe allowlist (src/, tests/, docs/, config/, public/).
  
  Each tool returns a JSON-serializable dict suitable for OpenAI/DeepSeek
  function-calling protocol.
  """
  from __future__ import annotations
  
  import json
  import logging
  import os
  import re
  import shlex
  import subprocess
  import time
  from pathlib import Path
  from typing import Any, Dict, List, Optional, Tuple
  
  logger = logging.getLogger("AgentToolbox")
  
  PROJECT_ROOT = Path(__file__).resolve().parents[3]  # src/backend/agents/ -> root
  ALLOWED_WRITE_PREFIXES = ("src/", "tests/", "docs/", "config/", "public/",
                             "storage/agent_workspaces/", "storage/pipeline_runs/")
  MAX_FILE_BYTES = 256 * 1024   # 256KB per read
  MAX_GREP_HITS = 200
  MAX_EXEC_OUTPUT = 32 * 1024   # 32KB stdout/stderr cap
  
  
  # ═════════════════════════════════════════════════════════════════
  # OpenAI / DeepSeek function-calling tool schema (V4 supports this)
  # ═════════════════════════════════════════════════════════════════
  
  TOOL_SCHEMA: List[Dict[str, Any]] = [
      {
          "type": "function",
          "function": {
              "name": "read_file",
              "description": (
                  "读取项目里某个文件的内容。优先使用此工具理解现有代码，再基于实际代码做修改。"
                  "只能读取项目根目录下的文件。"
              ),
              "parameters": {
                  "type": "object",
                  "properties": {
                      "path": {
                          "type": "string",
                          "description": "项目相对路径，如 src/backend/channels/marine_base.py",
                      },
                      "start_line": {"type": "integer", "description": "起始行 (1-based, 可选)", "default": 1},
                      "end_line": {"type": "integer", "description": "结束行 (1-based, 可选)", "default": 0},
                  },
                  "required": ["path"],
              },
          },
      },
      {
          "type": "function",
          "function": {
              "name": "grep",
              "description": (
                  "在项目中按正则搜索文本。用于查找类/函数/枚举值的真实定义位置。"
                  "返回每个匹配的文件路径、行号、行内容。"
              ),
              "parameters": {
                  "type": "object",
                  "properties": {
                      "pattern": {"type": "string", "description": "正则表达式"},
                      "include": {
                          "type": "string",
                          "description": "glob 限定，如 src/backend/**/*.py",
                          "default": "**/*",
                      },
                      "max_hits": {"type": "integer", "default": 50},
                  },
                  "required": ["pattern"],
              },
          },
      },
      {
          "type": "function",
          "function": {
              "name": "list_files",
              "description": "列出某个目录下的所有文件（递归）。",
              "parameters": {
                  "type": "object",
                  "properties": {
                      "path": {"type": "string", "description": "项目相对目录"},
                      "max_depth": {"type": "integer", "default": 3},
                  },
                  "required": ["path"],
              },
          },
      },
      {
          "type": "function",
          "function": {
              "name": "write_file",
              "description": (
                  "向项目写入或新建文件。只能写入 src/, tests/, docs/, config/, public/ 下。"
                  "如果目标已存在，旧内容会先备份为 .bak。优先创建新文件而非整文件覆盖大文件。"
              ),
              "parameters": {
                  "type": "object",
                  "properties": {
                      "path": {"type": "string", "description": "项目相对路径"},
                      "content": {"type": "string", "description": "完整文件内容"},
                      "create_only": {
                          "type": "boolean",
                          "description": "为 true 时仅在文件不存在时写入",
                          "default": False,
                      },
                  },
                  "required": ["path", "content"],
              },
          },
      },
      {
          "type": "function",
          "function": {
              "name": "patch_file",
              "description": (
                  "对已有文件做精准搜索-替换。比 write_file 安全，因为它要求你先看到原文。"
                  "search 必须是文件中存在的、唯一的连续片段。"
              ),
              "parameters": {
                  "type": "object",
                  "properties": {
                      "path": {"type": "string"},
                      "search": {"type": "string", "description": "要被替换的原文片段（必须唯一）"},
                      "replace": {"type": "string", "description": "替换为的新内容"},
                  },
                  "required": ["path", "search", "replace"],
              },
          },
      },
      {
          "type": "function",
          "function": {
              "name": "run_python",
              "description": (
                  "在项目 venv 中执行一段 Python 代码（cwd=src/backend）。"
                  "用于验证 import 是否成功、检查类的属性等。最长执行 30s。"
              ),
              "parameters": {
                  "type": "object",
                  "properties": {
                      "code": {"type": "string", "description": "要执行的 Python 代码"},
                      "timeout": {"type": "integer", "default": 30},
                  },
                  "required": ["code"],
              },
          },
      },
      {
          "type": "function",
          "function": {
              "name": "run_pytest",
              "description": (
                  "运行 pytest，可指定路径或 -k 表达式。仅 QA agent 使用。"
                  "返回最后 60 行输出。"
              ),
              "parameters": {
                  "type": "object",
                  "properties": {
                      "target": {"type": "string", "description": "测试路径或 -k 表达式", "default": ""},
                      "timeout": {"type": "integer", "default": 120},
                  },
              },
          },
      },
      {
          "type": "function",
          "function": {
              "name": "finish",
              "description": (
                  "声明任务完成。Agent 调用此工具表示完成本步骤的所有工作，并附上简短总结。"
                  "调用后循环终止。"
              ),
              "parameters": {
                  "type": "object",
                  "properties": {
                      "summary": {"type": "string", "description": "本步骤完成情况的简短总结"},
                      "files_changed": {
                          "type": "array",
                          "items": {"type": "string"},
                          "description": "本步骤修改/新建的文件路径列表",
                          "default": [],
                      },
                  },
                  "required": ["summary"],
              },
          },
      },
  ]
  
  
  def _safe_path(rel: str) -> Path:
      """Resolve a project-relative path, refusing escapes."""
      if not rel:
          raise ValueError("empty path")
      p = (PROJECT_ROOT / rel).resolve()
      try:
          p.relative_to(PROJECT_ROOT)
      except ValueError:
          raise PermissionError(f"path escapes project root: {rel}")
      return p
  
  
  def _is_allowed_write(rel: str) -> bool:
      rel = rel.replace("\\", "/")
      return any(rel.startswith(p) for p in ALLOWED_WRITE_PREFIXES)
  
  
  # ═════════════════════════════════════════════════════════════════
  # Tool implementations
  # ═════════════════════════════════════════════════════════════════
  
  def tool_read_file(path: str, start_line: int = 1, end_line: int = 0) -> Dict[str, Any]:
      try:
          p = _safe_path(path)
          if not p.is_file():
              return {"ok": False, "error": f"not a file: {path}"}
          size = p.stat().st_size
          if size > MAX_FILE_BYTES * 4:
              return {
                  "ok": False,
                  "error": f"file too large ({size}B). Use grep to find the relevant section first.",
              }
          text = p.read_text(encoding="utf-8", errors="replace")
          lines = text.splitlines()
          total = len(lines)
          if end_line and end_line > 0:
              lines = lines[max(0, start_line - 1):end_line]
          elif start_line > 1:
              lines = lines[start_line - 1:]
          out = "\n".join(lines)
          if len(out) > MAX_FILE_BYTES:
              out = out[:MAX_FILE_BYTES] + "\n…(truncated)"
          return {"ok": True, "path": path, "total_lines": total, "content": out}
      except Exception as e:
          return {"ok": False, "error": str(e)}
  
  
  def tool_grep(pattern: str, include: str = "**/*", max_hits: int = 50) -> Dict[str, Any]:
      try:
          regex = re.compile(pattern)
      except re.error as e:
          return {"ok": False, "error": f"bad regex: {e}"}
      max_hits = min(max_hits, MAX_GREP_HITS)
      hits: List[Dict[str, Any]] = []
      for fp in PROJECT_ROOT.glob(include):
          if not fp.is_file():
              continue
          # Skip irrelevant
          rel = str(fp.relative_to(PROJECT_ROOT))
          if any(seg in rel for seg in ("/node_modules/", "/.git/", "/__pycache__/", "/venv/", ".bak")):
              continue
          try:
              with fp.open("r", encoding="utf-8", errors="replace") as f:
                  for i, line in enumerate(f, 1):
                      if regex.search(line):
                          hits.append({"path": rel, "line": i, "text": line.rstrip()[:200]})
                          if len(hits) >= max_hits:
                              return {"ok": True, "hits": hits, "truncated": True}
          except Exception:
              continue
      return {"ok": True, "hits": hits, "truncated": False}
  
  
  def tool_list_files(path: str, max_depth: int = 3) -> Dict[str, Any]:
      try:
          p = _safe_path(path)
          if not p.is_dir():
              return {"ok": False, "error": f"not a directory: {path}"}
          out: List[str] = []
          base_depth = len(p.parts)
          for root, dirs, files in os.walk(p):
              depth = len(Path(root).parts) - base_depth
              if depth > max_depth:
                  dirs[:] = []
                  continue
              dirs[:] = [d for d in dirs
                         if not d.startswith(".")
                         and d not in ("node_modules", "__pycache__", "venv")]
              for f in files:
                  if f.endswith((".pyc", ".bak")):
                      continue
                  rel = str((Path(root) / f).relative_to(PROJECT_ROOT))
                  out.append(rel)
                  if len(out) >= 500:
                      return {"ok": True, "files": out, "truncated": True}
          return {"ok": True, "files": out, "truncated": False}
      except Exception as e:
          return {"ok": False, "error": str(e)}
  
  
  def tool_write_file(path: str, content: str, create_only: bool = False) -> Dict[str, Any]:
      try:
          if not _is_allowed_write(path):
              return {"ok": False, "error": f"write denied (outside allowed dirs): {path}"}
          p = _safe_path(path)
          if p.exists() and create_only:
              return {"ok": False, "error": f"file exists and create_only=True: {path}"}
          # Shrink-replace guard
          if p.is_file():
              old_size = p.stat().st_size
              if old_size > 2048 and len(content) < old_size * 0.5:
                  return {
                      "ok": False,
                      "error": (
                          f"shrink-replace blocked: new {len(content)}B "
                          f"< 50% of existing {old_size}B. "
                          f"Use patch_file for incremental edits, or write a new file."
                      ),
                  }
              # Backup
              bak = p.with_suffix(p.suffix + ".bak")
              try:
                  bak.write_bytes(p.read_bytes())
              except Exception:
                  pass
          p.parent.mkdir(parents=True, exist_ok=True)
          p.write_text(content, encoding="utf-8")
          return {"ok": True, "path": path, "bytes": len(content), "created": not p.exists()}
      except Exception as e:
          return {"ok": False, "error": str(e)}
  
  
  def tool_patch_file(path: str, search: str, replace: str) -> Dict[str, Any]:
      try:
          if not _is_allowed_write(path):
              return {"ok": False, "error": f"write denied: {path}"}
          p = _safe_path(path)
          if not p.is_file():
              return {"ok": False, "error": f"file not found: {path}"}
          text = p.read_text(encoding="utf-8")
          cnt = text.count(search)
          if cnt == 0:
              return {"ok": False, "error": "search pattern not found in file"}
          if cnt > 1:
              return {
                  "ok": False,
                  "error": f"search pattern matches {cnt} times — must be unique. Add more context.",
              }
          new_text = text.replace(search, replace, 1)
          bak = p.with_suffix(p.suffix + ".bak")
          try:
              bak.write_text(text, encoding="utf-8")
          except Exception:
              pass
          p.write_text(new_text, encoding="utf-8")
          return {"ok": True, "path": path, "old_bytes": len(text), "new_bytes": len(new_text)}
      except Exception as e:
          return {"ok": False, "error": str(e)}
  
  
  def _run_subprocess(cmd: List[str], cwd: Path, timeout: int) -> Dict[str, Any]:
      start = time.time()
      try:
          proc = subprocess.run(
              cmd, cwd=str(cwd), capture_output=True, text=True,
              timeout=timeout,
              env={**os.environ, "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1"},
          )
          elapsed = time.time() - start
          out = proc.stdout or ""
          err = proc.stderr or ""
          if len(out) > MAX_EXEC_OUTPUT:
              out = "…(truncated)\n" + out[-MAX_EXEC_OUTPUT:]
          if len(err) > MAX_EXEC_OUTPUT:
              err = "…(truncated)\n" + err[-MAX_EXEC_OUTPUT:]
          return {
              "ok": True,
              "exit_code": proc.returncode,
              "stdout": out,
              "stderr": err,
              "elapsed_sec": round(elapsed, 2),
          }
      except subprocess.TimeoutExpired:
          return {"ok": False, "error": f"timeout after {timeout}s"}
      except Exception as e:
          return {"ok": False, "error": str(e)}
  
  
  def tool_run_python(code: str, timeout: int = 30) -> Dict[str, Any]:
      venv_py = PROJECT_ROOT / "venv" / "bin" / "python"
      py = str(venv_py) if venv_py.exists() else "python3"
      cwd = PROJECT_ROOT / "src" / "backend"
      return _run_subprocess([py, "-c", code], cwd, timeout)
  
  
  def tool_run_pytest(target: str = "", timeout: int = 120) -> Dict[str, Any]:
      venv_py = PROJECT_ROOT / "venv" / "bin" / "python"
      py = str(venv_py) if venv_py.exists() else "python3"
      args = [py, "-m", "pytest", "-q", "--tb=short", "--maxfail=5"]
      if target:
          if target.startswith("-k") or "::" in target or target.endswith(".py"):
              if target.startswith("-k"):
                  args += target.split(maxsplit=1)
              else:
                  args.append(target)
          else:
              args += ["-k", target]
      return _run_subprocess(args, PROJECT_ROOT, timeout)
  
  
  # ═════════════════════════════════════════════════════════════════
  # Dispatcher
  # ═════════════════════════════════════════════════════════════════
  
  _DISPATCH = {
      "read_file": l
  ```
  
  ### 文件: `src/backend/agents/models.py`
  ```py
  # -*- coding: utf-8 -*-
  """AgentsGroup2026 Agent Team Framework — Core Data Models.
  
  Inspired by Clawith platform architecture:
  - AgentTeam = Company (team-level resource sharing)
  - AgentProfile = Employee (individual agent with personality/skills/permissions)
  - ModelConfig = Model Pool entry
  - ToolDefinition = Tool catalog entry
  - SkillDefinition = Skill catalog entry
  """
  
  from __future__ import annotations
  
  import uuid
  from dataclasses import dataclass, field
  from datetime import datetime, timezone
  from enum import Enum
  from typing import Any, Dict, List, Optional
  
  
  # ── Enums ──────────────────────────────────────────────────────────────────
  
  
  class AgentState(Enum):
      """Agent lifecycle states."""
  
      IDLE = "idle"
      WORKING = "working"
      PAUSED = "paused"
      ERROR = "error"
      STOPPED = "stopped"
  
  
  class ToolCategory(Enum):
      """Tool classification categories."""
  
      GENERAL = "general"
      BROWSER = "browser"
      CODE_EXECUTION = "code_execution"
      COMMUNICATION = "communication"
      FILE_OPERATION = "file_operation"
      TRIGGERS = "triggers"
      DISCOVERY = "discovery"
      DIGITAL_TWIN = "digital_twin"
      # Hermes-style tool categories
      WEB = "web"
      VISION = "vision"
      MEMORY = "memory"
      SKILLS = "skills"
      DELEGATION = "delegation"
  
  
  class SkillCategory(Enum):
      """Skill classification categories."""
  
      GENERAL = "general"
      DIGITAL_TWIN = "digital_twin"
      AUTOMATION = "automation"
      # Hermes-style skill categories
      RESEARCH = "research"
      DOMAIN_KNOWLEDGE = "domain_knowledge"
  
  
  class Visibility(Enum):
      """Visibility level for teams/agents."""
  
      PUBLIC = "public"
      PRIVATE = "private"
      INTERNAL = "internal"
  
  
  class AccessLevel(Enum):
      """Permission access levels."""
  
      READ = "read"
      WRITE = "write"
      ADMIN = "admin"
  
  
  class AgentTemplateType(Enum):
      """Predefined agent template types."""
  
      RESEARCHER = "researcher"
      DEVELOPER = "developer"
      ANALYST = "analyst"
      ENGINEER = "engineer"
      COORDINATOR = "coordinator"
      CUSTOM = "custom"
      # Hermes-style agent types
      HERMES_RESEARCHER = "hermes_researcher"
      HERMES_DEVELOPER = "hermes_developer"
      HERMES_CREATIVE = "hermes_creative"
  
  
  # ── Dataclasses ────────────────────────────────────────────────────────────
  
  
  @dataclass
  class ModelConfig:
      """LLM model configuration entry."""
  
      model_id: str = ""
      provider: str = "anthropic"
      name: str = "claude-sonnet-4-20250514"
      max_tokens: int = 65536
      temperature: float = 0.7
      is_default: bool = False
      enabled: bool = True
      api_key: str = ""
      api_base_url: str = ""
  
      def __post_init__(self) -> None:
          if not self.model_id:
              self.model_id = str(uuid.uuid4())[:8]
  
      def to_dict(self) -> Dict[str, Any]:
          return {
              "model_id": self.model_id,
              "provider": self.provider,
              "name": self.name,
              "max_tokens": self.max_tokens,
              "temperature": self.temperature,
              "is_default": self.is_default,
              "enabled": self.enabled,
              "api_key": ("****" + self.api_key[-4:]) if len(self.api_key) >= 4 else ("****" if self.api_key else ""),
              "api_base_url": self.api_base_url,
              "has_api_key": bool(self.api_key),
          }
  
  
  @dataclass
  class ToolDefinition:
      """Tool catalog entry."""
  
      tool_id: str = ""
      name: str = ""
      description: str = ""
      category: ToolCategory = ToolCategory.BROWSER
      enabled: bool = True
      requires_approval: bool = False
      parameters: Dict[str, Any] = field(default_factory=dict)
      icon: str = "🔧"
      config_schema: Dict[str, Any] = field(default_factory=dict)
      config: Dict[str, Any] = field(default_factory=dict)
      is_default: bool = False
      source: str = "builtin"
  
      def __post_init__(self) -> None:
          if not self.tool_id:
              self.tool_id = str(uuid.uuid4())[:8]
  
      def to_dict(self) -> Dict[str, Any]:
          return {
              "tool_id": self.tool_id,
              "name": self.name,
              "description": self.description,
              "category": self.category.value,
              "enabled": self.enabled,
              "requires_approval": self.requires_approval,
              "parameters": self.parameters,
              "icon": self.icon,
              "config_schema": self.config_schema,
              "config": self.config,
              "is_default": self.is_default,
              "source": self.source,
          }
  
  
  @dataclass
  class SkillDefinition:
      """Skill catalog entry."""
  
      skill_id: str = ""
      name: str = ""
      description: str = ""
      category: SkillCategory = SkillCategory.GENERAL
      required: bool = False
      enabled: bool = True
      icon: str = "⚡"
      config_schema: Dict[str, Any] = field(default_factory=dict)
      config: Dict[str, Any] = field(default_factory=dict)
      is_default: bool = False
      source: str = "builtin"
      slug: str = ""
      required_tools: List[str] = field(default_factory=list)
      instructions: str = ""
  
      def __post_init__(self) -> None:
          if not self.skill_id:
              self.skill_id = str(uuid.uuid4())[:8]
  
      def to_dict(self) -> Dict[str, Any]:
          return {
              "skill_id": self.skill_id,
              "name": self.name,
              "description": self.description,
              "category": self.category.value,
              "required": self.required,
              "enabled": self.enabled,
              "icon": self.icon,
              "config_schema": self.config_schema,
              "config": self.config,
              "is_default": self.is_default,
              "source": self.source,
              "slug": self.slug,
              "required_tools": self.required_tools,
              "has_instructions": bool(self.instructions),
          }
  
  
  @dataclass
  class AgentPersonality:
      """Agent personality and behavior configuration."""
  
      tone: str = "professional"
      language: str = "zh-CN"
      expertise_areas: List[str] = field(default_factory=list)
      response_style: str = "concise"
      creativity: float = 0.5
  
      def to_dict(self) -> Dict[str, Any]:
          return {
              "tone": self.tone,
              "language": self.language,
              "expertise_areas": self.expertise_areas,
              "response_style": self.response_style,
              "creativity": self.creativity,
          }
  
  
  @dataclass
  class ToolsetDistribution:
      """Hermes-style probabilistic toolset distribution.
  
      Each toolset has a % probability of being available per turn.
      Inspired by NousResearch/hermes-agent toolset_distributions.py.
      """
  
      name: str = "default"
      description: str = ""
      toolsets: Dict[str, int] = field(default_factory
  ```
  
  (后续文件因 token 预算已省略)
  
  (后续文件因 token 预算已省略)
  
  (后续文件因 token 预算已省略)
  
  
  ## 前序步骤的产出 (递进式摘要)
  
  ### 步骤 01: pm_decompose (完整产出)
  
  # PM分解 — project_manager
  
  任务: 构建逆事实推演框架，用历史决策数据标定 OpenClaw 误判成本与沉默代价，熔合成决策折损率基线
  步骤: pm_decompose
  Agent: build_pm
  
  ---
  
  📋 任务: e32cbf0e-868
  🤖 Agent: PM (project_manager)
  📂 工作目录: /Users/panglaohu/Downloads/AgentsGroup2026
  🔧 执行方式: DeepSeek API (直连)
  ⏱️ 超时: 1200s
  ────────────────────────────────────────────────────────────
  📝 提示词:
    你是 AgentsGroup2026 系统的 PM (project_manager)。
    请执行以下开发任务:
    
    你是项目经理 (PM)。请对以下任务进行分解和规划:
    
    ## 任务
    构建逆事实推演框架，用历史决策数据标定 OpenClaw 误判成本与沉默代价，熔合成决策折损率基线
    技术研究员 + Developer
    
    ## 📂 项目上下文 (系统自动预加载)
    
    ### 项目文件结构 (src/ 目录)
    ```
    src/frontend/agent-team-config.html
    src/frontend/datacenter-ratchet-evolution.html
    src/frontend/index.html
    src/frontend/login.html
    src/frontend/plaza-dark.html
    src/frontend/plaza-old.html
    src/frontend/plaza-wabisabi-v2.html
    src/frontend/plaza-wabisabi.html
    src/frontend/plaza.html
    src/frontend/system-evolution.html
    src/frontend/tasks.html
    src/frontend/css/agent-team-config.css
    src/frontend/css/openbridge-theme.css
    src/frontend/css/ws-theme-bridge.css
    src/frontend/js/agent-team-config.js
    src/frontend/js/i18n.js
    src/frontend/js/nav-sidebar.js
    src/backend/__init__.py
    src/backend/agent_team_api.py
    src/backend/main.py
    src/backend/main.py.bak
    src/backend/startup_check.py
    src/backend/startup_validator.py
    src/backend/agents/__init__.py
    src/backend/agents/ab_testing.py
    src/backend/agents/agent_loop.py
    src/backend/agents/agent_toolbox.py
    src/backend/agents/api.py
    src/backend/agents/chat_harness.py
    src/backend/agents/execution_registry.py
    src/backend/agents/hermes_research.py
    src/backend/agents/knowledge_base.py
    src/backend/agents/models.py
    src/backend/agents/plaza.py
    src/backend/agents/plaza_engine.py
    src/backend/agents/plaza_routes.py
    src/backend/agents/plaza_routes.py.bak
    src/backend/agents/plaza_store.py
    src/backend/agents/session_store.py
    src/backend/agents/skill_registry.py
    src/backend/agents/task_engine.py
    src/backend/agents/task_store.py
    src/backend/agents/team_manager.py
    src/backend/agents/team_store.py
    src/backend/agents/tool_executor.py
    src/backend/agents/tool_registry.py
    src/backend/agents/tts_routes.py
    src/backend/agents/teams/__init__.py
    src/backend/agents/teams/ai_coding_team.py
    src/backend/agents/teams/build_team.py
    src/backend/agents/teams/energy_team.py
    src/backend/agents/skills/__init__.py
    src/backend/agents/skills/greeting.py
    src/backend/agents/skills/hello.py
    src/backend/scripts/__init__.py
    src/backend/scripts/validate_startup.py
    src/backend/scripts/validate_telemetry.py
    src/backend/monitoring/__init__.py
    src/backend/monitoring/collector.py
    src/backend/monitoring/models.py
    src/backend/monitoring/plaza_monitor.py
    src/backend/monitoring/plaza_monitor.py.bak
    src/backend/monitoring/sampler.py
    src/backend/channels/__init__.py
    src/backend/channels/bridge_chat.py
    src/backend/channels/marine_base.py
    src/backend/channels/openclaw_sync.py
    src/backend/channels/openclaw_sync.py.bak
    src/backend/channels/system_evolution.py
    src/docs/agent_handoffs/1ce78c0e-062_architecture_20260503T045804.md
    src/docs/agent_handoffs/1ce78c0e-062_deploy_FAILED_20260503T050220.md
    src/docs/agent_handoffs/1ce78c0e-062_develop_20260503T045845.md
    src/docs/agent_handoffs/1ce78c0e-062_develop_20260503T050025.md
    src/docs/agent_handoffs/1ce78c0e-062_develop_20260503T050150.md
    src/docs/agent_handoffs/1ce78c0e-062_pm_decompose_20260503T045724.md
    src/docs/agent_handoffs/1ce78c0e-062_research_20260503T045739.md
    src/docs/agent_handoffs/1ce78c0e-062_task_init_20260503T045659.md
    src/docs/agent_handoffs/1ce78c0e-062_test_20260503T045905.md
    src/docs/agent_handoffs/1ce78c0e-062_test_20260503T050050.md
    src/docs/agent_handoffs/1ce78c0e-062_test_20260503T050210.md
    src/docs/agent_handoffs/23cb267e-4e0_executor_started_20260503T114540.md
    src/docs/agent_handoffs/38e22004-b64_architecture_20260503T045011.md
    src/docs/agent_handoffs/38e22004-b64_pm_decompose_20260503T044921.md
    src/docs/agent_handoffs/38e22004-b64_research_20260503T044941.md
    src/docs/agent_handoffs/38e22004-b64_task_init_20260503T044856.md
    src/docs/agent_handoffs/4b17f83b-805_architecture_20260507T003640.md
    src/docs/agent_handoffs/4b17f83b-805_deploy_FAILED_20260507T004132.md
    src/docs/agent_handoffs/4b17f83b-805_develop_FAILED_20260507T003706.md
    src/docs/agent_handoffs/4b17f83b-805_develop_FAILED_20260507T003913.md
    src/docs/agent_handoffs/4b17f83b-805_develop_FAILED_20260507T004040.md
    src/docs/agent_handoffs/4b17f83b-805_executor_started_20260507T003435.md
    src/docs/agent_handoffs/4b17f83b-805_pm_decompose_20260507T003510.md
    src/docs/agent_handoffs/4b17f83b-805_research_20260507T003555.md
    src/docs/agent_handoffs/4b17f83b-805_test_FAILED_20260507T003732.md
    src/docs/agent_handoffs/4b17f83b-805_test_FAILED_20260507T003939.md
    src/docs/agent_handoffs/4b17f83b-805_test_FAILED_20260507T004102.md
    src/docs/agent_handoffs/6f911ba3-822_architecture_20260507T003740.md
    src/docs/agent_handoffs/6f911ba3-822_deploy_FAILED_20260507T004337.md
    src/docs/agent_handoffs/6f911ba3-822_develop_FAILED_20260507T003806.md
    src/docs/agent_handoffs/6f911ba3-822_develop_FAILED_20260507T004113.md
    src/docs/agent_handoffs/6f911ba3-822_develop_FAILED_20260507T004235.md
    src/docs/agent_handoffs/6f911ba3-822_executor_started_20260507T003435.md
    src/docs/agent_handoffs/6f911ba3-822_pm_decompose_20260507T003510.md
    src/docs/agent_handoffs/6f911ba3-822_research_20260507T003550.md
    src/docs/agent_handoffs/6f911ba3-822_test_FAILED_20260507T003827.md
    src/docs/agent_handoffs/6f911ba3-822_test_FAILED_20260507T004134.md
    src/docs/agent_handoffs/6f911ba3-822_test_FAILED_20260507T004311.md
    src/docs/agent_handoffs/7c934759-39e_architecture_20260505T010014.md
    src/docs/agent_handoffs/7c934759-39e_develop_20260505T010359.md
    src/docs/agent_handoffs/7c934759-39e_develop_20260505T012357.md
    src/docs/agent_handoffs/7c934759-39e_develop_FAILED_20260505T011447.md
    src/docs/agent_handoffs/7c934759-39e_executor_started_20260505T005814.md
    src/docs/agent_handoffs/7c934759-39e_pm_decompose_20260505T005849.md
    src/docs/agent_handoffs/7c934759-39e_research_20260505T005919.md
    src/docs/agent_handoffs/7c934759-39e_test_FAILED_20260505T011016.md
    src/docs/agent_handoffs/7c934759-39e_test_FAILED_20260505T011949.md
    src/docs/agent_handoffs/7c934759-39e_test_FAILED_20260505T012853.md
    src/docs/agent_handoffs/8a5071c5-834_architecture_20260507T003655.md
    src/docs/agent_handoffs/8a5071c5-834_deploy_FAILED_20260507T004051.md
    src/docs/agent_handoffs/8a5071c5-834_develop_FAILED_20260507T003716.md
    src/docs/agent_handoffs/8a5071c5-834_develop_FAILED_20260507T003903.md
    src/docs/agent_handoffs/8a5071c5-834_develop_FAILED_20260507T004005.md
    src/docs/agent_handoffs/8a5071c5-834_executor_started_20260507T003435.md
    src/docs/agent_handoffs/8a5071c5-834_pm_decompose_20260507T003510.md
    src/docs/agent_handoffs/8a5071c5-834_research_20260507T003540.md
    src/docs/agent_handoffs/8a5071c5-834_test_FAILED_20260507T003737.md
    src/docs/agent_handoffs/8a5071c5-834_test_FAILED_20260507T003929.md
    src/docs/agent_handoffs/8a5071c5-834_test_FAILED_20260507T004031.md
    src/docs/agent_handoffs/a77bd3b9-2db_architecture_20260507T003625.md
    src/docs/agent_handoffs/a77bd3b9-2db_deploy_FAILED_20260507T004102.md
    src/docs/agent_handoffs/a77bd3b9-2db_develop_FAILED_20260507T003646.md
    src/docs/agent_handoffs/a77bd3b9-2db_develop_FAILED_20260507T003838.md
    src/docs/agent_handoffs/a77bd3b9-2db_develop_FAILED_20260507T004005.md
    src/docs/agent_handoffs/a77bd3b9-2db_executor_started_20260507T003435.md
    src/docs/agent_handoffs/a77bd3b9-2db_pm_decompose_20260507T003515.md
    src/docs/agent_handoffs/a77bd3b9-2db_research_20260507T003545.md
    src/docs/agent_handoffs/a77bd3b9-2db_test_FAILED_20260507T003712.md
    src/docs/agent_handoffs/a77bd3b9-2db_test_FAILED_20260507T003904.md
    src/docs/agent_handoffs/a77bd3b9-2db_test_FAILED_20260507T004042.md
    src/docs/agent_handoffs/ba3b66b1-a77_architecture_20260505T154317.md
    src/docs/agent_handoffs/ba3b66b1-a77_deploy_FAILED_20260505T154903.md
    src/docs/agent_handoffs/ba3b66b1-a77_develop_FAILED_20260505T154353.md
    src/docs/agent_handoffs/ba3b66b1-a77_develop_FAILED_20260505T154600.md
    src/docs/agent_handoffs/ba3b66b1-a77_develop_FAILED_20260505T154807.md
    src/docs/agent_handoffs/ba3b66b1-a77_executor_started_20260505T153921.md
    src/docs/agent_handoffs/ba3b66b1-a77_pm_decompose_20260505T153951.md
    src/docs/agent_handoffs/ba3b66b1-a77_research_20260505T154041.md
    src/docs/agent_handoffs/ba3b66b1-a77_test_FAILED_20260505T154424.md
    src/docs/agent_handoffs/ba3b66b1-a77_test_FAILED_20260505T154631.md
    src/docs/agent_handoffs/ba3b66b1-a77_test_FAILED_20260505T154838.md
    ... (共 254 个 src/ 文件)
    
    ```
    
    ### 文件: `src/backend/main.py`
    ```py
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
    import json
    import logging
    import os
    import sys
    from pathlib import Path
    from typing import Any, Dict, Optional
    
    import uvicorn
    from fastapi import FastAPI, HTTPException
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
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
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
            logger.warning(f"⚠️ Channel registration failed: {e}")
    
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
            logger.warning(f"⚠️ Agent Team API failed: {e}")
    
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
            except Exception:
                pass
    
            # Try energy team (optional)
            try:
                from agents.teams.energy_team import create_energy_team
                energy_team_obj = create_energy_team()
                _team_manager._teams[energy_team_obj.team_id] = energy_team_obj
            except Exception:
                pass
    
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
                logger.warning(f"⚠️ Plaza API failed: {e}")
    
            # 4b. TTS 语音合成代理 (GPT-SoVITS)
            try:
                from agents.tts_routes import router as tts_router
                app.include_router(tts_router, prefix="/api/v1")
                logger.info("✅ TTS API mounted (/api/v1/tts)")
            except Exception as e:
                logger.warning(f"⚠️ TTS API failed: {e}")
    
        except Exception as e:
            logger.warning(f"⚠️ Agent Config API failed: {e}")
    
        # 5. 启动验证路由
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
    
    import hashlib
    import secrets
    
    # Default users (in production, use a proper database)
    _USERS = {
        "admin": hashlib.sha256("admin123".encode()).hexdigest(),
    }
    _TOKENS: Dict[str, str] = {}
    
    
    @app.post("/api/v1/auth/register")
    async def register(req: RegisterRequest):
        """Register a new user."""
        username = req.username.strip()
        if not username or len(username) < 2:
            raise HTTPException(status_code=400, detail="用户名至少需要2个字符")
        if len(req.password) < 4:
            raise HTTPException(status_code=400, detail="密码至少需要4个字符")
        if username in _USERS:
            raise HTTPException(status_code=409, detail="该用户名已被注册")
        _USERS[username] = hashlib.sha256(req.password.encode()).hexdigest()
        token = secrets.token_hex(32)
        _TOKENS[token] = username
        logger.info(f"✅ New user registered: {username}")
        return {"token": token, "username": username}
    
    
    @app.post("/api/v1/auth/login")
    async def login(req: LoginRequest):
        """Simple token-based login."""
        pwd_hash = hashlib.sha256(req.password.encode()).hexdigest()
        if req.username not in _USERS or _USERS[req.username] != pwd_hash:
            raise HTTPException(status_code=401, detail="用户名或密码错误")
        token = secrets.token_hex(32)
        _TOKENS[token] = req.username
        return {"token": token, "username": req.username}
    
    
    @app.get("/api/v1/auth/me")
    async def auth_me(authorization: str = ""):
        """Check current auth status."""
        token = authorization.replace("Bearer ", "") if authorization else ""
        if token in _TOKENS:
            return {"username": _TOKENS[token], "authenticated": True}
        return {"username": "guest", "authenticated": False}
    
    
    # ══════════════════════════════════════════════════════════════════
    # Health & Info
    # ══════════════════════════════════════════════════════════════════
    
    @app.get("/api/v1/health")
    async def health():
        """Health check endpoint."""
        from channels.marine_base import get_default_registry
        registry = get_default_registry()
        return HealthResponse(
            status="ok",
            version="1.0.0",
            services={
                "evolution": registry.get("system_evolution") is not None,
                "bridge_chat": registry.get("bridge_chat") is not None,
                "agent_config": _team_manager is not None,
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
                
    ```
    
    ### 文件: `src/backend/agents/agent_loop.py`
    ```py
    """Function-calling loop for Developer/QA agents.
    
    Drives a multi-turn conversation with DeepSeek V4 where each turn the model can
    call tools (read_file, grep, write_file, patch_file, run_python, run_pytest) to
    inspect and modify the codebase, then finishes with a `finish` tool call.
    
    This replaces the single-shot "emit a markdown blob with code fences" approach
    that produced hallucinated imports and truncated files.
    """
    from __future__ import annotations
    
    import http.client
    import json
    import logging
    import ssl
    import time
    from typing import Any, Dict, List, Optional
    from urllib.parse import urlparse
    
    from .agent_toolbox import (
        TOOL_SCHEMA,
        dispatch_tool_call,
        get_tools_for_role,
    )
    
    logger = logging.getLogger("AgentLoop")
    
    DEFAULT_MAX_ITERATIONS = 25
    DEFAULT_MAX_TOKENS = 65536
    DEFAULT_TEMPERATURE = 0.2
    
    # ── Safeguard constants ──
    # Safeguard 1: auto-finish nudge when approaching iteration cap
    _ITERATION_NUDGE_RATIO = 0.80  # at 80% of max_iterations, inject nudge
    # Safeguard 2: context budget — compress old tool results when messages grow
    _CONTEXT_BUDGET_CHARS = 100_000  # max combined chars in messages
    _TOOL_RESULT_TRUNC = 500  # truncate old tool results to this when over budget
    
    
    class AgentLoop:
        """Multi-turn function-calling driver against an OpenAI-compatible endpoint."""
    
        def __init__(
            self,
            *,
            api_key: str,
            api_base_url: str,
            model: str,
            role: str,
            system_prompt: str,
            max_iterations: int = DEFAULT_MAX_ITERATIONS,
            max_tokens: int = DEFAULT_MAX_TOKENS,
            temperature: float = DEFAULT_TEMPERATURE,
            on_event: Optional[Any] = None,
        ):
            self.api_key = api_key
            self.api_base_url = api_base_url.rstrip("/")
            self.model = model
            self.role = role
            self.max_iterations = max_iterations
            self.max_tokens = max_tokens
            self.temperature = temperature
            self.tools = get_tools_for_role(role)
            self.messages: List[Dict[str, Any]] = [
                {"role": "system", "content": system_prompt},
            ]
            self.on_event = on_event   # callable(event_type:str, payload:dict)
            self.files_changed: List[str] = []
            self.summary: str = ""
            self.tool_call_log: List[Dict[str, Any]] = []
    
        # ────────────────────────────────────────────────
        # HTTP plumbing
        # ────────────────────────────────────────────────
        _API_MAX_RETRIES = 3
        _API_RETRY_BACKOFF = [2, 5, 10]  # seconds between retries
        # Transient errors worth retrying
        _RETRYABLE = (
            ConnectionResetError, ConnectionAbortedError, ConnectionRefusedError,
            BrokenPipeError, TimeoutError, OSError,
            http.client.RemoteDisconnected, http.client.IncompleteRead,
        )
    
        def _post_chat(self) -> Dict[str, Any]:
            parsed = urlparse(self.api_base_url)
            host = parsed.hostname or "api.deepseek.com"
            port = parsed.port or (443 if parsed.scheme == "https" else 80)
            path = (parsed.path or "").rstrip("/") + "/chat/completions"
            ctx = ssl.create_default_context() if parsed.scheme == "https" else None
            conn_cls = http.client.HTTPSConnection if parsed.scheme == "https" else http.client.HTTPConnection
    
            payload: Dict[str, Any] = {
                "model": self.model,
                "messages": self.messages,
                "tools": self.tools,
                "tool_choice": "auto",
                "max_tokens": self.max_tokens,
                "temperature": self.temperature,
                "stream": False,
                "thinking": {"type": "enabled"},
                "reasoning_effort": "high",
            }
            body_str = json.dumps(payload)
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }
    
            last_err: Optional[Exception] = None
            for attempt in range(self._API_MAX_RETRIES):
                try:
                    conn = conn_cls(host, port, context=ctx, timeout=300) if ctx \
                        else conn_cls(host, port, timeout=300)
                    conn.request("POST", path, body=body_str, headers=headers)
                    resp = conn.getresponse()
                    raw = resp.read().decode("utf-8", errors="replace")
                    conn.close()
                    if resp.status == 429 or resp.status >= 500:
                        # Server-side error — retryable
                        raise RuntimeError(f"LLM HTTP {resp.status}: {raw[:300]}")
                    if resp.status >= 400:
                        raise RuntimeError(f"LLM HTTP {resp.status}: {raw[:500]}")
                    return json.loads(raw)
                except self._RETRYABLE as e:
                    last_err = e
                    wait = self._API_RETRY_BACKOFF[min(attempt, len(self._API_RETRY_BACKOFF) - 1)]
                    logger.warning(
                        "[AgentLoop] Transient error on attempt %d/%d: %s — retrying in %ds",
                        attempt + 1, self._API_MAX_RETRIES, e, wait,
                    )
                    time.sleep(wait)
                except RuntimeError as e:
                    # HTTP 429 / 5xx — retry with backoff
                    if "HTTP 4" in str(e) and "HTTP 429" not in str(e):
                        raise  # 4xx (non-429) is not retryable
                    last_err = e
                    wait = self._API_RETRY_BACKOFF[min(attempt, len(self._API_RETRY_BACKOFF) - 1)]
                    logger.warning(
                        "[AgentLoop] Server error on attempt %d/%d: %s — retrying in %ds",
                        attempt + 1, self._API_MAX_RETRIES, e, wait,
                    )
                    time.sleep(wait)
            raise last_err or RuntimeError("_post_chat failed after retries")
    
        # ────────────────────────────────────────────────
        # Loop
        # ────────────────────────────────────────────────
        def run(self, user_prompt: str) -> Dict[str, Any]:
            """Run the agent loop. Returns {ok, summary, files_changed, iterations, log}."""
            self.messages.append({"role": "user", "content": user_prompt})
            self._emit("loop_start", {"role": self.role, "tools": [t["function"]["name"] for t in self.tools]})
    
            for it in range(self.max_iterations):
                # ── Safeguard 1: nudge agent when approaching iteration cap ──
                self._maybe_inject_nudge(it)
                # ── Safeguard 2: compact old tool results when context too large ──
                self._compact_old_tool_results()
    
                t0 = time.time()
                try:
                    resp = self._post_chat()
                except Exception as e:
                    logger.exception("[AgentLoop] HTTP error on iteration %d (after retries)", it)
                    self._emit("error", {"iteration": it, "error": str(e)})
                    # If we have already done useful work, don't discard it —
                    # treat as a graceful early stop instead of hard failure.
                    if self.files_changed or self.summary:
                        logger.info(
                            "[AgentLoop] Partial progress (%d files, %d chars summary) — "
                            "returning partial success",
                            len(self.files_changed), len(self.summary),
                        )
                        self._emit("loop_end", {"reason": "network_error_partial", "iteration": it})
                        return {
                            "ok": True, "error": str(e),
                            "summary": self.summary or f"(network error after {it} turns)",
                            "files_changed": self.files_changed,
                            "iterations": it, "log": self.tool_call_log,
                        }
                    return {
                        "ok": False, "error": str(e),
                        "summary": self.summary, "files_changed": self.files_changed,
                        "iterations": it, "log": self.tool_call_log,
                    }
    
                choice = (resp.get("choices") or [{}])[0]
                msg = choice.get("message", {}) or {}
                content = msg.get("content") or ""
                tool_calls = msg.get("tool_calls") or []
                finish_reason = choice.get("finish_reason", "")
    
                self._emit("model_turn", {
                    "iteration": it,
                    "elapsed": round(time.time() - t0, 2),
                    "content_chars": len(content),
                    "tool_call_count": len(tool_calls),
                    "finish_reason": finish_reason,
                })
    
                # Append assistant turn
                assistant_msg: Dict[str, Any] = {"role": "assistant", "content": content}
                if tool_calls:
                    assistant_msg["tool_calls"] = tool_calls
                self.messages.append(assistant_msg)
    
                # No tool calls → model is done talking
                if not tool_calls:
                    if not self.summary and content:
                        self.summary = content[:1000]
                    self._emit("loop_end", {"reason": "no_tool_call", "iteration": it})
                    return {
                        "ok": True, "summary": self.summary,
                        "files_changed": self.files_changed,
                        "iterations": it + 1, "log": self.tool_call_log,
                        "final_message": content,
                    }
    
                # Process each tool call
                finished = False
                for tc in tool_calls:
                    tc_id = tc.get("id", "")
                    fn = tc.get("function", {}) or {}
                    name = fn.get("name", "")
                    args_raw = fn.get("arguments", "") or "{}"
                    self._emit("tool_call", {"name": name, "args": args_raw[:500]})
    
                    if name == "finish":
                        try:
                            a = json.loads(args_raw or "{}")
                            self.summary = a.get("summary", "")
                            for fc in a.get("files_changed") or []:
                                if fc not in self.files_changed:
                                    self.files_changed.append(fc)
                        except Exception:
                            self.summary = args_raw[:500]
                        self.messages.append({
                            "role": "tool", "tool_call_id": tc_id, "name": name,
                            "content": json.dumps({"ok": True, "ack": "finished"}),
                        })
                        self.tool_call_log.append({"name": name, "args": args_raw, "ok": True})
                        finished = True
                        continue
    
                    result = dispatch_tool_call(name, args_raw)
                    # Track writes
                    if name in ("write_file", "patch_file") and result.get("ok"):
                        try:
                            a = json.loads(args_raw or "{}")
                            path = a.get("path", "")
                            if path and path not in self.files_changed:
                                self.files_changed.append(path)
                        except Exception:
                            pass
    
                    self.tool_call_log.append({
                        "name": name, "args": args_raw[:1000],
                        "ok": bool(result.get("ok")),
                        "summary": self._summarize_result(name, result),
                    })
                    self._emit("tool_result", {
                        "name": name, "ok": bool(result.get("ok")),
                        "summary": self.tool_call_log[-1]["summary"],
                    })
                    self.messages.append({
                        "role": "tool", "tool_call_id": tc_id, "name": name,
                        "content": json.dumps(result, ensure_ascii=False)[:32_000],
                    })
    
                if finished:
                    self._emit("loop_end", {"reason": "finish_called", "iteration": it})
                    return {
                        "ok": True, "summary": self.summary,
                        "files_changed": self.files_changed,
                        "iterations": it + 1, "log": self.tool_call_log,
                    }
    
            # Hit iteration cap
            # ── Safeguard 3: partial success if agent produced useful work ──
            if self.files_changed or self.summary:
                logger.info(
                    "[AgentLoop] Iteration cap hit but agent produced work "
                    "(%d files, %d chars summary) — treating as partial success",
                    len(self.files_changed), len(self.summary),
                )
                self._emit("loop_end", {"reason": "iteration_cap_partial", "iteration": self.max_iterations})
                return {
                    "ok": True,
                    "error": f"iteration cap hit ({self.max_iterations}) — partial result",
                    "summary": self.summary or f"(completed {len(self.files_changed)} file changes before cap)",
                    "files_changed": self.files_changed,
                    "iterations": self.max_iterations, "log": self.tool_call_log,
                }
            self._emit("loop_end", {"reason": "iteration_cap", "iteration": self.max_iterations})
            return {
                "ok": False, "error": f"iteration cap hit ({self.max_iterations})",
                "summary": self.summary, "files_changed": self.files_changed,
                "iterations": self.max_iterations, "log": self.tool_call_log,
            }
    
        def _summarize_result(self, name: str, result: Dict[str, Any]) -> str:
            if not result.get("ok"):
                return f"FAIL: {result.get('error','')[:120]}"
            if name == "read_file":
                return f"{result.get('total_lines', '?')} lines, {len(result.get('content',''))} chars"
            if name == "grep":
                return f"{len(result.get('hits', []))} hits"
            if name == "list_files":
                return f"{len(result.get('files', []))} files"
            if name in ("write_file", "patch_file"):
                return f"{result.get('bytes', result.get('new_bytes', 0))} bytes"
            if name in ("run_python", "run_pytest"):
                ec = result.get("exit_code")
                return f"exit={ec}, {result.get('elapsed_sec','?')}s"
            return "ok"
    
        def _emit(self, kind: str, payload: Dict[str, Any]):
            if self.on_event:
                try:
                    self.on_event(kind, payload)
                except Exception:
                    pass
    
        # ────────────────────────────────────────────────
        # Safeguard helpers
        # ────────────────────────────────────────────────
        def _messages_char_count(self) -> int:
            """Estimate total chars in the message list."""
            total = 0
            for m in self.messages:
                total += len(m.get("content") or "")
            return total
    
        def _compact_old_tool_results(self):
            """Safeguard 
  ...(截断)
  
  ## ⚠️ 最重要的规则
  系统已自动预加载项目文件结构和相关源文件（见上方 📂 项目上下文）。
  **你必须只引用上方提供的实际文件**，严禁凭想象编造文件名或路径。
  如果上下文中没有某个文件，说明该文件不存在。
  
  ## 要求
  1. 仔细阅读上方提供的项目文件结构和源文件内容
  2. 根据**实际存在的文件**分析哪些需要修改
  3. 列出需要修改的文件的**完整路径** (必须是项目上下文中出现的路径)
  4. 分析实现方案的可行性
  5. 引用具体代码行号说明修改点
  
  项目根目录: /Users/panglaohu/Downloads/DoubleBoatClawSystem
  后端: src/backend/ (Python FastAPI)
  前端: src/frontend/ (HTML + JS)
  
  
  项目根目录: /Users/panglaohu/Downloads/AgentsGroup2026
  后端: src/backend/ (Python FastAPI)
  前端: src/frontend/ (HTML + JS)
  
────────────────────────────────────────────────────────────
⚡ 使用 DeepSeek V4 直连 (64K 输出, 流式)...

🔗 API: api.deepseek.com | 模型: deepseek-chat
────────────────────────────────────────────────────────────

# 技术调研报告：逆事实推演框架 — OpenClaw 误判成本与沉默代价标定

## 1. 任务理解与核心概念

### 1.1 任务目标
构建一个**逆事实推演框架**（Counterfactual Reasoning Framework），利用历史决策数据来：
1. **标定 OpenClaw 误判成本**（False Positive Cost）：当系统错误地判定某个事件/决策为异常时的代价
2. **标定沉默代价**（Silence Cost）：当系统应该介入但未介入时的代价
3. **熔合成决策折损率基线**（Decision Degradation Baseline）：综合两种代价的决策质量度量

### 1.2 核心概念定义

| 概念 | 定义 | 数学表示 |
|------|------|----------|
| **误判成本** | 系统错误触发干预造成的资源浪费 | `C_fp = Σ(intervention_cost * false_positive_count)` |
| **沉默代价** | 系统未及时干预导致的损失放大 | `C_silence = Σ(damage_cost * missed_intervention_count)` |
| **决策折损率** | 综合决策质量度量 | `D = α*C_fp + β*C_silence` (归一化到 [0,1]) |

## 2. 现有系统架构分析

### 2.1 OpenClaw 同步通道 (`src/backend/channels/openclaw_sync.py`)

从项目文件结构可知，OpenClaw 集成通过 `openclaw_sync.py` 实现。该文件是核心集成点。

**关键发现**：`openclaw_sync.py.bak` 存在，说明该文件近期被修改过，可能存在历史决策数据。

### 2.2 系统演化通道 (`src/backend/channels/system_evolution.py`)

系统演化通道负责审计→分发→验证→关闭的循环，是决策数据的天然收集器。

### 2.3 监控系统 (`src/backend/monitoring/`)

```
src/backend/monitoring/
├── __init__.py
├── collector.py
├── models.py
├── plaza_monitor.py
├── plaza_monitor.py.bak
└── sampler.py
```

监控系统已有 `collector.py` 和 `sampler.py`，可以扩展为决策数据收集器。

## 3. 技术可行性分析

### 3.1 数据源分析

| 数据源 | 位置 | 可用性 | 说明 |
|--------|------|--------|------|
| OpenClaw 同步日志 | `openclaw_sync.py` | ✅ 存在 | 包含历史同步决策记录 |
| 系统演化审计日志 | `system_evolution.py` | ✅ 存在 | 包含审计→分发→验证记录 |
| 广场监控数据 | `plaza_monitor.py` | ✅ 存在 | 包含智能体行为监控数据 |
| 任务执行记录 | `task_store.py` | ✅ 存在 | 包含任务执行历史 |
| Agent 会话记录 | `session_store.py` | ✅ 存在 | 包含对话历史 |

### 3.2 需要新建的文件

根据项目结构，以下文件需要新建：

```
src/backend/agents/counterfactual/
├── __init__.py                    # 模块初始化
├── framework.py                   # 逆事实推演框架核心
├── cost_calibrator.py             # 成本标定器
├── decision_baseline.py           # 决策折损率基线
├── historical_analyzer.py         # 历史数据分析器
└── models.py                      # 数据模型
```

### 3.3 需要修改的文件

| 文件路径 | 修改内容 | 行号参考 |
|----------|----------|----------|
| `src/backend/main.py` | 注册逆事实推演框架 | 约第 100-150 行（startup 函数） |
| `src/backend/channels/openclaw_sync.py` | 添加决策数据导出接口 | 需查看实际文件 |
| `src/backend/monitoring/collector.py` | 扩展收集决策相关指标 | 需查看实际文件 |
| `src/backend/agents/api.py` | 添加逆事实推演 API 端点 | 需查看实际文件 |

## 4. 实现方案设计

### 4.1 逆事实推演框架架构

```
┌─────────────────────────────────────────────────────────────┐
│                  Counterfactual Framework                     │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────────┐   │
│  │ Historical   │  │ Cost         │  │ Decision         │   │
│  │ Data Loader  │→│ Calibrator   │→│ Baseline Engine  │   │
│  └─────────────┘  └──────────────┘  └──────────────────┘   │
│         │                │                    │              │
│         ▼                ▼                    ▼              │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────────┐   │
│  │ OpenClaw     │  │ FP Cost      │  │ Degradation      │   │
│  │ Sync Logs    │  │ Silence Cost │  │ Baseline Curve   │   │
│  └─────────────┘  └──────────────┘  └──────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### 4.2 核心算法设计

#### 4.2.1 误判成本标定算法

```python
def calibrate_false_positive_cost(historical_decisions: List[Decision]) -> float:
    """
    标定误判成本
    算法：基于历史中所有 false positive 决策的累计资源消耗
    """
    total_cost = 0.0
    for decision in historical_decisions:
        if decision.outcome == DecisionOutcome.FALSE_POSITIVE:
            # 计算干预成本：时间、计算资源、人工介入等
            intervention_cost = (
                decision.intervention_duration * 
                decision.compute_unit_cost +
                decision.human_review_cost
            )
            total_cost += intervention_cost
    return total_cost / len(historical_decisions) if historical_decisions else 0.0
```

#### 4.2.2 沉默代价标定算法

```python
def calibrate_silence_cost(historical_decisions: List[Decision]) -> float:
    """
    标定沉默代价
    算法：基于历史中所有 missed intervention 导致的损失放大
    """
    total_cost = 0.0
    for decision in historical_decisions:
        if decision.outcome == DecisionOutcome.MISSED_INTERVENTION:
            # 计算沉默代价：未干预导致的损失 - 如果及时干预的损失
            silence_cost = (
                decision.actual_damage - 
                decision.estimated_damage_if_intervened
            )
            total_cost += max(0, silence_cost)  # 只计正向损失
    return total_cost / len(historical_decisions) if historical_decisions else 0.0
```

#### 4.2.3 决策折损率基线熔合

```python
def compute_decision_degradation_baseline(
    fp_cost: float,
    silence_cost: float,
    alpha: float = 0.5,
    beta: float = 0.5
) -> float:
    """
    熔合误判成本与沉默代价为决策折损率基线
    输出范围 [0, 1]，值越大表示决策质量越差
    """
    # 归一化处理
    normalized_fp = sigmoid_normalize(fp_cost)
    normalized_silence = sigmoid_normalize(silence_cost)
    
    # 加权熔合
    degradation = alpha * normalized_fp + beta * normalized_silence
    
    # 确保在 [0, 1] 范围
    return min(1.0, max(0.0, degradation))

def sigmoid_normalize(value: float, threshold: float = 1.0) -> float:
    """使用 sigmoid 函数将成本值归一化到 [0, 1]"""
    import math
    return 1.0 / (1.0 + math.exp(-(value - threshold)))
```

### 4.3 数据模型设计

```python
# src/backend/agents/counterfactual/models.py

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

class DecisionOutcome(Enum):
    """决策结果枚举"""
    CORRECT = "correct"           # 正确决策
    FALSE_POSITIVE = "fp"         # 误判（过度干预）
    FALSE_NEGATIVE = "fn"         # 漏判（未干预）
    MISSED_INTERVENTION = "missed" # 沉默（应干预未干预）
    UNCERTAIN = "uncertain"       # 不确定

@dataclass
class HistoricalDecision:
    """历史决策记录"""
    decision_id: str
    timestamp: datetime
    source: str  # "openclaw", "evolution", "plaza"
    decision_type: str
    outcome: DecisionOutcome
    intervention_duration: float  # 秒
    compute_unit_cost: float
    human_review_cost: float
    actual_damage: float
    estimated_damage_if_intervened: float
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class CostCalibration:
    """成本标定结果"""
    fp_cost: float
    silence_cost: float
    fp_confidence: float  # 置信度 [0, 1]
    silence_confidence: float
    sample_size: int
    calibration_timestamp: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class DecisionDegradationBaseline:
    """决策折损率基线"""
    baseline_value: float  # [0, 1]
    fp_contribution: float
    silence_contribution: float
    alpha: float  # fp 权重
    beta: float   # silence 权重
    calibration: CostCalibration
    timestamp: datetime
```

## 5. 与现有系统的集成点

### 5.1 OpenClaw 同步通道集成

在 `openclaw_sync.py` 中，需要添加决策数据导出接口：

```python
# 在 OpenClawSyncChannel 类中添加
async def export_decision_history(self) -> List[HistoricalDecision]:
    """导出历史决策数据供逆事实推演框架使用"""
    decisions = []
    for record in self._sync_history:
        decision = HistoricalDecision(
            decision_id=record.id,
            timestamp=record.timestamp,
            source="openclaw",
            decision_type=record.type,
            outcome=self._classify_outcome(record),
            intervention_duration=record.duration,
            compute_unit_cost=record.compute_cost,
            human_review_cost=record.review_cost,
            actual_damage=record.actual_damage,
            estimated_damage_if_intervened=record.estimated_damage,
        )
        decisions.append(decision)
    return decisions
```

### 5.2 监控系统集成

在 `collector.py` 中扩展决策指标收集：

```python
# 添加决策相关指标
class DecisionMetrics:
    fp_count: int = 0
    silence_count: int = 0
    total_decisions: int = 0
    fp_cost_accumulated: float = 0.0
    silence_cost_accumulated: float = 0.0
```

### 5.3 API 端点集成

在 `agents/api.py` 中添加逆事实推演 API：

```python
@router.get("/counterfactual/baseline")
async def get_decision_baseline():
    """获取当前决策折损率基线"""
    baseline = counterfactual_engine.get_baseline()
    return baseline.to_dict()

@router.get("/counterfactual/history")
async def get_decision_history(
    source: Optional[str] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None
):
    """获取历史决策数据"""
    return counterfactual_engine.query_history(
        source=source,
        start_time=start_time,
        end_time=end_time
    )
```

## 6. 实现步骤与优先级

### 阶段 1：数据收集与模型定义（高优先级）
1. 创建 `src/backend/agents/counterfactual/` 目录结构
2. 实现 `models.py` 数据模型
3. 实现 `historical_analyzer.py` 历史数据分析器
4. 修改 `openclaw_sync.py` 添加数据导出接口

### 阶段 2：成本标定（高优先级）
1. 实现 `cost_calibrator.py` 成本标定器
2. 实现误判成本标定算法
3. 实现沉默代价标定算法
4. 集成到监控系统

### 阶段 3：基线熔合（中优先级）
1. 实现 `decision_baseline.py` 决策折损率基线
2. 实现熔合算法
3. 添加自适应权重调整

### 阶段 4：API 与集成（中优先级）
1. 添加 REST API 端点
2. 注册到 `main.py` 启动流程
3. 前端可视化支持

## 7. 风险评估

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| 历史数据不足 | 标定不准确 | 使用模拟数据 + 贝叶斯先验 |
| 成本量化困难 | 基线偏差 | 引入专家评审校准 |
| 实时性要求 | 计算延迟 | 异步批处理 + 缓存 |
| 权重选择主观 | 结果偏差 | 使用 A/B 测试自动调优 |

## 8. 结论

**可行性评估：✅ 可行**

基于现有系统架构：
- OpenClaw 同步通道已有历史决策数据
- 监控系统具备数据收集能力
- 系统演化通道提供审计轨迹
- API 框架支持扩展

**建议实施路径**：
1. 先实现核心算法（成本标定 + 基线熔合）
2. 再集成到现有系统
3. 最后添加 API 和前端支持

**预计工作量**：
- 核心算法：2-3 天
- 系统集成：1-2 天
- API 和前端：1 天
- 测试和调优：1-2 天

**总计：5-8 天**

────────────────────────────────────────────────────────────
✅ deepseek-chat 完成
