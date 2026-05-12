# 架构设计 — architect

任务: 构建逆事实推演框架，用历史决策数据标定 OpenClaw 误判成本与沉默代价，熔合成决策折损率基线
步骤: architecture
Agent: build_architect

---

📋 任务: e32cbf0e-868
🤖 Agent: Architect (architect)
📂 工作目录: /Users/panglaohu/Downloads/AgentsGroup2026
🔧 执行方式: DeepSeek API (直连)
⏱️ 超时: 1200s
────────────────────────────────────────────────────────────
📝 提示词:
  你是 AgentsGroup2026 系统的 Architect (architect)。
  请执行以下开发任务:
  
  你是系统架构师。请为以下任务设计技术方案:
  
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
  
  ### 步骤 01: pm_decompose
  任务: 构建逆事实推演框架，用历史决策数据标定 OpenClaw 误判成本与沉默代价，熔合成决策折损率基线
  步骤: pm_decompose
  📋 任务: e32cbf0e-868
  🤖 Agent: PM (project_manager)
  📂 工作目录: /Users/panglaohu/Downloads/AgentsGroup2026
  🔧 执行方式: DeepSeek API (直连)
  ────────────────────────────────────────────────────────────
  你是 AgentsGroup2026 系统的 PM (project_manager)。
  你是项目经理 (PM)。请对以下任务进行分解和规划:
  构建逆事实推演框架，用历史决策数据标定 OpenClaw 误判成本与沉默代价，熔合成决策折损率基线
  技术研究员 + Developer
  ## 📂 项目上下文 (系统自动预加载)
  ### 项目文件结构 (src/ 目录)
  ### 文件: `src/backend/main.py`
  ### 文件: `src/backend/agents/agent_loop.py`
  **变更文件 (2):**
    - `src/backend/agents/task_store.py`
    - `src/backend/channels/openclaw_sync.py`
  **子任务拆解:**
    - *项目名称:** AgentsGroup2026
    - *任务ID:** TASK-2026-OPENCLAW-COST-BASELINE
    - *负责人:** 技术研究员 + Developer
    - *状态:** 规划中
    - *核心概念定义:**
    - **逆事实推演 (Counterfactual Reasoning):** 一种分析方法，用于回答“如果当时做出了不同的决策，结果会怎样？”。在本任务中，我们将基于历史数据，模拟与OpenClaw实际决策相反的假设情景，以评估其决策的潜在影响。
    - **误判成本 (False Positive Cost):** OpenClaw执行了一个不必要的、错误的或有害的行动所带来的成本。例如，错误地触发了一个警报、错误地分配了资源、或错误地修改了系统配置。
    - **沉默代价 (Silence Cost):** OpenClaw在应该采取行动时却没有行动所带来的成本。例如，未能检测到关键事件、未能及时响应请求、或未能利用一个优化机会。
  
  ### 步骤 02: research (完整产出)
  
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
            """Safeguard 
  ...(截断)
  
  ## ⚠️ 重要提示
  上方 📂 项目上下文 包含了任务相关的实际源文件。
  请基于这些文件设计方案，不要引用不存在的文件。
  
  ## 要求
  1. 基于调研结果和实际源码，设计详细技术方案
  2. 明确指出需要修改的文件和具体修改内容
  3. 定义接口规范（如有新增 API）
  4. 为开发工程师提供逐步实施指南
  
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

# 逆事实推演框架 — 技术方案设计

## 1. 概述

本方案设计一个**逆事实推演框架 (Counterfactual Reasoning Framework)**，用于：
- 从历史决策数据中提取 OpenClaw 的**误判成本 (False Positive Cost)** 与**沉默代价 (Silence Cost)**
- 将两者熔合成**决策折损率基线 (Decision Degradation Baseline)**
- 为系统进化提���量化决策质量指标

## 2. 核心概念定义

### 2.1 误判成本 (False Positive Cost, FPC)
当 OpenClaw 执行了不必要的/错误的行动时产生的成本。

**计算公式：**
```
FPC = Σ(行动资源消耗 × 误判严重度 × 影响范围)
```

### 2.2 沉默代价 (Silence Cost, SC)
当 OpenClaw 应该行动但未行动时产生的成本。

**计算公式：**
```
SC = Σ(机会损失 + 风险累积 + 用户等待成本)
```

### 2.3 决策折损率 (Decision Degradation Rate, DDR)
```
DDR = α × FPC_normalized + β × SC_normalized
```
其中 α + β = 1，通过历史数据动态学习。

## 3. 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                  逆事实推演框架 (Counterfactual Engine)       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ 数据采集层    │  │ 推演分析层    │  │ 基线熔合层    │      │
│  │ (Collector)  │→│ (Analyzer)   │→│ (Fuser)      │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│         │                │                │                  │
│         ▼                ▼                ▼                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ 决策日志      │  │ 逆事实模拟器  │  │ 折损率基线    │      │
│  │ (TaskStore)  │  │ (Simulator)  │  │ (Baseline)   │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│                                                             │
└─────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│                  系统进化引擎 (System Evolution)              │
│  - 使用 DDR 基线评估进化提案                                 │
│  - 优先处理 DDR 高的决策领域                                 │
└─────────────────────────────────────────────────────────────┘
```

## 4. 数据模型设计

### 4.1 新增文件: `src/backend/agents/counterfactual/models.py`

```python
"""逆事实推演框架 — 数据模型"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional


