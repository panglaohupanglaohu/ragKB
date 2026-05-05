# 架构设计 — architect

任务: 创建 greeting 工具函数
步骤: architecture
Agent: build_architect

---

📋 任务: d87c964b-c06
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
  创建 greeting 工具函数
  在 src/backend/agents/skills/ 下创建 greeting.py，包含 greet(name) 返回 Hello name。同时创建 tests/test_greeting.py 测试。
  
  ## 📂 项目上下文 (系统自动预加载)
  
  ### 项目文件结构 (src/ 目录)
  ```
  src/frontend/agent-team-config.html
  src/frontend/datacenter-ratchet-evolution.html
  src/frontend/index.html
  src/frontend/login.html
  src/frontend/plaza-old.html
  src/frontend/plaza.html
  src/frontend/system-evolution.html
  src/frontend/css/agent-team-config.css
  src/frontend/css/openbridge-theme.css
  src/frontend/css/ws-theme-bridge.css
  src/frontend/js/agent-team-config.js
  src/frontend/js/i18n.js
  src/frontend/js/nav-sidebar.js
  src/backend/__init__.py
  src/backend/agent_team_api.py
  src/backend/main.py
  src/backend/agents/__init__.py
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
  src/backend/agents/session_store.py
  src/backend/agents/skill_registry.py
  src/backend/agents/task_engine.py
  src/backend/agents/team_manager.py
  src/backend/agents/tool_executor.py
  src/backend/agents/tool_registry.py
  src/backend/agents/teams/__init__.py
  src/backend/agents/teams/ai_coding_team.py
  src/backend/agents/teams/build_team.py
  src/backend/agents/teams/energy_team.py
  src/backend/agents/skills/__init__.py
  src/backend/agents/skills/hello.py
  src/backend/channels/__init__.py
  src/backend/channels/bridge_chat.py
  src/backend/channels/marine_base.py
  src/backend/channels/system_evolution.py
  src/docs/agent_handoffs/38e22004-b64_architecture_20260503T045011.md
  src/docs/agent_handoffs/38e22004-b64_pm_decompose_20260503T044921.md
  src/docs/agent_handoffs/38e22004-b64_research_20260503T044941.md
  src/docs/agent_handoffs/38e22004-b64_task_init_20260503T044856.md
  src/docs/workflow_artifacts/38e22004-b64_architecture.md
  src/docs/workflow_artifacts/38e22004-b64_pm_decompose.md
  src/docs/workflow_artifacts/38e22004-b64_research.md
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
  
              app.include_router(plaza_router, prefix="/api/v1/agent-config")
              logger.info("✅ 智能体广场 API mounted (/api/v1/agent-config/plaza)")
          except Exception as e:
              logger.warning(f"⚠️ Plaza API failed: {e}")
      except Exception as e:
          logger.warning(f"⚠️ Agent Config API failed: {e}")
  
      logger.info("🎉 AgentsGroup2026 ready")
  
  
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
          raise HTTPException(status_code=404, detail="Chat channe
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
  
  ### 文件: `src/backend/agents/hermes_research.py`
  ```py
  # -*- coding: utf-8 -*-
  """AgentsGroup2026 — Hermes-style Research Agent Module.
  
  Transforms the Research Agent from a read-only advisory role into a
  self-improving research agent inspired by NousResearch/hermes-agent:
  
  Architecture mapping (Hermes → AgentsGroup2026):
    - AIAgent class         → HermesResearchAgent
    - run_conversation()    → agent_loop()
    - toolsets.py           → RESEARCH_TOOLSET_DISTRIBUTIONS
    - prompt_builder.py     → build_research_system_prompt()
    - SOUL.md               → agent.hermes_config.soul_md
    - Memory/Skills nudge   → MEMORY_GUIDANCE / SKILLS_GUIDANCE
    - Delegate subagents    → delegate_task()
    - Session search        → session_search()
  
  Key Hermes characteristics adopted:
    1. Closed learning loop — auto-create skills from complex research
    2. Persistent memory — save research findings across sessions
    3. Probabilistic toolset distribution — web 90%, browser 70%, vision 50%
    4. SOUL.md — research persona
    5. Context files — AGENTS.md project context
    6. Tool-use enforcement — tools must be used, not just described
    7. Session search — cross-session recall of past research
  """
  
  from __future__ import annotations
  
  import random
  from dataclasses import dataclass, field
  from typing import Any, Dict, List, Optional
  
  from .models import (
      AgentProfile,
      AgentTemplateType,
      AgentPersonality,
      HermesAgentConfig,
      ToolsetDistribution,
  )
  
  
  # ══════════════════════════════════════════════════════════════
  # Hermes-style Toolset Distributions
  # Inspired by NousResearch/hermes-agent/toolset_distributions.py
  # ══════════════════════════════════════════════════════════════
  
  RESEARCH_TOOLSET_DISTRIBUTIONS: Dict[str, Dict[str, Any]] = {
      "general_research": {
          "description": "General domain research — literature review, data analysis, technical investigation",
          "toolsets": {
              "web": 90,
              "browser": 70,
              "vision": 50,
              "file": 80,
              "research": 95,
              "memory": 100,
              "skills": 100,
              "delegation": 30,
          },
      },
      "deep_analysis": {
          "description": "Deep analysis — systematic review, data verification, cross-referencing",
          "toolsets": {
              "web": 60,
              "file": 95,
              "research": 100,
              "code_execution": 80,
              "memory": 100,
              "vision": 40,
          },
      },
      "compliance_audit": {
          "description": "Standards and compliance verification",
          "toolsets": {
              "web": 85,
              "browser": 65,
              "file": 90,
              "research": 100,
              "code_execution": 70,
              "memory": 100,
          },
      },
      "technical_review": {
          "description": "Technical design review, architecture analysis, code review",
          "toolsets": {
              "web": 50,
              "file": 95,
              "code_execution": 90,
              "research": 100,
              "vision": 70,
              "memory": 100,
          },
      },
      "general_research": {
          "description": "General web research with all tools available",
          "toolsets": {
              "web": 90,
              "browser": 70,
              "vision": 50,
              "memory": 100,
              "skills": 100,
              "file": 60,
              "code_execution": 30,
          },
      },
  }
  
  # ══════════════════════════════════════════════════════════════
  # Hermes-style Toolset Definitions
  # Inspired by NousResearch/hermes-agent/toolsets.py
  # ══════════════════════════════════════════════════════════════
  
  HERMES_TOOLSETS: Dict[str, Dict[str, Any]] = {
      "web": {
          "description": "Web research and content extraction",
          "tools": ["web_search", "extract_content"],
      },
      "browser": {
          "description": "Browser automation for deep research",
          "tools": ["navigate_url", "screenshot", "click_element", "fill_form", "extract_content", "web_search"],
      },
      "file": {
          "description": "File read/write/search operations",
          "tools": ["read_file", "write_file", "list_directory", "search_files"],
      },
      "code_execution": {
          "description": "Run Python/shell for analysis and calculation",
          "tools": ["run_python", "run_shell"],
      },
      "vision": {
          "description": "Image/chart analysis for technical documents",
          "tools": ["screenshot"],
      },
      "research": {
          "description": "Research-specific tools — search, analysis, data retrieval",
          "tools": ["search_query", "data_lookup", "info_fetch", "analysis_engine"],
      },
      "memory": {
          "description": "Persistent memory and session search",
          "tools": ["memory_save", "memory_read", "session_search"],
      },
      "skills": {
          "description": "Skill management — list, view, create, patch",
          "tools": ["skill_list", "skill_view", "skill_manage"],
      },
      "delegation": {
          "description": "Spawn subagents for parallel research tasks",
          "tools": ["delegate_task"],
      },
  }
  
  
  def sample_toolsets(distribution_name: str) -> List[str]:
      """Sample toolsets based on distribution probabilities.
  
      Each toolset rolls independently — multiple can be active.
      Mirrors NousResearch/hermes-agent/toolset_distributions.py logic.
      """
      dist = RESEARCH_TOOLSET_DISTRIBUTIONS.get(distribution_name)
      if not dist:
          dist = RESEARCH_TOOLSET_DISTRIBUTIONS["general_research"]
  
      selected = []
      for toolset_name, probability in dist["toolsets"].items():
          if random.random() * 100 < probability:
              selected.append(toolset_name)
  
      # Ensure at least one toolset
      if not selected and dist["toolsets"]:
          highest = max(dist["toolsets"].items(), key=lambda x: x[1])
          selected.append(highest[0])
  
      return selected
  
  
  def resolve_tools(toolset_names: List[str]) -> List[str]:
      """Resolve toolset names to individual tool IDs."""
      tools: set[str] = set()
      for name in toolset_names:
          ts = HERMES_TOOLSETS.get(name)
          if ts:
              tools.update(ts["tools"])
      return sorted(tools)
  
  
  # ══════════════════════════════════════════════════════════════
  # Hermes-style System Prompt Builder
  # Inspired by NousResearch/hermes-agent/agent/prompt_builder.py
  # ══════════════════════════════════════════════════════════════
  
  MARINE_RESEARCHER_IDENTITY = (
      "You are AgentsGroup2026 Research Agent, an intelligent research agent "
      "built on the Hermes Agent architecture from Nous Research. "
      "You are a self-improving researcher with a closed learning loop — "
      "you create skills from experience, improve them during use, persist knowledge, "
      "and build deepening expertise across research sessions.\n\n"
      "Your research expertise includes:\n"
      "- Literature review, systematic analysis, and cross-referencing\n"
      "- Technical standards research and compliance verification\n"
      "- Data analysis, formula validation, and computational verification\n"
      "- Architecture review, design pattern analysis, and best practices\n"
      "- Multi-source information synthesis and knowledge extraction\n\n"
      "You communicate in Chinese with English technical terms preserved."
  )
  
  MEMORY_GUIDANCE = (
      "You have persistent memory across sessions. Save durable facts using the memory "
      "tool: research findings, domain conventions, technical citations, calculation results. "
      "Memory is injected into every turn, so keep it compact and focused on facts that "
      "will still matter later.\n"
      "Prioritize what reduces future user steering — the most valuable memory is one "
      "that prevents the user from having to correct or remind you again. "
      "Technical standards, validated formulas, and verified references are high-value.\n"
      "Do NOT save task progress, session outcomes, or temporary TODO state to memory; "
      "use session_search to recall those from past transcripts."
  )
  
  SKILLS_GUIDANCE = (
      "After completing a complex research task (5+ tool calls), validating a formula, "
      "or discovering a non-trivial analysis workflow, save the approach as a "
      "skill with skill_manage so you can reuse it next time.\n"
      "When using a skill and finding it outdated or wrong, "
      "patch it immediately with skill_manage(action='patch').\n"
      "Skills to prioritize: standard lookup workflows, calculation verification, "
      "literature review patterns, compliance audit procedures."
  )
  
  SESSION_SEARCH_GUIDANCE = (
      "When the user references something from a past research session or you suspect "
      "relevant cross-session context exists, use session_search to recall it before "
      "asking them to repeat themselves."
  )
  
  TOOL_USE_ENFORCEMENT = (
      "# Tool-use enforcement\n"
      "You MUST use your tools to take action — do not describe what you would do "
      "or plan to do without actually doing it. When you say you will perform a "
      "research action (e.g. 'I will check the standard', 'Let me verify the formula'), "
      "you MUST immediately make the corresponding tool call in the same response.\n"
      "Every response should either (a) contain tool calls that make progress, or "
      "(b) deliver a final research result to the user."
  )
  
  
  def build_research_system_prompt(
      agent: AgentProfile,
      active_toolsets: Optional[List[str]] = None,
  ) -> str:
      """Build the full Hermes-style system prompt for a research agent.
  
      Assembles: identity → memory guidance → skills guidance → tool enforcement
      → context files → SOUL.md persona.
  
      Mirrors NousResearch/hermes-agent/agent/prompt_builder.py structure.
      """
      sections: List[str] = []
  
      # 1. Identity (SOUL.md or default)
      hc = agent.hermes_config
      if hc and hc.soul_md:
          sections.append(hc.soul_md)
      else:
          sections.append(MARINE_RESEARCHER_IDENTITY)
  
      # 2. Memory guidance
      if hc and hc.memory_enabled:
          sections.append(MEMORY_GUIDANCE)
  
      # 3. Session search guidance
      if hc and hc.session_search_enabled:
          sections.append(SESSION_SEARCH_GUIDANCE)
  
      # 4. Skills guidance
      if hc and hc.skill_auto_create:
          sections.append(SKILLS_GUIDANCE)
  
      # 5. Tool-use enforcement
      sections.append(TOOL_USE_ENFORCEMENT)
  
      # 6. Available toolsets
      if active_toolsets:
          ts_lines = ["## Active Toolsets"]
          for ts_name in active_toolsets:
              ts = HERMES_TOOLSETS.get(ts_name)
              if ts:
                  ts_lines.append(f"- **{ts_name}**: {ts['description']} — tools: {', '.join(ts['tools'])}")
          sections.append("\n".join(ts_lines))
  
      # 7. Context files
      if hc and hc.context_files:
          context_header = "## Project Context\nThe following project context files are loaded:\n"
          sections.append(context_header + "\n".join(f"- {f}" for f in hc.context_files))
  
      # 8. Research reference files
      sections.append(
          "## Key Research Reference Files\n"
          "- `docs/requirements_analysis.md` — Project requirements and specifications\n"
          "- `docs/gap_analysis.md` — Gap analysis and improvement areas\n"
          "- `docs/architecture.md` — System architecture documentation\n"
          "- `config/settings.json` — System configuration and parameters"
      )
  
      return "\n\n".join(sections)
  
  
  # ══════════════════════════════════════════════════════════════
  # Hermes-style Agent Factory
  # ══════════════════════════════════════════════════════════════
  
  # Default SOUL.md for the research agent
  MARINE_RESEARCHER_SOUL = """# Research Agent
  
  You are AgentsGroup2026's research specialist, powered by Hermes Agent architecture.
  
  ## Core Identity
  I am a domain expert in systematic research, technical analysis, and knowledge synthesis.
  I research, validate, and advise — producing rigorous analysis backed by authoritative sources.
  
  ## Personality
  - Rigorous and methodical — every claim must cite a source or provide evidence
  - Proactive learner — after solving a complex problem, I save it as a skill
  - Memory-driven — I persist key findings so I never repeat the same research twice
  - Collaborative — I can delegate sub-research tasks to specialized agents
  
  ## Research Domains
  1. **Literature Review** — systematic search, source evaluation, cross-referencing
  2. **Technical Analysis** — architecture review, design patterns, best practices
  3. **Data Verification** — formula validation, calculation checking, data integrity
  4. **Standards Compliance** — industry standards, regulatory requirements, audit
  5. **Knowledge Synthesis** — multi-source integration, summary generation, insight extraction
  
  ## Behavioral Rules
  - Always cite specific sources, standards, or evidence
  - Never guess parameter ranges — look them up
  - After 5+ tool calls on a complex task, offer to save as a reusable skill
  - Write in Chinese, keep English for technical terms
  """
  
  
  def create_hermes_researcher(
      name: str = "Research Agent",
      distribution: str = "general_research",
      soul_md: str = "",
      can_delegate: bool = True,
  ) -> AgentProfile:
      """Create a Hermes-style research agent.
  
      Returns an AgentProfile with HermesAgentConfig attached,
      pre-configured with the research toolset distribution,
      SOUL.md persona, and self-improving skill/memory capabilities.
      """
      dist = RESEARCH_TOOLSET_DISTRIBUTIONS.get(distribution)
      if not dist:
          dist = RESEARCH_TOOLSET_DISTRIBUTIONS["general_research"]
  
      hermes_config = HermesAgentConfig(
          max_iterations=90,
          iteration_budget=90,
          toolset_distribution=ToolsetDistribution(
              name=distribution,
              description=dist["description"],
              toolsets=dict(dist["toolsets"]),
          ),
          enabled_toolsets=list(dist["toolsets"].keys()),
          disabled_toolsets=[],
          memory_enabled=True,
          session_search_enabled=True,
          skill_auto_create=True,
          soul_md=soul_md or MARINE_RESEARCHER_SOUL,
          context_files=[
              "AGENTS.md",
              "docs/SJTU_REQUIREMENTS_ANALYSIS.md",
              "docs/requirements_analysis.md",
              "docs/gap_analysis.md",
          ],
          can_delegate=can_delegate,
          max_subagents=3,
          platform="cli",
      )
  
      agent = AgentProfile(
          name=name,
          role="研究员 (Hermes Agent)",
          description=(
              "Hermes-style self-improving research agent — "
              "literature review, technical analysis, data verification, "
              "standards compliance, and knowledge synthesis. "
              "Closed learning loop with skills, memory, and session search."
          ),
          template_type=AgentTemplateType.HERMES_RESEARCHER,
          system_prompt="",  # Built dynamically via build_research_system_prompt()
          personality=AgentPersonality(
              tone="professional",
              language="zh-CN",
              expertise_areas=[
                  "literature review",
                  "technical analysis",
                  "data verification",
                 
  ```
  
  ### 文件: `src/backend/agents/plaza_engine.py`
  ```py
  # -*- coding: utf-8 -*-
  """智能体广场引擎 — 讨论编排与多 Agent 协同.
  
  核心编排逻辑:
  1. Moderator（主持人壁龛）提出子话题，引导讨论方向
  2. 每轮: 各参与者按座席层级依次发言（内圈→中圈→外圈）
  3. Moderator 总结本轮关键观点
  4. 最终轮: Moderator 生成全局总结 + 关键结论
  
  消息通过 asyncio.Queue 实时推送给 SSE 订阅者。
  """
  
  from __future__ import annotations
  
  import asyncio
  import logging
  from datetime import datetime, timezone
  from typing import Any, AsyncIterator, Callable, Dict, List, Optional
  from uuid import uuid4
  
  from .plaza import (
      Discussion, DiscussionStatus, NicheRole, Participant,
      Plaza, PlazaMessage, SeatTier, PRESET_TOPICS,
  )
  
  logger = logging.getLogger(__name__)
  
  
  class PlazaEngine:
      """广场引擎 — 管理广场、参与者和讨论编排."""
  
      def __init__(self):
          self._plazas: Dict[str, Plaza] = {}
          self._sse_queues: Dict[str, List[asyncio.Queue]] = {}  # discussion_id → queues
          self._chat_fn: Optional[Callable] = None  # ChatHarness.chat reference
  
      def set_chat_fn(self, fn: Callable):
          """注入 ChatHarness.chat 异步函数."""
          self._chat_fn = fn
  
      # ── 广场 CRUD ──────────────────────────────────────────
  
      def create_plaza(self, name: str, description: str = "") -> Plaza:
          plaza = Plaza(name=name, description=description)
          self._plazas[plaza.id] = plaza
          logger.info(f"🏛️ 广场创建: {name} ({plaza.id})")
          return plaza
  
      def get_plaza(self, plaza_id: str) -> Optional[Plaza]:
          return self._plazas.get(plaza_id)
  
      def list_plazas(self) -> List[Plaza]:
          return list(self._plazas.values())
  
      def delete_plaza(self, plaza_id: str) -> bool:
          if plaza_id in self._plazas:
              del self._plazas[plaza_id]
              return True
          return False
  
      # ── 参与者管理 ──────────────────────────────────────────
  
      def add_participant(
          self, plaza_id: str, agent_id: str, agent_name: str = "",
          role: str = "", team_id: str = "",
          seat_tier: SeatTier = SeatTier.MIDDLE,
          niche_role: NicheRole = NicheRole.OBSERVER,
      ) -> Optional[Participant]:
          plaza = self._plazas.get(plaza_id)
          if not plaza:
              return None
          # 分配壁龛编号 (动态扩展)
          used_niches = {p.niche_index for p in plaza.participants.values() if p.niche_index >= 0}
          niche_index = len(used_niches)
          # 自动扩展壁龛数
          if niche_index >= plaza.niche_count:
              plaza.niche_count = niche_index + 1
          p = Participant(
              agent_id=agent_id, agent_name=agent_name, role=role,
              team_id=team_id, seat_tier=seat_tier, niche_role=niche_role,
              niche_index=niche_index,
          )
          plaza.participants[agent_id] = p
          logger.info(f"🪑 参与者加入广场 {plaza_id}: {agent_name} (壁龛 #{niche_index})")
          return p
  
      def remove_participant(self, plaza_id: str, agent_id: str) -> bool:
          plaza = self._plazas.get(plaza_id)
          if plaza and agent_id in plaza.participants:
              del plaza.participants[agent_id]
              return True
          return False
  
      # ── 讨论管理 ──────────────────────────────────────────
  
      def create_discussion(
          self, plaza_id: str, topic: str, description: str = "",
          moderator_agent_id: str = "", max_rounds: int = 5,
      ) -> Optional[Discussion]:
          plaza = self._plazas.get(plaza_id)
          if not plaza:
              return None
          disc = Discussion(
              plaza_id=plaza_id, topic=topic, description=description,
              moderator_agent_id=moderator_agent_id, max_rounds=max_rounds,
          )
          plaza.discussions[disc.id] = disc
          logger.info(f"💬 讨论创建: {topic[:40]} ({disc.id})")
          return disc
  
      def get_discussion(self, plaza_id: str, discussion_id: str) -> Optional[Discussion]:
          plaza = self._plazas.get(plaza_id)
          if not plaza:
              return None
          return plaza.discussions.get(discussion_id)
  
      def list_discussions(self, plaza_id: str) -> List[Discussion]:
          plaza = self._plazas.get(plaza_id)
          if not plaza:
              return []
          return list(plaza.discussions.values())
  
      # ── SSE 订阅管理 ──────────────────────────────────────
  
      def subscribe(self, discussion_id: str) -> asyncio.Queue:
          q: asyncio.Queue = asyncio.Queue()
          self._sse_queues.setdefault(discussion_id, []).append(q)
          return q
  
      def unsubscribe(self, discussion_id: str, q: asyncio.Queue):
          qs = self._sse_queues.get(discussion_id, [])
          if q in qs:
              qs.remove(q)
  
      async def _broadcast(self, discussion_id: str, event: Dict[str, Any]):
          """向所有 SSE 订阅者推送事件."""
          for q in self._sse_queues.get(discussion_id, []):
              try:
                  q.put_nowait(event)
              except asyncio.QueueFull:
                  pass
  
      # ── 核心讨论编排 ──────────────────────────────────────
  
      async def run_discussion(
          self, plaza_id: str, discussion_id: str,
      ) -> Optional[Discussion]:
          """运行一场完整的广场讨论.
  
          编排流程 (向心结构):
          1. Moderator 开场: 阐述话题，提出第一轮子问题
          2. 每轮:
             a. 各参与者按座席层级依次发言 (内→中→外)
             b. Moderator 总结本轮观点
          3. 最终轮: Moderator 生成全局总结 + 关键结论
          """
          plaza = self._plazas.get(plaza_id)
          if not plaza:
              return None
          disc = plaza.discussions.get(discussion_id)
          if not disc:
              return None
          if disc.status not in (DiscussionStatus.OPEN,):
              return disc
  
          disc.status = DiscussionStatus.IN_PROGRESS
          disc.started_at = datetime.now(timezone.utc).isoformat()
  
          await self._broadcast(disc.id, {
              "type": "discussion_start",
              "discussion_id": disc.id,
              "topic": disc.topic,
          })
  
          participants = list(plaza.participants.values())
          moderator = None
          speakers = []
  
          # 找到 moderator
          if disc.moderator_agent_id:
              moderator = plaza.participants.get(disc.moderator_agent_id)
          if not moderator and participants:
              moderator = participants[0]
              disc.moderator_agent_id = moderator.agent_id
  
          # 按座席层级排序发言者 (内→中→外)
          tier_order = {SeatTier.INNER: 0, SeatTier.MIDDLE: 1, SeatTier.OUTER: 2}
          speakers = sorted(
              [p for p in participants if p.agent_id != moderator.agent_id],
              key=lambda p: tier_order.get(p.seat_tier, 1),
          ) if moderator else participants
  
          if not self._chat_fn:
              # 无 LLM 时使用模拟回复
              await self._run_simulated(disc, moderator, speakers)
              return disc
  
          # ── 开场: Moderator 引导话题 ──
          opening_prompt = (
              f"你是本场讨论的议事长（主持人）。\n"
              f"讨论话题: 「{disc.topic}」\n"
              f"{f'话题描述: {disc.description}' if disc.description else ''}\n"
              f"{f'讨论目标: {disc.goal}' if disc.goal else ''}\n"
              f"参与者: {', '.join(p.agent_name or p.agent_id for p in speakers)}\n\n"
              f"请开场: 简要阐述话题的背景和意义，明确讨论目标，然后提出第一个引导性问题。"
          )
          opening = await self._agent_speak(
              disc, moderator, opening_prompt, round_number=0,
              niche_role="moderator",
          )
  
          # ── 多轮讨论 ──
          for round_num in range(1, disc.max_rounds + 1):
              disc.current_round = round_num
              await self._broadcast(disc.id, {
                  "type": "round_start", "round": round_num,
                  "max_rounds": disc.max_rounds,
              })
  
              # 每个参与者发言
              prev_messages = self._format_history(disc)
              for speaker in speakers:
                  speak_prompt = (
                      f"你正在参与一场关于「{disc.topic}」的讨论。\n"
                      f"你的角色: {speaker.agent_name} ({speaker.role})\n"
                      f"当前是第 {round_num}/{disc.max_rounds} 轮。\n\n"
                      f"之前的讨论内容:\n{prev_messages}\n\n"
                      f"请根据你的专业背景发表观点。注意:\n"
                      f"- 回应之前的讨论内容，可以赞同、补充或提出不同见解\n"
                      f"- 言之有物，提供具体的技术细节或实践经验\n"
                      f"- 控制在 200 字以内"
                  )
                  await self._agent_speak(
                      disc, speaker, speak_prompt, round_number=round_num,
                      niche_role=speaker.niche_role.value,
                  )
                  prev_messages = self._format_history(disc)
  
              # Moderator 总结本轮
              if round_num < disc.max_rounds:
                  summary_prompt = (
                      f"你是主持人。第 {round_num} 轮讨论已结束。\n\n"
                      f"本轮讨论内容:\n{self._format_round_messages(disc, round_num)}\n\n"
                      f"请简要总结本轮的关键观点 (3 句以内)，"
                      f"然后提出下一轮的引导性问题。"
                  )
                  await self._agent_speak(
                      disc, moderator, summary_prompt, round_number=round_num,
                      niche_role="moderator",
                  )
  
          # ── 最终总结 ──
          disc.status = DiscussionStatus.SUMMARIZING
          await self._broadcast(disc.id, {"type": "summarizing"})
  
          final_prompt = (
              f"你是议事长。关于「{disc.topic}」的讨论已经完成 {disc.max_rounds} 轮。\n"
              f"{f'讨论目标: {disc.goal}' if disc.goal else ''}\n\n"
              f"完整讨论记录:\n{self._format_history(disc)}\n\n"
              f"请生成最终总结和执行计划:\n"
              f"1. 讨论概要 (3-5 句)\n"
              f"2. 关键结论 (列出 3-5 个要点)\n"
              f"3. 执行计划:\n"
              f"   - 列出 2-4 个具体可执行的任务步骤\n"
              f"   - 每个步骤包含: 任务名称、负责角色、预期产出\n"
              f"4. 建议指派给哪个团队执行\n\n"
              f"请用结构化格式输出。"
          )
          summary_msg = await self._agent_speak(
              disc, moderator, final_prompt, round_number=disc.max_rounds + 1,
              niche_role="moderator",
          )
          disc.summary = summary_msg.content if summary_msg else ""
          disc.status = DiscussionStatus.CLOSED
          disc.ended_at = datetime.now(timezone.utc).isoformat()
  
          await self._broadcast(disc.id, {
              "type": "discussion_end",
              "summary": disc.summary,
          })
  
          logger.info(
              f"✅ 讨论完成: {disc.topic[:30]} — "
              f"{len(disc.messages)} 条消息, {disc.max_rounds} 轮"
          )
          return disc
  
      async def _agent_speak(
          self, disc: Discussion, participant: Participant,
          prompt: str, round_number: int, niche_role: str = "",
      ) -> Optional[PlazaMessage]:
          """让一个 Agent 在广场中发言."""
          try:
              result = await self._chat_fn(
                  prompt,
                  agent_id=participant.agent_id,
                  system_prompt=(
                      f"你是 {participant.agent_name}，角色: {participant.role}。"
                      f"你正在智能体广场中参与讨论。请用中文回答，专业且简洁。"
                  ),
              )
              content = result.response if result else "[无响应]"
          except Exception as e:
              logger.warning(f"Agent {participant.agent_id} 发言失败: {e}")
              content = f"[{participant.agent_name} 暂时离线]"
  
          msg = PlazaMessage(
              discussion_id=disc.id,
              agent_id=participant.agent_id,
              agent_name=participant.agent_name or participant.agent_id,
              role=participant.role,
              niche_role=niche_role or participant.niche_role.value,
              content=content,
              round_number=round_number,
          )
          disc.messages.append(msg)
  
          await self._broadcast(disc.id, {
              "type": "message",
              "message": msg.to_dict(),
          })
          return msg
  
      async def _run_simulated(
          self, disc: Discussion, moderator: Optional[Participant],
          speakers: List[Participant],
      ):
          """无 LLM 时的模拟讨论."""
          sim_responses = [
              "这是一个很好的话题。从技术角度来看，我认为关键在于系统的可扩展性和模块化设计。",
              "我同意前面的观点，同时想补充：在实际实施中，我们还需要考虑性能瓶颈和容错机制。",
              "从测试的角度，我建议我们在设计阶段就规划好测试策略，包括单元测试和集成测试的覆盖范围。",
              "关于这个问题，业界已经有一些成熟的方案可以参考。我们可以结合自身需求进行适配。",
          ]
  
          if moderator:
              msg = PlazaMessage(
                  discussion_id=disc.id, agent_id=moderator.agent_id,
                  agent_name=moderator.agent_name, role=moderator.role,
                  niche_role="moderator", content=f"欢迎各位参与「{disc.topic}」的讨论。让我们开始吧。",
                  round_number=0,
              )
              disc.messages.append(msg)
              await self._broadcast(disc.id, {"type": "message", "message": msg.to_dict()})
  
          for round_num in range(1, min(disc.max_rounds + 1, 3)):
              disc.current_round = round_num
              await self._broadcast(disc.id, {"type": "round_start", "round": round_num, "max_rounds": disc.max_rounds})
              for i, speaker in enumerate(speakers):
                  content = sim_responses[i % len(sim_responses)]
                  msg = PlazaMessage(
                      discussion_id=disc.id, agent_id=speaker.agent_id,
                      agent_name=speaker.agent_name, role=speaker.role,
                      niche_role=speaker.niche_role.value, conte
  ```
  
  (后续文件因 token 预算已省略)
  
  (后续文件因 token 预算已省略)
  
  (后续文件因 token 预算已省略)
  
  
  ## 前序步骤的产出 (递进式摘要)
  
  ### 步骤 01: pm_decompose
  任务: 创建 greeting 工具函数
  步骤: pm_decompose
  📋 任务: d87c964b-c06
  🤖 Agent: PM (project_manager)
  📂 工作目录: /Users/panglaohu/Downloads/AgentsGroup2026
  🔧 执行方式: DeepSeek API (直连)
  ────────────────────────────────────────────────────────────
  你是 AgentsGroup2026 系统的 PM (project_manager)。
  你是项目经理 (PM)。请对以下任务进行分解和规划:
  创建 greeting 工具函数
  在 src/backend/agents/skills/ 下创建 greeting.py，包含 greet(name) 返回 Hello name。同时创建 tests/test_greeting.py 测试。
  ## 📂 项目上下文 (系统自动预加载)
  ### 项目文件结构 (src/ 目录)
  ### 文件: `src/backend/main.py`
  ### 文件: `src/backend/agents/agent_toolbox.py`
  **子任务拆解:**
    - *任务目标**: 在 `src/backend/agents/skills/` 目录下创建一个名为 `greeting.py` 的工具函数模块，该模块包含一个 `greet(name)` 函数，其功能是返回 `"Hello {name}"` 字符串。同时，创建对应的单元测试文件 `tests/test_greeting.py`。
    - *任务背景**: 此任务旨在为 Agent 系统增加一个基础的、可复用的问候工具函数。这通常是技能注册系统 (`skill_registry.py`) 中的一个标准组件，用于演示或作为其他更复杂技能的基础。
    - **现有代码模式分析**:
    -  **实现方案**:
    - **第一步: 阅读现有代码**
    - **第二步: 实现 `greeting.py`**
    - **第三步: 实现 `test_greeting.py`**
    - **第四步: 运行测试**
  
  ### 步骤 02: research (完整产出)
  
  # 研究分析 — researcher
  
  任务: 创建 greeting 工具函数
  步骤: research
  Agent: build_researcher
  
  ---
  
  📋 任务: d87c964b-c06
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
    创建 greeting 工具函数
    在 src/backend/agents/skills/ 下创建 greeting.py，包含 greet(name) 返回 Hello name。同时创建 tests/test_greeting.py 测试。
    
    ## 📂 项目上下文 (系统自动预加载)
    
    ### 项目文件结构 (src/ 目录)
    ```
    src/frontend/agent-team-config.html
    src/frontend/datacenter-ratchet-evolution.html
    src/frontend/index.html
    src/frontend/login.html
    src/frontend/plaza-old.html
    src/frontend/plaza.html
    src/frontend/system-evolution.html
    src/frontend/css/agent-team-config.css
    src/frontend/css/openbridge-theme.css
    src/frontend/css/ws-theme-bridge.css
    src/frontend/js/agent-team-config.js
    src/frontend/js/i18n.js
    src/frontend/js/nav-sidebar.js
    src/backend/__init__.py
    src/backend/agent_team_api.py
    src/backend/main.py
    src/backend/agents/__init__.py
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
    src/backend/agents/session_store.py
    src/backend/agents/skill_registry.py
    src/backend/agents/task_engine.py
    src/backend/agents/team_manager.py
    src/backend/agents/tool_executor.py
    src/backend/agents/tool_registry.py
    src/backend/agents/teams/__init__.py
    src/backend/agents/teams/ai_coding_team.py
    src/backend/agents/teams/build_team.py
    src/backend/agents/teams/energy_team.py
    src/backend/agents/skills/__init__.py
    src/backend/agents/skills/hello.py
    src/backend/channels/__init__.py
    src/backend/channels/bridge_chat.py
    src/backend/channels/marine_base.py
    src/backend/channels/system_evolution.py
    src/docs/agent_handoffs/38e22004-b64_architecture_20260503T045011.md
    src/docs/agent_handoffs/38e22004-b64_pm_decompose_20260503T044921.md
    src/docs/agent_handoffs/38e22004-b64_research_20260503T044941.md
    src/docs/agent_handoffs/38e22004-b64_task_init_20260503T044856.md
    src/docs/workflow_artifacts/38e22004-b64_architecture.md
    src/docs/workflow_artifacts/38e22004-b64_pm_decompose.md
    src/docs/workflow_artifacts/38e22004-b64_research.md
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
    
                app.include_router(plaza_router, prefix="/api/v1/agent-config")
                logger.info("✅ 智能体广场 API mounted (/api/v1/agent-config/plaza)")
            except Exception as e:
                logger.warning(f"⚠️ Plaza API failed: {e}")
        except Exception as e:
            logger.warning(f"⚠️ Agent Config API failed: {e}")
    
        logger.info("🎉 AgentsGroup2026 ready")
    
    
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
            raise HTTPException(status_code=404, detail="Chat channe
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
    
    ### 文件: `src/backend/agents/hermes_research.py`
    ```py
    # -*- coding: utf-8 -*-
    """AgentsGroup2026 — Hermes-style Research Agent Module.
    
    Transforms the Research Agent from a read-only advisory role into a
    self-improving research agent inspired by NousResearch/hermes-agent:
    
    Architecture mapping (Hermes → AgentsGroup2026):
      - AIAgent class         → HermesResearchAgent
      - run_conversation()    → agent_loop()
      - toolsets.py           → RESEARCH_TOOLSET_DISTRIBUTIONS
      - prompt_builder.py     → build_research_system_prompt()
      - SOUL.md               → agent.hermes_config.soul_md
      - Memory/Skills nudge   → MEMORY_GUIDANCE / SKILLS_GUIDANCE
      - Delegate subagents    → delegate_task()
      - Session search        → session_search()
    
    Key Hermes characteristics adopted:
      1. Closed learning loop — auto-create skills from complex research
      2. Persistent memory — save research findings across sessions
      3. Probabilistic toolset distribution — web 90%, browser 70%, vision 50%
      4. SOUL.md — research persona
      5. Context files — AGENTS.md project context
      6. Tool-use enforcement — tools must be used, not just described
      7. Session search — cross-session recall of past research
    """
    
    from __future__ import annotations
    
    import random
    from dataclasses import dataclass, field
    from typing import Any, Dict, List, Optional
    
    from .models import (
        AgentProfile,
        AgentTemplateType,
        AgentPersonality,
        HermesAgentConfig,
        ToolsetDistribution,
    )
    
    
    # ══════════════════════════════════════════════════════════════
    # Hermes-style Toolset Distributions
    # Inspired by NousResearch/hermes-agent/toolset_distributions.py
    # ══════════════════════════════════════════════════════════════
    
    RESEARCH_TOOLSET_DISTRIBUTIONS: Dict[str, Dict[str, Any]] = {
        "general_research": {
            "description": "General domain research — literature review, data analysis, technical investigation",
            "toolsets": {
                "web": 90,
                "browser": 70,
                "vision": 50,
                "file": 80,
                "research": 95,
                "memory": 100,
                "skills": 100,
                "delegation": 30,
            },
        },
        "deep_analysis": {
            "description": "Deep analysis — systematic review, data verification, cross-referencing",
            "toolsets": {
                "web": 60,
                "file": 95,
                "research": 100,
                "code_execution": 80,
                "memory": 100,
                "vision": 40,
            },
        },
        "compliance_audit": {
            "description": "Standards and compliance verification",
            "toolsets": {
                "web": 85,
                "browser": 65,
                "file": 90,
                "research": 100,
                "code_execution": 70,
                "memory": 100,
            },
        },
        "technical_review": {
            "description": "Technical design review, architecture analysis, code review",
            "toolsets": {
                "web": 50,
                "file": 95,
                "code_execution": 90,
                "research": 100,
                "vision": 70,
                "memory": 100,
            },
        },
        "general_research": {
            "description": "General web research with all tools available",
            "toolsets": {
                "web": 90,
                "browser": 70,
                "vision": 50,
                "memory": 100,
                "skills": 100,
                "file": 60,
                "code_execution": 30,
            },
        },
    }
    
    # ══════════════════════════════════════════════════════════════
    # Hermes-style Toolset Definitions
    # Inspired by NousResearch/hermes-agent/toolsets.py
    # ══════════════════════════════════════════════════════════════
    
    HERMES_TOOLSETS: Dict[str, Dict[str, Any]] = {
        "web": {
            "description": "Web research and content extraction",
            "tools": ["web_search", "extract_content"],
        },
        "browser": {
            "description": "Browser automation for deep research",
            "tools": ["navigate_url", "screenshot", "click_element", "fill_form", "extract_content", "web_search"],
        },
        "file": {
            "description": "File read/write/search operations",
            "tools": ["read_file", "write_file", "list_directory", "search_files"],
        },
        "code_execution": {
            "description": "Run Python/shell for analysis and calculation",
            "tools": ["run_python", "run_shell"],
        },
        "vision": {
            "description": "Image/chart analysis for technical documents",
            "tools": ["screenshot"],
        },
        "research": {
            "description": "Research-specific tools — search, analysis, data retrieval",
            "tools": ["search_query", "data_lookup", "info_fetch", "analysis_engine"],
        },
        "memory": {
            "description": "Persistent memory and session search",
            "tools": ["memory_save", "memory_read", "session_search"],
        },
        "skills": {
            "description": "Skill management — list, view, create, patch",
            "tools": ["skill_list", "skill_view", "skill_manage"],
        },
        "delegation": {
            "description": "Spawn subagents for parallel research tasks",
            "tools": ["delegate_task"],
        },
    }
    
    
    def sample_toolsets(distribution_name: str) -> List[str]:
        """Sample toolsets based on distribution pr
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

# 技术方案 — greeting 工具函数

## 1. 方案概述

在 `src/backend/agents/skills/` 下创建 `greeting.py` 工具函数模块，包含 `greet(name)` 函数，返回 `"Hello {name}"`。同时创建对应的单元测试文件 `tests/test_greeting.py`。

## 2. 技术调研结论

### 2.1 现有代码模式分析

通过阅读项目源码，发现以下关键模式：

1. **技能模块模式** (`src/backend/agents/skills/hello.py`):
   - 技能模块是简单的 Python 函数模块
   - 通过 `skill_registry.py` 注册到系统中
   - 被 `tool_executor.py` 调用执行

2. **测试模式**:
   - 项目使用 `pytest` 作为测试框架
   - 测试文件位于 `tests/` 目录下
   - 测试文件命名规范: `test_*.py`

3. **项目结构**:
   - 后端代码在 `src/backend/`
   - 技能模块在 `src/backend/agents/skills/`
   - 测试文件在 `tests/`

### 2.2 关键依赖分析

- **skill_registry.py**: 技能注册中心，负责管理所有技能模块
- **tool_executor.py**: 工具执行器，负责调用技能函数
- **agent_toolbox.py**: Agent 工具箱，提供文件读写等工具

## 3. 详细设计方案

### 3.1 新增文件

#### 文件 1: `src/backend/agents/skills/greeting.py`

```python
# -*- coding: utf-8 -*-
"""
greeting — 问候工具函数

提供基础的问候功能，可作为其他技能的基础组件。
"""

from __future__ import annotations

from typing import Optional


def greet(name: str) -> str:
    """返回问候语 "Hello {name}"。

    Args:
        name: 要问候的对象名称

    Returns:
        格式化的问候语字符串

    Raises:
        ValueError: 如果 name 为空或 None

    Examples:
        >>> greet("World")
        'Hello World'
        >>> greet("Alice")
        'Hello Alice'
    """
    if not name or not name.strip():
        raise ValueError("name cannot be empty")
    return f"Hello {name.strip()}"


def greet_formal(title: str, last_name: str) -> str:
    """返回正式问候语 "Hello {title} {last_name}"。

    Args:
        title: 称谓 (Mr./Ms./Dr.)
        last_name: 姓氏

    Returns:
        格式化的正式问候语

    Examples:
        >>> greet_formal("Mr.", "Smith")
        'Hello Mr. Smith'
    """
    return f"Hello {title} {last_name}"
```

#### 文件 2: `tests/test_greeting.py`

```python
# -*- coding: utf-8 -*-
"""
Tests for greeting skill module.
"""

from __future__ import annotations

import pytest
from src.backend.agents.skills.greeting import greet, greet_formal


class TestGreet:
    """Test suite for greet() function."""

    def test_basic_greeting(self):
        """Test basic greeting with a simple name."""
        result = greet("World")
        assert result == "Hello World"

    def test_greeting_with_name(self):
        """Test greeting with a person's name."""
        result = greet("Alice")
        assert result == "Hello Alice"

    def test_greeting_with_chinese_name(self):
        """Test greeting with Chinese characters."""
        result = greet("张三")
        assert result == "Hello 张三"

    def test_greeting_with_numbers(self):
        """Test greeting with numeric string."""
        result = greet("Agent007")
        assert result == "Hello Agent007"

    def test_greeting_with_spaces(self):
        """Test greeting with extra spaces (should be stripped)."""
        result = greet("  Bob  ")
        assert result == "Hello Bob"

    def test_empty_name_raises_error(self):
        """Test that empty name raises ValueError."""
        with pytest.raises(ValueError, match="name cannot be empty"):
            greet("")

    def test_none_name_raises_error(self):
        """Test that None name raises ValueError."""
        with pytest.raises(ValueError, match="name cannot be empty"):
            greet(None)  # type: ignore

    def test_whitespace_only_name_raises_error(self):
        """Test that whitespace-only name raises ValueError."""
        with pytest.raises(ValueError, match="name cannot be empty"):
            greet("   ")


class TestGreetFormal:
    """Test suite for greet_formal() function."""

    def test_formal_greeting(self):
        """Test formal greeting with title and last name."""
        result = greet_formal("Mr.", "Smith")
        assert result == "Hello Mr. Smith"

    def test_formal_greeting_doctor(self):
        """Test formal greeting with Dr. title."""
        result = greet_formal("Dr.", "Jones")
        assert result == "Hello Dr. Jones"

    def test_formal_greeting_professor(self):
        """Test formal greeting with Prof. title."""
        result = greet_formal("Prof.", "Wang")
        assert result == "Hello Prof. Wang"
```

### 3.2 无需修改的文件

以下文件**不需要**修改，因为 greeting 技能是独立的工具函数：

- `src/backend/main.py` — 不需要修改，技能通过注册机制自动发现
- `src/backend/agents/agent_toolbox.py` — 不需要修改，greeting 不是 Agent 工具箱的一部分
- `src/backend/agents/skill_registry.py` — 不需要修改，技能注册是动态的
- `src/backend/agents/tool_executor.py` — 不需要修改，执行器自动处理新技能

## 4. 接口规范

### 4.1 `greet(name: str) -> str`

| 参数 | 类型 | 必需 | 说明 |
|------|------|------|------|
| name | str | 是 | 要问候的对象名称 |

**返回值**: `str` — 格式化的问候语 `"Hello {name}"`

**异常**: `ValueError` — 当 name 为空或 None 时抛出

### 4.2 `greet_formal(title: str, last_name: str) -> str`

| 参数 | 类型 | 必需 | 说明 |
|------|------|------|------|
| title | str | 是 | 称谓 (Mr./Ms./Dr.) |
| last_name | str | 是 | 姓氏 |

**返回值**: `str` — 格式化的正式问候语 `"Hello {title} {last_name}"`

## 5. 实施指南

### 步骤 1: 创建 greeting.py

在 `src/backend/agents/skills/` 目录下创建 `greeting.py` 文件，包含上述代码。

### 步骤 2: 创建 test_greeting.py

在 `tests/` 目录下创建 `test_greeting.py` 文件，包含上述测试代码。

### 步骤 3: 运行测试

```bash
cd /Users/panglaohu/Downloads/AgentsGroup2026
python -m pytest tests/test_greeting.py -v
```

预期输出:
```
tests/test_greeting.py::TestGreet::test_basic_greeting PASSED
tests/test_greeting.py::TestGreet::test_greeting_with_name PASSED
tests/test_greeting.py::TestGreet::test_greeting_with_chinese_name PASSED
tests/test_greeting.py::TestGreet::test_greeting_with_numbers PASSED
tests/test_greeting.py::TestGreet::test_greeting_with_spaces PASSED
tests/test_greeting.py::TestGreet::test_empty_name_raises_error PASSED
tests/test_greeting.py::TestGreet::test_none_name_raises_error PASSED
tests/test_greeting.py::TestGreet::test_whitespace_only_name_raises_error PASSED
tests/test_greeting.py::TestGreetFormal::test_formal_greeting PASSED
tests/test_greeting.py::TestGreetFormal::test_formal_greeting_doctor PASSED
tests/test_greeting.py::TestGreetFormal::test_formal_greeting_professor PASSED
```

### 步骤 4: 验证导入

```bash
cd /Users/panglaohu/Downloads/AgentsGroup2026
python -c "from src.backend.agents.skills.greeting import greet; print(greet('World'))"
```

预期输出: `Hello World`

## 6. 风险与注意事项

1. **路径问题**: 确保 `tests/` 目录存在，如果不存在需要先创建
2. **导入路径**: 测试文件中的导入路径 `from src.backend.agents.skills.greeting import greet` 需要与项目结构一致
3. **Python 版本**: 项目使用 Python 3.10+，确保 `from __future__ import annotations` 兼容

────────────────────────────────────────────────────────────
✅ deepseek-chat 完成