class DecisionType(Enum):
    """决策类型"""
    ACTION = "action"          # 执行了行动
    SILENCE = "silence"        # 未行动（沉默）
    DELEGATION = "delegation"  # 委派给其他系统


class DecisionOutcome(Enum):
    """决策结果"""
    CORRECT = "correct"        # 正确
    FALSE_POSITIVE = "fp"      # 误判
    FALSE_NEGATIVE = "fn"      # 漏判（沉默代价）
    UNCERTAIN = "uncertain"    # 不确定


@dataclass
class DecisionRecord:
    """单条决策记录"""
    decision_id: str = ""
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    decision_type: DecisionType = DecisionType.ACTION
    outcome: DecisionOutcome = DecisionOutcome.CORRECT
    
    # 决策上下文
    agent_id: str = ""
    team_id: str = ""
    session_id: str = ""
    task_id: str = ""
    
    # 资源消耗
    resource_cost: float = 0.0       # 计算/API 资源消耗
    latency_ms: float = 0.0          # 响应延迟
    tokens_used: int = 0             # Token 消耗
    
    # 影响评估
    impact_scope: str = "local"      # local / team / system
    severity: float = 0.0            # 0.0 ~ 1.0
    user_facing: bool = False        # 是否影响用户
    
    # 逆事实标签（由分析器填充）
    counterfactual_label: str = ""   # "fp" / "fn" / "correct"
    counterfactual_confidence: float = 0.0  # 置信度
    
    # 元数据
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        if not self.decision_id:
            self.decision_id = str(uuid.uuid4())[:12]


@dataclass
class CostCalibration:
    """成本标定结果"""
    calibration_id: str = ""
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    # 误判成本参数
    fp_base_cost: float = 1.0        # 基础误判成本
    fp_severity_multiplier: float = 2.0  # 严重度乘数
    fp_resource_weight: float = 0.3  # 资源消耗权重
    
    # 沉默代价参数
    sc_base_cost: float = 1.5        # 基础沉默代价
    sc_opportunity_weight: float = 0.4  # 机会损失权重
    sc_risk_weight: float = 0.3      # 风险累积权重
    
    # 熔合参数
    alpha: float = 0.5               # FPC 权重
    beta: float = 0.5                # SC 权重
    
    # 统计信息
    total_decisions: int = 0
    fp_count: int = 0
    fn_count: int = 0
    avg_fp_cost: float = 0.0
    avg_sc_cost: float = 0.0
    
    # 基线
    baseline_ddr: float = 0.0        # 当前决策折损率基线
    
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DegradationBaseline:
    """决策折损率基线"""
    baseline_id: str = ""
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    # 整体基线
    overall_ddr: float = 0.0
    
    # 按维度分解
    by_agent: Dict[str, float] = field(default_factory=dict)
    by_team: Dict[str, float] = field(default_factory=dict)
    by_decision_type: Dict[str, float] = field(default_factory=dict)
    
    # 趋势
    trend_slope: float = 0.0         # 正数表示恶化
    trend_window: int = 100          # 分析窗口
    
    # 阈值
    warning_threshold: float = 0.7   # 警告阈值
    critical_threshold: float = 0.9  # 严重阈值
    
    metadata: Dict[str, Any] = field(default_factory=dict)
```

### 4.2 修改文件: `src/backend/agents/task_store.py`

**需要修改的内容：**
1. 在 `TaskRecord` 中添加决策成本字段
2. 添加决策记录查询接口

```python
# 在 TaskRecord 类中添加
@dataclass
class TaskRecord:
    # ... 现有字段 ...
    
    # 新增：决策成本相关
    decision_cost: Optional[float] = None       # 决策成本
    decision_outcome: Optional[str] = None      # "fp" / "fn" / "correct"
    decision_latency_ms: Optional[float] = None  # 决策延迟
    
    # 新增方法
    def get_decision_record(self) -> Optional[Dict[str, Any]]:
        """转换为决策记录"""
        if self.decision_cost is None:
            return None
        return {
            "task_id": self.task_id,
            "agent_id": self.agent_id,
            "team_id": self.team_id,
            "timestamp": self.created_at.isoformat(),
            "decision_type": "action" if self.decision_outcome else "silence",
            "outcome": self.decision_outcome or "uncertain",
            "resource_cost": self.decision_cost or 0.0,
            "latency_ms": self.decision_latency_ms or 0.0,
        }
```

## 5. 核心模块设计

### 5.1 数据采集器 (Collector)

**文件:** `src/backend/agents/counterfactual/collector.py`

```python
"""决策数据采集器"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from .models import DecisionRecord, DecisionType, DecisionOutcome

logger = logging.getLogger("counterfactual.collector")


class DecisionCollector:
    """采集 OpenClaw 决策数据"""
    
    def __init__(self, task_store=None, openclaw_sync=None):
        self.task_store = task_store
        self.openclaw_sync = openclaw_sync
        self._buffer: List[DecisionRecord] = []
        self._buffer_size = 1000
    
    async def collect_from_task_store(self, task_id: str) -> Optional[DecisionRecord]:
        """从任务存储采集决策数据"""
        if not self.task_store:
            return None
        
        task = await self.task_store.get_task(task_id)
        if not task:
            return None
        
        record = DecisionRecord(
            decision_id=f"dec_{task_id[:8]}",
            timestamp=task.created_at or datetime.now(timezone.utc),
            decision_type=DecisionType.ACTION if task.status == "completed" else DecisionType.SILENCE,
            outcome=self._classify_outcome(task),
            agent_id=task.agent_id,
            team_id=task.team_id,
            task_id=task.task_id,
            resource_cost=task.decision_cost or 0.0,
            latency_ms=task.decision_latency_ms or 0.0,
            impact_scope=self._estimate_impact(task),
            severity=self._estimate_severity(task),
            user_facing=task.metadata.get("source") == "bridge_chat",
        )
        
        self._buffer.append(record)
        if len(self._buffer) >= self._buffer_size:
            await self.flush()
        
        return record
    
    def _classify_outcome(self, task) -> DecisionOutcome:
        """分类决策结果"""
        # 基于任务状态和元数据分类
        if task.status == "failed":
            return DecisionOutcome.FALSE_POSITIVE
        elif task.status == "cancelled":
            return DecisionOutcome.FALSE_NEGATIVE
        elif task.status == "completed":
            return DecisionOutcome.CORRECT
        return DecisionOutcome.UNCERTAIN
    
    def _estimate_impact(self, task) -> str:
        """估计影响范围"""
        priority = task.priority or 0
        if priority >= 4:
            return "system"
        elif priority >= 2:
            return "team"
        return "local"
    
    def _estimate_severity(self, task) -> float:
        """估计严重度"""
        priority = task.priority or 0
        return min(priority / 5.0, 1.0)
    
    async def collect_from_openclaw(self, event: Dict[str, Any]) -> Optional[DecisionRecord]:
        """从 OpenClaw 同步事件采集"""
        if not self.openclaw_sync:
            return None
        
        # 解析 OpenClaw 事件
        record = DecisionRecord(
            timestamp=datetime.fromisoformat(event.get("timestamp", datetime.now(timezone.utc).isoformat())),
            decision_type=DecisionType(event.get("type", "action")),
            outcome=self._classify_openclaw_outcome(event),
            agent_id=event.get("agent_id", "openclaw"),
            team_id=event.get("team_id", "openclaw"),
            resource_cost=event.get("cost", 0.0),
            latency_ms=event.get("latency_ms", 0.0),
            impact_scope=event.get("impact", "local"),
            severity=event.get("severity", 0.0),
            metadata=event.get("metadata", {}),
        )
        
        self._buffer.append(record)
        return record
    
    def _classify_openclaw_outcome(self, event: Dict) -> DecisionOutcome:
        """分类 OpenClaw 事件结果"""
        status = event.get("status", "")
        if status == "false_positive":
            return DecisionOutcome.FALSE_POSITIVE
        elif status == "false_negative":
            return DecisionOutcome.FALSE_NEGATIVE
        elif status == "success":
            return DecisionOutcome.CORRECT
        return DecisionOutcome.UNCERTAIN
    
    async def flush(self):
        """刷新缓冲区到持久存储"""
        if not self._buffer:
            return
        
        # TODO: 持久化到数据库
        records = self._buffer.copy()
        self._buffer.clear()
        logger.info(f"Flushed {len(records)} decision records")
        return records
    
    async def get_recent_decisions(self, limit: int = 100) -> List[DecisionRecord]:
        """获取最近的决策记录"""
        # 合并缓冲区和持久化数据
        return self._buffer[-limit:] if self._buffer else []
```

### 5.2 逆事实分析器 (Analyzer)

**文件:** `src/backend/agents/counterfactual/analyzer.py`

```python
"""逆事实推演分析器"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Tuple

from .models import (
    DecisionRecord, DecisionOutcome, DecisionType,
    CostCalibration, DegradationBaseline,
)

logger = logging.getLogger("counterfactual.analyzer")


class CounterfactualAnalyzer:
    """执行逆事实推演分析"""
    
    def __init__(self, collector=None):
        self.collector = collector
        self._calibration: Optional[CostCalibration] = None
        self._baseline: Optional[DegradationBaseline] = None
    
    async def analyze_decisions(
        self, 
        decisions: List[DecisionRecord]
    ) -> CostCalibration:
        """分析决策记录，标定成本参数"""
        
        if not decisions:
            return self._calibration or CostCalibration()
        
        # 1. 分类决策
        fp_decisions = [d for d in decisions if d.outcome == DecisionOutcome.FALSE_POSITIVE]
        fn_decisions = [d for d in decisions if d.outcome == DecisionOutcome.FALSE_NEGATIVE]
        correct_decisions = [d for d in decisions if d.outcome == DecisionOutcome.CORRECT]
        
        # 2. 计算误判成本 (FPC)
        fp_costs = [self._calculate_fp_cost(d) for d in fp_decisions]
        avg_fp_cost = sum(fp_costs) / len(fp_costs) if fp_costs else 0.0
        
        # 3. 计算沉默代价 (SC)
        sc_costs = [self._calculate_sc_cost(d) for d in fn_decisions]
        avg_sc_cost = sum(sc_costs) / len(sc_costs) if sc_costs else 0.0
        
        # 4. 动态学习 α, β 权重
        alpha, beta = self._learn_weights(fp_decisions, fn_decisions, correct_decisions)
        
        # 5. 计算基线 DDR
        baseline_ddr = self._calculate_baseline_ddr(
            avg_fp_cost, avg_sc_cost, alpha, beta
        )
        
        # 6. 构建标定结果
        calibration = CostCalibration(
            total_decisions=len(decisions),
            fp_count=len(fp_decisions),
            fn_count=len(fn_decisions),
            avg_fp_cost=avg_fp_cost,
            avg_sc_cost=avg_sc_cost,
            alpha=alpha,
            beta=beta,
            baseline_ddr=baseline_ddr,
            metadata={
                "analysis_window": {
                    "start": min(d.timestamp for d in decisions).isoformat(),
                    "end": max(d.timestamp for d in decisions).isoformat(),
                },
                "correct_count": len(correct_decisions),
                "fp_rate": len(fp_decisions) / len(decisions) if decisions else 0,
                "fn_rate": len(fn_decisions) / len(decisions) if decisions else 0,
            },
        )
        
        self._calibration = calibration
        return calibration
    
    def _calculate_fp_cost(self, decision: DecisionRecord) -> float:
        """计算单条误判成本"""
        base = self._calibration.fp_base_cost if self._calibration else 1.0
        severity_mult = self._calibration.fp_severity_multiplier if self._calibration else 2.0
        resource_weight = self._calibration.fp_resource_weight if self._calibration else 0.3
        
        cost = (
            base +
            severity_mult * decision.severity +
            resource_weight * decision.resource_cost +
            0.1 * (decision.latency_ms / 1000)  # 延迟惩罚
        )
        
        # 影响范围乘数
        if decision.impact_scope == "system":
            cost *= 3.0
        elif decision.impact_scope == "team":
            cost *= 1.5
        
        return cost
    
    def _calculate_sc_cost(self, decision: DecisionRecord) -> float:
        """计算单条沉默代价"""
        base = self._calibration.sc_base_cost if self._calibration else 1.5
        opportunity_weight = self._calibration.sc_opportunity_weight if self._calibration else 0.4
        risk_weight = self._calibration.sc_risk_weight if self._calibration else 0.3
        
        # 机会损失：基于任务优先级
        opportunity_loss = decision.severity * 2.0
        
        # 风险累积：沉默时间越长风险越高
        risk_accumulation = risk_weight * (1.0 - decision.severity) * 0.5
        
        cost = (
            base +
            opportunity_weight * opportunity_loss +
            risk_accumulation +
            0.2 * (decision.latency_ms / 1000)  # 延迟惩罚
        )
        
        return cost
    
    def _learn_weights(
        self,
        fp_decisions: List[DecisionRecord],
        fn_decisions: List[DecisionRecord],
        correct_decisions: List[DecisionRecord],
    ) -> Tuple[float, float]:
        """动态学习 α 和 β 权重"""
        total = len(fp_decisions) + len(fn_decisions) + len(correct_decisions)
        if total == 0:
            return 0.5, 0.5
        
        # 基于错误率调整权重
        fp_rate = len(fp_decisions) / total
        fn_rate = len(fn_decisions) / total
        
        # 如果误判多，提高 α（更重视误判成本）
        # 如果沉默多，提高 β（更重视沉默代价）
        alpha = 0.5 + (fp_rate - fn_rate) * 0.3
        alpha = max(0.1, min(0.9, alpha))
        beta = 1.0 - alpha
        
        return alpha, beta
    
    def _calculate_baseline_ddr(
        self,
        avg_fp_cost: float,
        avg_sc_cost: float,
        alpha: float,
        beta: float,
    ) -> float:
        """计算决策折损率基线"""
        # 归一化到 0~1 范围
        normalized_fp = min(avg_fp_cost / 10.0, 1.0)
        normalized_sc = min(avg_sc_cost / 10.0, 1.0)
        
        ddr = alpha * normalized_fp + beta * normalized_sc
        return min(ddr, 1.0)
    
    async def build_baseline(
        self,
        decisions: List[DecisionRecord],
        calibration: CostCalibration,
    ) -> DegradationBaseline:
        """构建决策折损率基线"""
        
        # 按 Agent 分解
        by_agent = {}
        for d in decisions:
            agent_id = d.agent_id
            if agent_id not in by_agent:
                by_agent[agent_id] = []
            by_agent[agent_id].append(d)
        
        agent_ddr = {}
        for agent_id, agent_decisions in by_agent.items():
            fp_costs = [self._calculate_fp_cost(d) for d in agent_decisions 
                       if d.outcome == DecisionOutcome.FALSE_POSITIVE]
            sc_costs = [self._calculate_sc_cost(d) for d in agent_decisions 
                       if d.outcome == DecisionOutcome.FALSE_NEGATIVE]
            
            avg_fp = sum(fp_costs) / len(fp_costs) if fp_costs else 0
            avg_sc = sum(sc_costs) / len(sc_costs) if sc_costs else 0
            
            agent_ddr[agent_id] = self._calculate_baseline_ddr(
                avg_fp, avg_sc, calibration.alpha, calibration.beta
            )
        
        # 按决策类型分解
        type_ddr = {}
        for dtype in DecisionType:
            type_decisions = [d for d in decisions if d.decision_type == dtype]
            if type_decisions:
                fp_costs = [self._calculate_fp_cost(d) for d in type_decisions 
                           if d.outcome == DecisionOutcome.FALSE_POSITIVE]
                sc_costs = [self._calculate_sc_cost(d) for d in type_decisions 
                           if d.outcome == DecisionOutcome.FALSE_NEGATIVE]
                
                avg_fp = sum(fp_costs) / len(fp_costs) if fp_costs else 0
                avg_sc = sum(sc_costs) / len(sc_costs) if sc_costs else 0
                
                type_ddr[dtype.value] = self._calculate_baseline_ddr(
                    avg_fp, avg_sc, calibration.alpha, calibration.beta
                )
        
        # 计算趋势
        trend_slope = self._calculate_trend(decisions)
        
        baseline = DegradationBaseline(
            overall_ddr=calibration.baseline_ddr,
            by_agent=agent_ddr,
            by_team={},  # TODO: 按团队分解
            by_decision_type=type_ddr,
            trend_slope=trend_slope,
            trend_window=len(decisions),
            metadata={
                "calibration_id": calibration.calibration_id,
                "analysis_timestamp": calibration.timestamp.isoformat(),
            },
        )
        
        self._baseline = baseline
        return baseline
    
    def _calculate_trend(self, decisions: List[DecisionRecord]) -> float:
        """计算 DDR 趋势斜率"""
        if len(decisions) < 10:
            return 0.0
        
        # 简单线性回归
        sorted_decisions = sorted(decisions, key=lambda d: d.timestamp)
        n = len(sorted_decisions)
        
        # 分成前后两半比较
        half = n // 2
        first_half = sorted_decisions[:half]
        second_half = sorted_decisions[half:]
        
        first_ddr = self._calculate_baseline_ddr(
            sum(self._calculate_fp_cost(d) for d in first_half if d.outcome == DecisionOutcome.FALSE_POSITIVE) / max(len([d for d in first_half if d.outcome == DecisionOutcome.FALSE_POSITIVE]), 1),
            sum(self._calculate_sc_cost(d) for d in first_half if d.outcome == DecisionOutcome.FALSE_NEGATIVE) / max(len([d for d in first_half if d.outcome == DecisionOutcome.FALSE_NEGATIVE]), 1),
            0.5, 0.5
        )
        
        second_ddr = self._calculate_baseline_ddr(
            sum(self._calculate_fp_cost(d) for d in second_half if d.outcome == DecisionOutcome.FALSE_POSITIVE) / max(len([d for d in second_half if d.outcome == DecisionOutcome.FALSE_POSITIVE]), 1),
            sum(self._calculate_sc_cost(d) for d in second_half if d.outcome == DecisionOutcome.FALSE_NEGATIVE) / max(len([d for d in second_half if d.outcome == DecisionOutcome.FALSE_NEGATIVE]), 1),
            0.5, 0.5
        )
        
        return second_ddr - first_ddr
    
    def get_calibration(self) -> Optional[CostCalibration]:
        """获取当前标定结果"""
        return self._calibration
    
    def get_baseline(self) -> Optional[DegradationBaseline]:
        """获取当前基线"""
        return self._baseline
```

### 5.3 基线熔合器 (Fuser)

**文件:** `src/backend/agents/counterfactual/fuser.py`

```python
"""决策折损率基线熔合器"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from .models import CostCalibration, DegradationBaseline

logger = logging.getLogger("counterfactual.fuser")


class BaselineFuser:
    """熔合误判成本与沉默代价为决策折损率基线"""
    
    def __init__(self, analyzer=None):
        self.analyzer = analyzer
        self._history: List[DegradationBaseline] = []
        self._max_history = 100
    
    async def fuse(
        self,
        calibration: CostCalibration,
        baseline: DegradationBaseline,
    ) -> DegradationBaseline:
        """熔合标定结果与基线"""
        
        # 1. 平滑处理：与历史基线加权平均
        if self._history:
            last_baseline = self._history[-1]
            smoothed_ddr = 0.7 * baseline.overall_ddr + 0.3 * last_baseline.overall_ddr
            baseline.overall_ddr = smoothed_ddr
            
            # 平滑各维度
            for agent_id in baseline.by_agent:
                if agent_id in last_baseline.by_agent:
                    baseline.by_agent[agent_id] = (
                        0.7 * baseline.by_agent[agent_id] + 
                        0.3 * last_baseline.by_agent[agent_id]
                    )
        
        # 2. 记录历史
        self._history.append(baseline)
        if len(self._history) > self._max_history:
            self._history = self._history[-self._max_history:]
        
        # 3. 生成熔合报告
        report = self._generate_fusion_report(calibration, baseline)
        baseline.metadata["fusion_report"] = report
        
        logger.info(
            f"Baseline fused: DDR={baseline.overall_ddr:.3f}, "
            f"α={calibration.alpha:.2f}, β={calibration.beta:.2f}"
        )
        
        return baseline
    
    def _generate_fusion_report(
        self,
        calibration: CostCalibration,
        baseline: DegradationBaseline,
    ) -> Dict[str, Any]:
        """生成熔合报告"""
        return {
            "fusion_timestamp": baseline.timestamp.isoformat(),
            "calibration": {
                "total_decisions": calibration.total_decisions,
                "fp_count": calibration.fp_count,
                "fn_count": calibration.fn_count,
                "avg_fp_cost": round(calibration.avg_fp_cost, 3),
                "avg_sc_cost": round(calibration.avg_sc_cost, 3),
                "alpha": round(calibration.alpha, 3),
                "beta": round(calibration.beta, 3),
            },
            "baseline": {
                "overall_ddr": round(baseline.overall_ddr, 3),
                "trend": "improving" if baseline.trend_slope < -0.05 
                        else "degrading" if baseline.trend_slope > 0.05 
                        else "stable",
                "trend_slope": round(baseline.trend_slope, 4),
                "status": "critical" if baseline.overall_ddr >= baseline.critical_threshold
                         else "warning" if baseline.overall_ddr >= baseline.warning_threshold
                         else "normal",
            },
            "recommendations": self._generate_recommendations(baseline),
        }
    
    def _generate_recommendations(
        self, baseline: DegradationBaseline
    ) -> List[str]:
        """生成改进建议"""
        recommendations = []
        
        if baseline.overall_ddr >= baseline.critical_threshold:
            recommendations.append("⚠️ 决策折损率严重超标，建议立即审查决策流程")
        
        if baseline.overall_ddr >= baseline.warning_threshold:
            recommendations.append("⚠️ 决策折损率超过警告阈值，建议优化高 DDR 的 Agent")
        
        # 按 Agent 给出建议
        for agent_id, ddr in baseline.by_agent.items():
            if ddr >= 0.8:
                recommendations.append(f"Agent '{agent_id}' DDR={ddr:.2f}，建议重新配置或暂停")
            elif ddr >= 0.5:
                recommendations.append(f"Agent '{agent_id}' DDR={ddr:.2f}，建议优化决策逻辑")
        
        # 趋势建议
        if baseline.trend_slope > 0.1:
            recommendations.append("📈 DDR 呈上升趋势，建议分析近期变更")
        elif baseline.trend_slope < -0.1:
            recommendations.append("📉 DDR 呈下降趋势，当前优化措施有效")
        
        return recommendations
    
    def get_history(self) -> List[DegradationBaseline]:
        """获取历史基线"""
        return self._history.copy()
```

### 5.4 主引擎 (Engine)

**文件:** `src/backend/agents/counterfactual/engine.py`

```python
"""逆事实推演引擎 — 统一入口"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from .collector import DecisionCollector
from .analyzer import CounterfactualAnalyzer
from .fuser import BaselineFuser
from .models import (
    DecisionRecord, CostCalibration, DegradationBaseline,
    DecisionOutcome,
)

logger = logging.getLogger("counterfactual.engine")


class CounterfactualEngine:
    """逆事实推演引擎"""
    
    def __init__(
        self,
        task_store=None,
        openclaw_sync=None,
        evolution_engine=None,
    ):
        self.collector = DecisionCollector(
            task_store=task_store,
            openclaw_sync=openclaw_sync,
        )
        self.analyzer = CounterfactualAnalyzer(collector=self.collector)
        self.fuser = BaselineFuser(analyzer=self.analyzer)
        self.evolution_engine = evolution_engine
        
        self._running = False
        self._analysis_interval = 300  # 5分钟
        self._task: Optional[asyncio.Task] = None
    
    async def start(self):
        """启动引擎"""
        if self._running:
            return
        
        self._running = True
        self._task = asyncio.create_task(self._run_loop())
        logger.info("CounterfactualEngine started")
    
    async def stop(self):
        """停止引擎"""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("CounterfactualEngine stopped")
    
    async def _run_loop(self):
        """主循环"""
        while self._running:
            try:
                await self._analyze_cycle()
            except Exception as e:
                logger.error(f"Analysis cycle failed: {e}")
            
            await asyncio.sleep(self._analysis_interval)
    
    async def _analyze_cycle(self):
        """执行一次分析周期"""
        # 1. 采集数据
        decisions = await self.collector.get_recent_decisions(limit=500)
        if not decisions:
            logger.debug("No decisions to analyze")
            return
        
        # 2. 分析标定
        calibration = await self.analyzer.analyze_decisions(decisions)
        
        # 3. 构建基线
        baseline = await self.analyzer.build_baseline(decisions, calibration)
        
        # 4. 熔合基线
        fused_baseline = await self.fuser.fuse(calibration, baseline)
        
        # 5. 通知进化引擎
        if self.evolution_engine and fused_baseline.overall_ddr >= 0.7:
            await self._notify_evolution(fused_baseline)
        
        logger.info(
            f"Analysis cycle complete: "
            f"{len(decisions)} decisions, "
            f"DDR={fused_baseline.overall_ddr:.3f}"
        )
    
    async def _notify_evolution(self, baseline: DegradationBaseline):
        """通知进化引擎"""
        if not self.evolution_engine:
            return
        
        try:
            # 创建进化提案
            proposal = {
                "type": "counterfactual_baseline_update",
                "priority": "high" if baseline.overall_ddr >= 0.9 else "normal",
                "data": {
                    "baseline_id": baseline.baseline_id,
                    "overall_ddr": baseline.overall_ddr,
                    "high_risk_agents": [
                        agent_id for agent_id, ddr in baseline.by_agent.items()
                        if ddr >= 0.7
                    ],
                    "recommendations": baseline.metadata.get("fusion_report", {}).get("recommendations", []),
                },
            }
            
            await self.evolution_engine.submit_proposal(proposal)
            logger.info(f"Evolution proposal submitted: DDR={baseline.overall_ddr:.3f}")
            
        except Exception as e:
            logger.error(f"Failed to notify evolution: {e}")
    
    async def record_decision(
        self,
        agent_id: str,
        team_id: str,
        outcome: str,
        cost: float = 0.0,
        latency_ms: float = 0.0,
        severity: float = 0.0,
        metadata: Optional[Dict] = None,
    ) -> DecisionRecord:
        """记录一条决策（供外部调用）"""
        record = DecisionRecord(
            agent_id=agent_id,
            team_id=team_id,
            outcome=DecisionOutcome(outcome),
            resource_cost=cost,
            latency_ms=latency_ms,
            severity=severity,
            metadata=metadata or {},
        )
        
        self.collector._buffer.append(record)
        return record
    
    async def get_current_baseline(self) -> Optional[DegradationBaseline]:
        """获取当前基线"""
        return self.fuser.get_history()[-1] if self.fuser.get_history() else None
    
    async def get_calibration(self) -> Optional[CostCalibration]:
        """获取当前标定"""
        return self.analyzer.get_calibration()
```

## 6. API 接口设计

### 6.1 新增文件: `src/backend/agents/counterfactual/routes.py`

```python
"""逆事实推演 API 路由"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from .engine import CounterfactualEngine
from .models import DecisionRecord, CostCalibration, DegradationBaseline

logger = logging.getLogger("counterfactual.routes")

router = APIRouter(prefix="/api/v1/counterfactual", tags=["counterfactual"])

# 全局引擎实例
_engine: Optional[CounterfactualEngine] = None


def set_engine(engine: CounterfactualEngine):
    global _engine
    _engine = engine


# ── 请求/响应模型 ──

class RecordDecisionRequest(BaseModel):
    agent_id: str
    team_id: str = "default"
    outcome: str  # "correct" / "fp" / "fn" / "uncertain"
    cost: float = 0.0
    latency_ms: float = 0.0
    severity: float = 0.0
    metadata: Dict[str, Any] = {}


class BaselineResponse(BaseModel):
    baseline_id: str
    overall_ddr: float
    by_agent: Dict[str, float]
    by_decision_type: Dict[str, float]
    trend_slope: float
    status: str
    recommendations: List[str]


class CalibrationResponse(BaseModel):
    total_decisions: int
    fp_count: int
    fn_count: int
    avg_fp_cost: float
    avg_sc_cost: float
    alpha: float
    beta: float
    baseline_ddr: float


# ── 端点 ──

@router.post("/record", summary="记录一条决策")
async def record_decision(req: RecordDecisionRequest):
    """记录一条决策数据用于分析"""
    if not _engine:
        raise HTTPException(status_code=503, detail="Counterfactual engine not initialized")
    
    record = await _engine.record_decision(
        agent_id=req.agent_id,
        team_id=req.team_id,
        outcome=req.outcome,
        cost=req.cost,
        latency_ms=req.latency_ms,
        severity=req.severity,
        metadata=req.metadata,
    )
    
    return {
        "ok": True,
        "decision_id": record.decision_id,
        "timestamp": record.timestamp.isoformat(),
    }


@router.get("/baseline", summary="获取当前决策折损率基线")
async def get_baseline():
    """获取当前熔合后的决策折损率基线"""
    if not _engine:
        raise HTTPException(status_code=503, detail="Counterfactual engine not initialized")
    
    baseline = await _engine.get_current_baseline()
    if not baseline:
        return {
            "ok": True,
            "baseline": None,
            "message": "No baseline available yet. Collect more decisions.",
        }
    
    report = baseline.metadata.get("fusion_report", {})
    
    return {
        "ok": True,
        "baseline": BaselineResponse(
            baseline_id=baseline.baseline_id,
            overall_ddr=baseline.overall_ddr,
            by_agent=baseline.by_agent,
            by_decision_type=baseline.by_decision_type,
            trend_slope=baseline.trend_slope,
            status=report.get("baseline", {}).get("status", "unknown"),
            recommendations=report.get("recommendations", []),
        ),
    }


@router.get("/calibration", summary="获取当前成本标定")
async def get_calibration():
    """获取当前误判成本与沉默代价标定"""
    if not _engine:
        raise HTTPException(status_code=503, detail="Counterfactual engine not initialized")
    
    calibration = await _engine.get_calibration()
    if not calibration:
        return {
            "ok": True,
            "calibration": None,
            "message": "No calibration available yet.",
        }
    
    return {
        "ok": True,
        "calibration": CalibrationResponse(
            total_decisions=calibration.total_decisions,
            fp_count=calibration.fp_count,
            fn_count=calibration.fn_count,
            avg_fp_cost=calibration.avg_fp_cost,
            avg_sc_cost=calibration.avg_sc_cost,
            alpha=calibration.alpha,
            beta=calibration.beta,
            baseline_ddr=calibration.baseline_ddr,
        ),
    }


@router.post("/analyze", summary="手动触发一次分析")
async def trigger_analysis():
    """手动触发一次完整的逆事实推演分析"""
    if not _engine:
        raise HTTPException(status_code=503, detail="Counterfactual engine not initialized")
    
    try:
        await _engine._analyze_cycle()
        baseline = await _engine.get_current_baseline()
        
        return {
            "ok": True,
            "message": "Analysis complete",
            "baseline_ddr": baseline.overall_ddr if baseline else None,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history", summary="获取基线历史")
async def get_history(limit: int = Query(10, ge=1, le=100)):
    """获取历史基线记录"""
    if not _engine:
        raise HTTPException(status_code=503, detail="Counterfactual engine not initialized")
    
    history = _engine.fuser.get_history()
    return {
        "ok": True,
        "history": [
            {
                "timestamp": b.timestamp.isoformat(),
                "overall_ddr": b.overall_ddr,
                "trend_slope": b.trend_slope,
            }
            for b in history[-limit:]
        ],
    }
```

### 6.2 修改文件: `src/backend/main.py`

在 `startup()` 函数中添加逆事实推演引擎初始化：

```python
# 在 startup() 函数中添加

# 7. 逆事实推演引擎
try:
    from agents.counterfactual.engine import CounterfactualEngine
    from agents.counterfactual.routes import router as cf_router, set_engine
    
    # 获取进化引擎
    from channels.marine_base import get_default_registry
    registry = get_default_registry()
    evo_engine = registry.get("system_evolution")
    
    # 初始化引擎
    cf_engine = CounterfactualEngine(
        task_store=_team_manager.task_store if hasattr(_team_manager, 'task_store') else None,
        openclaw_sync=registry.get("openclaw_sync"),
        evolution_engine=evo_engine,
    )
    
    # 注入到路由
    set_engine(cf_engine)
    
    # 启动引擎
    import asyncio
    asyncio.create_task(cf_engine.start())
    
    # 挂载路由
    app.include_router(cf_router)
    
    logger.info("✅ Counterfactual Engine initialized & API mounted (/api/v1/counterfactual)")
except Exception as e:
    logger.warning(f"⚠️ Counterfactual Engine failed: {e}")
```

## 7. 与 OpenClaw 集成

### 7.1 修改文件: `src/backend/channels/openclaw_sync.py`

在 `OpenClawSyncChannel` 中添加决策记录功能：

```python
# 在 OpenClawSyncChannel 类中添加

class OpenClawSyncChannel:
    # ... 现有代码 ...
    
    def __init__(self, counterfactual_engine=None):
        # ... 现有初始化 ...
        self.counterfactual_engine = counterfactual_engine
    
    async def on_decision_event(self, event: Dict[str, Any]):
        """处理 OpenClaw 决策事件"""
        # ... 现有处理逻辑 ...
        
        # 记录到逆事实推演引擎
        if self.counterfactual_engine:
            await self.counterfactual_engine.record_decision(
                agent_id=event.get("agent_id", "openclaw"),
                team_id="openclaw",
                outcome=event.get("outcome", "uncertain"),
                cost=event.get("cost", 0.0),
                latency_ms=event.get("latency_ms", 0.0),
                severity=event.get("severity", 0.0),
                metadata=event.get("metadata", {}),
            )
```

## 8. 实施步骤

### 步骤 1: 创建目录结构
```bash
mkdir -p src/backend/agents/counterfactual
touch src/backend/agents/counterfactual/__init__.py
```

### 步骤 2: 创建数据模型
- 创建 `src/backend/agents/counterfactual/models.py`
- 包含所有数据模型定义

### 步骤 3: 创建采集器
- 创建 `src/backend/agents/counterfactual/collector.py`
- 实现 `DecisionCollector` 类

### 步骤 4: 创建分析器
- 创建 `src/backend/agents/counterfactual/analyzer.py`
- 实现 `CounterfactualAnalyzer` 类

### 步骤 5: 创建熔合器
- 创建 `src/backend/agents/counterfactual/fuser.py`
- 实现 `BaselineFuser` 类

### 步骤 6: 创建引擎
- 创建 `src/backend/agents/counterfactual/engine.py`
- 实现 `CounterfactualEngine` 类

### 步骤 7: 创建 API 路由
- 创建 `src/backend/agents/counterfactual/routes.py`
- 实现所有 API 端点

### 步骤 8: 集成到主应用
- 修改 `src/backend/main.py` 添加引擎初始化
- 修改 `src/backend/channels/openclaw_sync.py` 添加决策记录

### 步骤 9: 修改 TaskStore
- 修改 `src/backend/agents/task_store.py` 添加决策成本字段

### 步骤 10: 测试
```bash
# 启动服务
cd src/backend && python main.py --port 8080

# 测试 API
curl http://localhost:8080/api/v1/counterfactual/baseline
curl http://localhost:8080/api/v1/counterfactual/calibration

# 记录测试决策
curl -X POST http://localhost:8080/api/v1/counterfactual/record \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "test_agent",
    "outcome": "fp",
    "cost": 2.5,
    "latency_ms": 1500,
    "severity": 0.7
  }'

# 触发分析
curl -X POST http://localhost:8080/api/v1/counterfactual/analyze
```

## 9. 预期输出

### 9.1 决策折损率基线示例
```json
{
  "baseline": {
    "baseline_id": "bl_abc123",
    "overall_ddr": 0.423,
    "by_agent": {
      "build_pm": 0.35,
      "build_developer": 0.52,
      "build_qa": 0.28,
      "openclaw_sync": 0.61
    },
    "by_decision_type": {
      "action": 0.38,
      "silence": 0.55,
      "delegation": 0.31
    },
    "trend_slope": -0.023,
    "status": "normal",
    "recommendations": [
      "Agent 'openclaw_sync' DDR=0.61，建议优化同步决策逻辑",
      "Agent 'build_developer' DDR=0.52，建议审查代码生成质量"
    ]
  }
}
```

### 9.2 成本标定示例
```json
{
  "calibration": {
    "total_decisions": 1250,
    "fp_count": 87,
    "fn_count": 43,
    "avg_fp_cost": 3.42,
    "avg_sc_cost": 4.15,
    "alpha": 0.47,
    "beta": 0.53,
    "baseline_ddr": 0.423
  }
}
```

## 10. 后续优化方向

1. **实时监控 Dashboard**：在 `src/frontend/` 中添加 DDR 可视化面板
2. **自动阈值调整**：基于历史数据动态调整 warning/critical 阈值
3. **多维度分析**：按时间段、任务类型、用户群体等维度分解 DDR
4. **预测模型**：使用时间序列预测 DDR 趋势
5. **自动优化**：当 DDR 超过阈值时，自动触发 Agent 配置优化

────────────────────────────────────────────────────────────
✅ deepseek-chat 完成
