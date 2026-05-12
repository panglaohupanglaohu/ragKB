# 架构设计 — architect

任务: 集成回归杀伤率门禁，要求修复模板在对应契约仿真中复现并杀死同类缺陷方可发布
步骤: architecture
Agent: build_architect

---

📋 任务: 72652523-8a4
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
  集成回归杀伤率门禁，要求修复模板在对应契约仿真中复现并杀死同类缺陷方可发布
  Tester + Architect
  
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
  src/docs/agent_handoffs/3bde709e-2fe_executor_started_20260507T031444.md
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
  src/docs/agent_handoffs/65c1db92-524_executor_started_20260507T031444.md
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
  src/docs/agent_handoffs/8665633b-cad_executor_started_20260507T031444.md
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
  ... (共 258 个 src/ 文件)
  
  ```
  
  ### 文件: `src/backend/agents/chat_harness.py`
  ```py
  # -*- coding: utf-8 -*-
  """AgentsGroup2026 Chat Harness — Unified LLM Chat Module.
  
  Inspired by claw-code's QueryEngine + Runtime architecture:
  - Single chat module used by ALL agents, bridge commands, and sessions
  - Provider abstraction: OpenAI-compatible, Anthropic, DeepSeek, local Ollama
  - Session/turn management, token budgeting, transcript compaction
  - Tool invocation pipeline with permission checks
  - Streaming support via SSE-compatible generator
  
  Usage:
      harness = ChatHarness.from_config(config_path="config/settings.json")
      result = await harness.chat(agent_id, prompt, tools=[...])
  
      # Or streaming:
      async for chunk in harness.stream_chat(agent_id, prompt):
          ...
  """
  
  from __future__ import annotations
  
  import json
  import logging
  import os
  import time
  from collections import deque
  from dataclasses import dataclass, field
  from datetime import datetime, timezone
  from enum import Enum
  from pathlib import Path
  from typing import Any, AsyncIterator, Callable, Dict, List, Optional, Tuple
  from uuid import uuid4
  
  from .session_store import (
      StoredSession, TranscriptStore,
      save_session, load_session as _load_stored_session,
      list_sessions as _list_stored_sessions,
      search_sessions,
  )
  from .execution_registry import (
      HistoryLog, ToolPermissionContext, PermissionDenial,
      RoutedMatch, ToolPool, assemble_tool_pool,
      PortRuntime, build_execution_registry,
  )
  
  logger = logging.getLogger(__name__)
  
  
  # ═══════════════════════════════════════════════════════════════
  # UltraPlan — Agentic Planning + Execution Pipeline
  # Inspired by Clawith's plan→act→observe→reflect loop
  # ═══════════════════════════════════════════════════════════════
  
  
  class PlanStepStatus(Enum):
      """Status of a single plan step."""
      PENDING = "pending"
      RUNNING = "running"
      COMPLETED = "completed"
      FAILED = "failed"
      SKIPPED = "skipped"
  
  
  @dataclass
  class PlanStep:
      """A single step in an execution plan."""
      step_id: int = 0
      action: str = ""            # e.g. "tool_call", "think", "respond", "delegate"
      tool_name: str = ""         # Tool to invoke (if action == "tool_call")
      tool_args: Dict[str, Any] = field(default_factory=dict)
      description: str = ""       # Human-readable description
      status: PlanStepStatus = PlanStepStatus.PENDING
      result: str = ""
      error: str = ""
      duration_ms: float = 0.0
      depends_on: List[int] = field(default_factory=list)
  
      def to_dict(self) -> Dict[str, Any]:
          return {
              "step_id": self.step_id,
              "action": self.action,
              "tool_name": self.tool_name,
              "description": self.description,
              "status": self.status.value,
              "result": self.result[:500] if self.result else "",
              "error": self.error,
              "duration_ms": self.duration_ms,
              "depends_on": self.depends_on,
          }
  
  
  @dataclass
  class ExecutionPlan:
      """An ordered plan of steps to fulfill a user request."""
      plan_id: str = field(default_factory=lambda: uuid4().hex[:8])
      goal: str = ""
      steps: List[PlanStep] = field(default_factory=list)
      created_at: str = field(
          default_factory=lambda: datetime.now(timezone.utc).isoformat()
      )
      status: str = "pending"  # pending / running / completed / failed
      final_response: str = ""
  
      def add_step(self, action: str, description: str = "",
                   tool_name: str = "", tool_args: Optional[Dict[str, Any]] = None,
                   depends_on: Optional[List[int]] = None) -> PlanStep:
          step = PlanStep(
              step_id=len(self.steps) + 1,
              action=action,
              tool_name=tool_name,
              tool_args=tool_args or {},
              description=description,
              depends_on=depends_on or [],
          )
          self.steps.append(step)
          return step
  
      @property
      def completed_steps(self) -> int:
          return sum(1 for s in self.steps if s.status == PlanStepStatus.COMPLETED)
  
      @property
      def progress(self) -> float:
          if not self.steps:
              return 1.0
          return self.completed_steps / len(self.steps)
  
      def to_dict(self) -> Dict[str, Any]:
          return {
              "plan_id": self.plan_id,
              "goal": self.goal,
              "status": self.status,
              "steps": [s.to_dict() for s in self.steps],
              "progress": round(self.progress, 2),
              "created_at": self.created_at,
          }
  
  
  # Plan builder: analyzes prompt keywords to auto-generate execution steps
  def build_plan_from_prompt(prompt: str, available_tools: List[str] = None) -> ExecutionPlan:
      """Build an execution plan by analyzing the prompt intent.
  
      This is a rule-based planner that maps keywords to tool invocations.
      When an LLM is available, the plan can be refined by the model.
      """
      plan = ExecutionPlan(goal=prompt[:200])
      lower = prompt.lower()
      tools = set(available_tools or [])
  
      # Multi-domain research
      if any(kw in lower for kw in ["研究", "分析", "调研", "research", "investigate"]):
          plan.add_step("tool_call", "网络搜索相关资料", tool_name="web_search",
                         tool_args={"query": prompt[:100]})
          plan.add_step("think", "整理搜索结果")
          plan.add_step("tool_call", "保存研究发现", tool_name="memory_save",
                         tool_args={"key": f"research_{uuid4().hex[:6]}", "content": ""})
          plan.add_step("respond", "生成研究报告")
  
      # General — single-step
      else:
          plan.add_step("think", "理解用户意图")
          plan.add_step("respond", "生成回复")
  
      return plan
  
  
  # Middleware hook type for plan interception
  PlanMiddleware = Callable[[ExecutionPlan], ExecutionPlan]
  
  
  # ═══════════════════════════════════════════════════════════════
  # Provider Abstraction
  # ═══════════════════════════════════════════════════════════════
  
  
  class LLMProvider(Enum):
      """Supported LLM providers."""
      OPENAI = "openai"
      ANTHROPIC = "anthropic"
      DEEPSEEK = "deepseek"
      OPENROUTER = "openrouter"
      LOCAL = "local"         # Ollama / vLLM / local OpenAI-compatible
      GITHUB = "github"       # GitHub Copilot models
      QWEN = "qwen"
  
  
  @dataclass
  class ProviderConfig:
      """LLM provider connection configuration."""
      provider: LLMProvider = LLMProvider.DEEPSEEK
      api_key: str = ""
      api_base_url: str = ""
      model: str = "deepseek-v4-pro"
      max_tokens: int = 65536  # DeepSeek V4: 64K output
      temperature: float = 0.2
      timeout: float = 1200.0  # Long timeout for big code generations
      thinking: Optional[Dict[str, str]] = None  # e.g. {"type": "enabled"}
      reasoning_effort: str = ""  # "low" | "medium" | "high"
  
      # Default endpoints per provider
      _DEFAULT_URLS: dict = field(default_factory=lambda: {
          LLMProvider.OPENAI: "https://api.openai.com/v1",
          LLMProvider.ANTHROPIC: "https://api.anthropic.com/v1",
          LLMProvider.DEEPSEEK: "https://api.deepseek.com",
          LLMProvider.OPENROUTER: "https://openrouter.ai/api/v1",
          LLMProvider.LOCAL: "http://127.0.0.1:11434/v1",
          LLMProvider.GITHUB: "https://models.inference.ai.azure.com",
          LLMProvider.QWEN: "https://dashscope.aliyuncs.com/compatible-mode/v1",
      }, repr=False)
  
      def resolve_base_url(self) -> str:
          if self.api_base_url:
              return self.api_base_url.rstrip("/")
          return self._DEFAULT_URLS.get(self.provider, "http://127.0.0.1:11434/v1")
  
      @classmethod
      def from_env(cls) -> "ProviderConfig":
          """Build config from environment variables."""
          provider_str = os.getenv("AG_LLM_PROVIDER", "deepseek")
          try:
              provider = LLMProvider(provider_str)
          except ValueError:
              provider = LLMProvider.DEEPSEEK
  
          return cls(
              provider=provider,
              api_key=os.getenv("AG_LLM_API_KEY", os.getenv("DEEPSEEK_API_KEY", "")),
              api_base_url=os.getenv("AG_LLM_BASE_URL", ""),
              model=os.getenv("AG_LLM_MODEL", "deepseek-v4-pro"),
              max_tokens=int(os.getenv("AG_LLM_MAX_TOKENS", "65536")),
              temperature=float(os.getenv("AG_LLM_TEMPERATURE", "0.2")),
              thinking={"type": "enabled"},
              reasoning_effort="high",
          )
  
      @classmethod
      def from_settings(cls, settings: Dict[str, Any]) -> "ProviderConfig":
          """Build from config/settings.json llm section."""
          llm = settings.get("llm", {})
          provider_str = llm.get("provider", "local")
          try:
              provider = LLMProvider(provider_str)
          except ValueError:
              provider = LLMProvider.LOCAL
  
          return cls(
              provider=provider,
              api_key=llm.get("api_key", os.getenv("DEEPSEEK_API_KEY", "")),
              api_base_url=llm.get("local", llm.get("api_base_url", "")),
              model=llm.get("model", "deepseek-v4-pro"),
              max_tokens=llm.get("max_tokens", 65536),
              temperature=llm.get("temperature", 0.2),
              thinking=llm.get("thinking"),
              reasoning_effort=llm.get("reasoning_effort", ""),
          )
  
      @classmethod
      def from_model_config(cls, model_config: Any) -> "ProviderConfig":
          """Build from agents.models.ModelConfig."""
          provider_str = getattr(model_config, "provider", "deepseek")
          try:
              provider = LLMProvider(provider_str)
          except ValueError:
              provider = LLMProvider.DEEPSEEK
  
          return cls(
              provider=provider,
              api_key=getattr(model_config, "api_key", ""),
              api_base_url=getattr(model_config, "api_base_url", ""),
              model=getattr(model_config, "name", "deepseek-v4-pro"),
              max_tokens=getattr(model_config, "max_tokens", 65536),
              temperature=getattr(model_config, "temperature", 0.2),
              thinking={"type": "enabled"},
              reasoning_effort="high",
          )
  
  
  # ═══════════════════════════════════════════════════════════════
  # Turn / Session Data Models
  # ═══════════════════════════════════════════════════════════════
  
  
  @dataclass
  class UsageSummary:
      """Token usage tracking (mirrors claw-code UsageSummary)."""
      input_tokens: int = 0
      output_tokens: int = 0
      total_tokens: int = 0
  
      def add(self, inp: int, out: int) -> "UsageSummary":
          return UsageSummary(
              input_tokens=self.input_tokens + inp,
              output_tokens=self.output_tokens + out,
              total_tokens=self.total_tokens + inp + out,
          )
  
      def to_dict(self) -> Dict[str, int]:
          return {
              "input_tokens": self.input_tokens,
              "output_tokens": self.output_tokens,
              "total_tokens": self.total_tokens,
          }
  
  
  @dataclass
  class ToolInvocation:
      """A tool call extracted from the LLM response."""
      tool_name: str = ""
      arguments: Dict[str, Any] = field(default_factory=dict)
      result: str = ""
      permitted: bool = True
      denial_reason: str = ""
  
      def to_dict(self) -> Dict[str, Any]:
          return {
              "tool_name": self.tool_name,
              "arguments": self.arguments,
              "result": self.result,
              "permitted": self.permitted,
              "denial_reason": self.denial_reason,
          }
  
  
  @dataclass
  class TurnResult:
      """Result of a single chat turn (mirrors claw-code TurnResult)."""
      prompt: str = ""
      response: str = ""
      usage: UsageSummary = field(default_factory=UsageSummary)
      tool_invocations: List[ToolInvocation] = field(default_factory=list)
      stop_reason: str = "completed"
      model: str = ""
      provider: str = ""
      latency_ms: float = 0.0
      error: str = ""
      timestamp: str = field(
          default_factory=lambda: datetime.now(timezone.utc).isoformat()
      )
  
      def to_dict(self) -> Dict[str, Any]:
          return {
              "prompt": self.prompt,
              "response": self.response,
              "usage": self.usage.to_dict(),
              "tool_invocations": [t.to_dict() for t in self.tool_invocations],
              "stop_reason": self.stop_reason,
              "model": self.model,
              "provider": self.provider,
              "latency_ms": self.latency_ms,
              "error": self.error,
              "timestamp": self.timestamp,
          }
  
  
  @dataclass
  class ChatMessage:
      """A single message in a conversation."""
      role: str = "user"  # user | assistant | system | tool
      content: str = ""
      name: str = ""
      tool_calls: List[Dict[str, Any]] = field(default_factory=list)
      timestamp: str = field(
          default_factory=lambda: datetime.now(timezone.utc).isoformat()
      )
  
      def to_openai_dict(self) -> Dict[str, Any]:
          d: Dict[str, Any] = {"role": self.role, "content": self.content}
          if self.name:
              d["name"] = self.name
          return d
  
  
  @dataclass
  class ChatSession:
      """Stateful conversation session with compaction, history & transcript.
  
      Integrates claw-code-parity patterns:
      - HistoryLog for event tracking
      - TranscriptStore for persistence & replay
      - Permission tracking
      """
      session_id: str = field(default_factory=lambda: uuid4().hex[:12])
      agent_id: str = ""
      system_prompt: str = ""
      messages: List[ChatMessage] = field(default_factory=list)
      total_usage: UsageSummary = field(default_factory=UsageSummary)
      turn_count: int = 0
      created_at: str = field(
          default_factory=lambda: datetime.now(timezone.utc).isoformat()
      )
      max_turns: int = 100
      compact_after: int = 40
      # claw-code-parity extensions
      history: HistoryLog = field(default_factory=HistoryLog)
      transcript: TranscriptStore = field(default_factory=TranscriptStore)
      permission_denials: List[PermissionDenial] = field(default_factory=list)
  
      def add_user_message(self, content: str) -> None:
          self.messages.append(ChatMessage(role="user", content=content))
          self.transcript.append(content)
          self.history.add("user_message", content[:100])
  
      def add_assistant_message(self, content: str) -> None:
          self.messages.append(ChatMessage(role="assistant", content=content))
          self.turn_count += 1
          self.transcript.append(content)
          self.history.add("assistant_message", f"turn={self.turn_count}")
  
      def compact_if_needed(self) -> None:
          """Keep conversation manageable by dropping old turns."""
          if len(self.messages) > self.compact_after:
              # Keep system prompt context (first msg if system) + last N messages
              keep = self.compact_after // 2
              sys_msgs = [m for m in self.messages[:1] if m.role == "system"]
              self.messages = sys_msgs + self.messages[-keep:]
  
      def build_openai_messages(self) -> List[Dict[str, Any]]:
          """Build the messages array for OpenAI-compatible API calls."""
          msgs = []
          if self.system_prompt:
              msgs.append({"role": "system", "content": self.system_prompt})
          msgs.extend(m.to_openai_dict() for m in self.messages)
          return msgs
  
      def persist(self) -> str:
        
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
      toolsets: Dict[str, int] = field(default_factory=dict)
  
      def to_dict(self) -> Dict[str, Any]:
          return {
              "name": self.name,
              "description": self.description,
              "toolsets": self.toolsets,
          }
  
  
  @dataclass
  class HermesAgentConfig:
      """Hermes-style agent configuration — extends AgentProfile with
      learning loop, memory, skills, toolsets, and context management.
  
      Inspired by NousResearch/hermes-agent architecture:
      - Closed learning loop (skills from experience)
      - Persistent memory across sessions
      - Toolset distributions for probabilistic tool access
      - SOUL.md persona
      - Context files (AGENTS.md, HERMES.md)
      - Session search (cross-session recall)
      - Delegate/subagent parallelization
      """
  
      # Agent loop parameters
      max_iterations: int = 90
      iteration_budget: int = 90
  
      # Toolset distribution (Hermes-style probabilistic tool selection)
      toolset_distribution: ToolsetDistribution = field(
          default_factory=lambda: ToolsetDistribution(name="default")
      )
      enabled_toolsets: List[str] = field(default_factory=list)
      disabled_toolsets: List[str] = field(default_factory=list)
  
      # Memory & learning
      memory_enabled: bool = True
      session_search_enabled: bool = True
      skill_auto_create: bool = True
      soul_md: str = ""
      context_files: List[str] = field(default_factory=list)
  
      # Delegation
      can_delegate: bool = False
      max_subagents: int = 3
  
      # Platform
      platform: str = "cli"
  
      def to_dict(self) -> Dict[str, Any]:
          return {
              "max_iterations": self.max_iterations,
              "iteration_budget": self.iteration_budget,
              "toolset_distribution": self.toolset_distribution.to_dict(),
              "enabled_toolsets": self.enabled_toolsets,
              "disabled_toolsets": self.disabled_toolsets,
              "memory_enabled": self.memory_enabled,
              "session_search_enabled": self.session_search_enabled,
              "skill_auto_create": self.skill_auto_create,
              "soul_md": self.soul_md,
              "context_files": self.context_files,
              "can_delegate": self.can_delegate,
              "max_subagents": self.max_subagents,
              "platform": self.platform,
          }
  
  
  @dataclass
  class AgentPermission:
      """Agent access permission."""
  
      resource: str = ""
      access_level: AccessLevel = AccessLevel.READ
      channels: List[str] = field(default_factory=list)
  
      def to_dict(self) -> Dict[str, Any]:
          return {
              "resource": self.resource,
              "access_level": self.access_level.value,
              "channels": self.channels,
          }
  
  
  @dataclass
  class AgentChannelConfig:
      """Channel subscription configuration for an agent."""
  
      channel_name: str = ""
      subscribe: bool = True
      publish: bool = False
      priority: int = 0
  
      def to_dict(self) -> Dict[str, Any]:
          return {
              "channel_name": self.channel_name,
              "subscribe": self.subscribe,
              "publish": self.publish,
              "priority": self.priority,
          }
  
  
  @dataclass
  class AgentProfile:
      """Individual agent profile — the Employee equivalent."""
  
      agent_id: str = ""
      name: str = ""
      role: str = ""
      description: str = ""
      template_type: AgentTemplateType = AgentTemplateType.CUSTOM
      state: AgentState = AgentState.IDLE
      model_id: str = ""
      system_prompt: str = ""
      personality: AgentPersonality = field(default_factory=AgentPersonality)
      permissions: List[AgentPermission] = field(default_factory=list)
      channels: List[AgentChannelConfig] = field(default_factory=list)
      tools: List[str] = field(default_factory=list)
      skills: List[str] = field(default_factory=list)
      metadata: Dict[str, Any] = field(default_factory=dict)
      created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
      # Hermes-style agent config (optional — non-None means Hermes mode)
      hermes_config: Optional[HermesAgentConfig] = None
  
      def __post_init__(self) -> None:
          if not self.agent_id:
              self.agent_id = str(uuid.uuid4())[:8]
  
      @property
      def is_hermes_agent(self) -> bool:
          return self.hermes_config is not None
  
      def to_dict(self) -> Dict[str, Any]:
          d = {
              "agent_id": self.agent_id,
              "name": self.name,
              "role": self.role,
              "description": self.description,
              "template_type": self.template_type.value,
              "state": self.state.value,
              "model_id": self.model_id,
              "system_prompt": self.system_prompt,
              "personality": self.personality.to_dict(),
              "permissions": [p.to_dict() for p in self.permissions],
              "channels": [c.to_dict() for c in self.channels],
              "tools": self.tools,
              "skills": self.skills,
              "metadata": self.metadata,
              "created_at": self.created_at,
              "is_hermes_agent": self.is_hermes_agent,
          }
          if self.hermes_config is not None:
              d["hermes_config"] = self.hermes_config.to_dict()
          return d
  
  
  @dataclass
  class AgentTeam:
      """Agent team — the Company equivalent. Holds shared resources."""
  
      team_id: str = ""
      name: str = ""
      description: str = ""
      visibility: Visibility = Visibility.PRIVATE
      agents: Dict[str, AgentProfile] = field(default_factory=dict)
      models: Dict[str, ModelConfig] = field(default_factory=dict)
      tools: Dict[str, ToolDefinition] = field(default_factory=dict)
      skills: Dict[str, SkillDefinition] = field(default_factory=dict)
      metadata: Dict[str, Any] = field(default_factory=dict)
      created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
  
      def __post_init__(self) -> None:
          if not self.team_id:
              self.team_id = str(uuid.uuid4())[:8]
  
      def add_agent(self, agent: AgentProfile) -> None:
          self.agents[agent.agent_id] = agent
  
      def remove_agent(self, agent_id: str) -> Optional[AgentProfile]:
          return self.agents.pop(agent_id, None)
  
      def get_agent(self, agent_id: str) -> Optional[AgentProfile]:
          return self.agents.get(agent_id)
  
      def add_model(self, model: ModelConfig) -> None:
          self.models[model.model_id] = model
  
      def remove_model(self, model_id: str) -> Optional[ModelConfig]:
          return self.models.pop(model_id, None)
  
      def get_model(self, model_id: str) -> Optional[ModelConfig]:
          return self.models.get(model_id)
  
      def add_tool(self, tool: ToolDefinition) -> None:
          self.tools[tool.tool_id] = tool
  
      def get_tool(self, tool_id: str) -> Optional[ToolDefinition]:
          return self.tools.get(tool_id)
  
      def add_skill(self, skill: SkillDefinition) -> None:
          self.skills[skill.skill_id] = skill
  
      def get_skill(self, skill_id: str) -> Optional[SkillDefinition]:
          return self.skills.get(skill_id)
  
      def to_dict(self) -> Dict[str, Any]:
          return {
              "team_id": self.team_id,
              "name": self.name,
              "description": self.description,
              "visibility": self.visibility.value,
              "agents": {k: v.to_dict() for k, v in self.agents.items()},
              "models": {k: v.to_dict() for k, v in self.models.items()},
              "tools": {k: v.to_dict() for k, v in self.tools.items()},
              "skills": {k: v.to_dict() for k, v in self.skills.items()},
              "metadata": self.metadata,
              "created_at": self.created_at,
          }
  
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
  import json
  import logging
  import re
  from datetime import datetime, timezone
  from typing import Any, AsyncIterator, Callable, Dict, List, Optional
  from uuid import uuid4
  
  from .plaza import (
      Discussion, DiscussionStatus, NicheRole, Participant,
      Plaza, PlazaMessage, SeatTier, PRESET_TOPICS,
  )
  from .plaza_store import PlazaStore
  
  logger = logging.getLogger(__name__)
  
  _ROUND_SPEAKER_LIMIT = 5
  _EXCHANGES_PER_ROUND = 2  # 每轮内交锋次数
  _SPEAKERS_PER_EXCHANGE = 3  # 每次交锋参与人数
  _CORE_ROLE_PRIORITY = {
      "architect": 0,
      "researcher": 1,
      "developer": 2,
      "qa_engineer": 3,
      "qa": 3,
      "tester": 3,
      "devops": 4,
      "project_manager": 5,
      "documentation": 6,
  }
  
  
  class PlazaEngine:
      """广场引擎 — 管理广场、参与者和讨论编排."""
  
      def __init__(self):
          self._store = PlazaStore()
          self._plazas: Dict[str, Plaza] = self._store.load_all()
          self._sse_queues: Dict[str, List[asyncio.Queue]] = {}  # discussion_id → queues
          self._discussion_locks: Dict[str, asyncio.Lock] = {}
          self._chat_fn: Optional[Callable] = None  # ChatHarness.chat reference
  
      def set_chat_fn(self, fn: Callable):
          """注入 ChatHarness.chat 异步函数."""
          self._chat_fn = fn
  
      def _get_agent_profile(self, agent_id: str):
          """从 TeamManager 获取完整 AgentProfile，用于注入个性."""
          try:
              from agents.api import _team_manager
              if _team_manager:
                  for team in _team_manager.list_teams():
                      agent = team.get_agent(agent_id)
                      if agent:
                          return agent
          except Exception:
              pass
          return None
  
      def _build_agent_system_prompt(self, participant: Participant) -> str:
          """根据 AgentProfile 构建有个性的 system prompt."""
          profile = self._get_agent_profile(participant.agent_id)
          if profile:
              expertise = "、".join(profile.personality.expertise_areas) if profile.personality.expertise_areas else ""
              traits = "、".join(profile.metadata.get("traits", [])) if profile.metadata else ""
              parts = [
                  f"你是 {profile.name}，职责: {profile.role}。",
                  f"专长: {expertise}。" if expertise else "",
                  f"性格特质: {traits}。" if traits else "",
                  f"你的工作方式: {profile.system_prompt}" if profile.system_prompt else "",
                  f"\n你正在一个智能体广场的讨论中发言。",
                  f"请用自然的方式说话，像一个真实的专业人士在开会讨论。",
                  f"可以表达观点、提出建议、回应他人，说话要有内容、有依据。",
                  f"不需要客套寒暄，但要说人话，不要像电报一样压缩。",
              ]
              return "".join(p for p in parts if p)
          # 回退到基础信息
          return (
              f"你是 {participant.agent_name}，职责: {participant.role}。"
              f"你正在一个智能体广场的讨论中发言。"
              f"请用自然的方式说话，像一个真实的专业人士在开会讨论。"
              f"可以表达观点、提出建议、回应他人，说话要有内容、有依据。"
          )
  
      # ── 广场 CRUD ──────────────────────────────────────────
  
      def create_plaza(self, name: str, description: str = "") -> Plaza:
          plaza = Plaza(name=name, description=description)
          self._plazas[plaza.id] = plaza
          self._store.save_plaza(plaza)
          logger.info(f"🏛️ 广场创建: {name} ({plaza.id})")
          return plaza
  
      def get_plaza(self, plaza_id: str) -> Optional[Plaza]:
          return self._plazas.get(plaza_id)
  
      def list_plazas(self) -> List[Plaza]:
          return list(self._plazas.values())
  
      def delete_plaza(self, plaza_id: str) -> bool:
          if plaza_id in self._plazas:
              del self._plazas[plaza_id]
              self._store.delete_plaza(plaza_id)
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
          self._store.save_plaza(plaza)
          logger.info(f"🪑 参与者加入广场 {plaza_id}: {agent_name} (壁龛 #{niche_index})")
          return p
  
      def remove_participant(self, plaza_id: str, agent_id: str) -> bool:
          plaza = self._plazas.get(plaza_id)
          if plaza and agent_id in plaza.participants:
              del plaza.participants[agent_id]
              self._store.save_plaza(plaza)
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
          self._store.save_plaza(plaza)
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
  
      def delete_discussion(self, plaza_id: str, discussion_id: str) -> bool:
          plaza = self._plazas.get(plaza_id)
          if not plaza or discussion_id not in plaza.discussions:
              return False
          del plaza.discussions[discussion_id]
          self._sse_queues.pop(discussion_id, None)
          self._store.save_plaza(plaza)
          return True
  
      def reset_discussion(self, plaza_id: str, discussion_id: str) -> Optional[Discussion]:
          """重置已结束讨论，保留话题本身以便重新讨论。"""
          disc = self.get_discussion(plaza_id, discussion_id)
          if not disc:
              return None
          disc.status = DiscussionStatus.OPEN
          disc.current_round = 0
          disc.messages.clear()
          disc.summary = ""
          disc.key_conclusions.clear()
          disc.plan.clear()
          disc.assigned_team_id = ""
          disc.started_at = None
          disc.ended_at = None
          plaza = self._plazas.get(plaza_id)
          if plaza:
              self._store.save_plaza(plaza)
          return disc
  
      # ── SSE 订阅管理 ──────────────────────────────────────
  
      def subscribe(self, discussion_id: str) -> asyncio.Queue:
          q: asynci
  ```
  
  (后续文件因 token 预算已省略)
  
  (后续文件因 token 预算已省略)
  
  
  ## 前序步骤的产出 (递进式摘要)
  
  ### 步骤 01: pm_decompose
  任务: 集成回归杀伤率门禁，要求修复模板在对应契约仿真中复现并杀死同类缺陷方可发布
  步骤: pm_decompose
  📋 任务: 72652523-8a4
  🤖 Agent: PM (project_manager)
  📂 工作目录: /Users/panglaohu/Downloads/AgentsGroup2026
  🔧 执行方式: DeepSeek API (直连)
  ────────────────────────────────────────────────────────────
  你是 AgentsGroup2026 系统的 PM (project_manager)。
  你是项目经理 (PM)。请对以下任务进行分解和规划:
  集成回归杀伤率门禁，要求修复模板在对应契约仿真中复现并杀死同类缺陷方可发布
  Tester + Architect
  ## 📂 项目上下文 (系统自动预加载)
  ### 项目文件结构 (src/ 目录)
  ### 文件: `src/backend/agents/chat_harness.py`
  ### 文件: `src/backend/agents/hermes_research.py`
  **子任务拆解:**
    - *任务**: 集成回归杀伤率门禁，要求修复模板在对应契约仿真中复现并杀死同类缺陷方可发布
    - *角色**: 项目经理 (PM) + Tester + Architect
    - *项目**: AgentsGroup2026 系统
    - **门禁机制**: 在发布流程中增加回归杀伤率检查
    - **修复模板**: 建立缺陷修复模板库
    - **契约仿真**: 构建基于契约的仿真测试环境
    - **同类缺陷检测**: 验证修复能覆盖同类缺陷
    - 后端: Python FastAPI (`src/backend/`)
  
  ### 步骤 02: research (完整产出)
  
  # 研究分析 — researcher
  
  任务: 集成回归杀伤率门禁，要求修复模板在对应契约仿真中复现并杀死同类缺陷方可发布
  步骤: research
  Agent: build_researcher
  
  ---
  
  📋 任务: 72652523-8a4
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
    集成回归杀伤率门禁，要求修复模板在对应契约仿真中复现并杀死同类缺陷方可发布
    Tester + Architect
    
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
    src/docs/agent_handoffs/3bde709e-2fe_executor_started_20260507T031444.md
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
    src/docs/agent_handoffs/65c1db92-524_executor_started_20260507T031444.md
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
    src/docs/agent_handoffs/8665633b-cad_executor_started_20260507T031444.md
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
    ... (共 258 个 src/ 文件)
    
    ```
    
    ### 文件: `src/backend/agents/chat_harness.py`
    ```py
    # -*- coding: utf-8 -*-
    """AgentsGroup2026 Chat Harness — Unified LLM Chat Module.
    
    Inspired by claw-code's QueryEngine + Runtime architecture:
    - Single chat module used by ALL agents, bridge commands, and sessions
    - Provider abstraction: OpenAI-compatible, Anthropic, DeepSeek, local Ollama
    - Session/turn management, token budgeting, transcript compaction
    - Tool invocation pipeline with permission checks
    - Streaming support via SSE-compatible generator
    
    Usage:
        harness = ChatHarness.from_config(config_path="config/settings.json")
        result = await harness.chat(agent_id, prompt, tools=[...])
    
        # Or streaming:
        async for chunk in harness.stream_chat(agent_id, prompt):
            ...
    """
    
    from __future__ import annotations
    
    import json
    import logging
    import os
    import time
    from collections import deque
    from dataclasses import dataclass, field
    from datetime import datetime, timezone
    from enum import Enum
    from pathlib import Path
    from typing import Any, AsyncIterator, Callable, Dict, List, Optional, Tuple
    from uuid import uuid4
    
    from .session_store import (
        StoredSession, TranscriptStore,
        save_session, load_session as _load_stored_session,
        list_sessions as _list_stored_sessions,
        search_sessions,
    )
    from .execution_registry import (
        HistoryLog, ToolPermissionContext, PermissionDenial,
        RoutedMatch, ToolPool, assemble_tool_pool,
        PortRuntime, build_execution_registry,
    )
    
    logger = logging.getLogger(__name__)
    
    
    # ═══════════════════════════════════════════════════════════════
    # UltraPlan — Agentic Planning + Execution Pipeline
    # Inspired by Clawith's plan→act→observe→reflect loop
    # ═══════════════════════════════════════════════════════════════
    
    
    class PlanStepStatus(Enum):
        """Status of a single plan step."""
        PENDING = "pending"
        RUNNING = "running"
        COMPLETED = "completed"
        FAILED = "failed"
        SKIPPED = "skipped"
    
    
    @dataclass
    class PlanStep:
        """A single step in an execution plan."""
        step_id: int = 0
        action: str = ""            # e.g. "tool_call", "think", "respond", "delegate"
        tool_name: str = ""         # Tool to invoke (if action == "tool_call")
        tool_args: Dict[str, Any] = field(default_factory=dict)
        description: str = ""       # Human-readable description
        status: PlanStepStatus = PlanStepStatus.PENDING
        result: str = ""
        error: str = ""
        duration_ms: float = 0.0
        depends_on: List[int] = field(default_factory=list)
    
        def to_dict(self) -> Dict[str, Any]:
            return {
                "step_id": self.step_id,
                "action": self.action,
                "tool_name": self.tool_name,
                "description": self.description,
                "status": self.status.value,
                "result": self.result[:500] if self.result else "",
                "error": self.error,
                "duration_ms": self.duration_ms,
                "depends_on": self.depends_on,
            }
    
    
    @dataclass
    class ExecutionPlan:
        """An ordered plan of steps to fulfill a user request."""
        plan_id: str = field(default_factory=lambda: uuid4().hex[:8])
        goal: str = ""
        steps: List[PlanStep] = field(default_factory=list)
        created_at: str = field(
            default_factory=lambda: datetime.now(timezone.utc).isoformat()
        )
        status: str = "pending"  # pending / running / completed / failed
        final_response: str = ""
    
        def add_step(self, action: str, description: str = "",
                     tool_name: str = "", tool_args: Optional[Dict[str, Any]] = None,
                     depends_on: Optional[List[int]] = None) -> PlanStep:
            step = PlanStep(
                step_id=len(self.steps) + 1,
                action=action,
                tool_name=tool_name,
                tool_args=tool_args or {},
                description=description,
                depends_on=depends_on or [],
            )
            self.steps.append(step)
            return step
    
        @property
        def completed_steps(self) -> int:
            return sum(1 for s in self.steps if s.status == PlanStepStatus.COMPLETED)
    
        @property
        def progress(self) -> float:
            if not self.steps:
                return 1.0
            return self.completed_steps / len(self.steps)
    
        def to_dict(self) -> Dict[str, Any]:
            return {
                "plan_id": self.plan_id,
                "goal": self.goal,
                "status": self.status,
                "steps": [s.to_dict() for s in self.steps],
                "progress": round(self.progress, 2),
                "created_at": self.created_at,
            }
    
    
    # Plan builder: analyzes prompt keywords to auto-generate execution steps
    def build_plan_from_prompt(prompt: str, available_tools: List[str] = None) -> ExecutionPlan:
        """Build an execution plan by analyzing the prompt intent.
    
        This is a rule-based planner that maps keywords to tool invocations.
        When an LLM is available, the plan can be refined by the model.
        """
        plan = ExecutionPlan(goal=prompt[:200])
        lower = prompt.lower()
        tools = set(available_tools or [])
    
        # Multi-domain research
        if any(kw in lower for kw in ["研究", "分析", "调研", "research", "investigate"]):
            plan.add_step("tool_call", "网络搜索相关资料", tool_name="web_search",
                           tool_args={"query": prompt[:100]})
            plan.add_step("think", "整理搜索结果")
            plan.add_step("tool_call", "保存研究发现", tool_name="memory_save",
                           tool_args={"key": f"research_{uuid4().hex[:6]}", "content": ""})
            plan.add_step("respond", "生成研究报告")
    
        # General — single-step
        else:
            plan.add_step("think", "理解用户意图")
            plan.add_step("respond", "生成回复")
    
        return plan
    
    
    # Middleware hook type for plan interception
    PlanMiddleware = Callable[[ExecutionPlan], ExecutionPlan]
    
    
    # ═══════════════════════════════════════════════════════════════
    # Provider Abstraction
    # ═══════════════════════════════════════════════════════════════
    
    
    class LLMProvider(Enum):
        """Supported LLM providers."""
        OPENAI = "openai"
        ANTHROPIC = "anthropic"
        DEEPSEEK = "deepseek"
        OPENROUTER = "openrouter"
        LOCAL = "local"         # Ollama / vLLM / local OpenAI-compatible
        GITHUB = "github"       # GitHub Copilot models
        QWEN = "qwen"
    
    
    @dataclass
    class ProviderConfig:
        """LLM provider connection configuration."""
        provider: LLMProvider = LLMProvider.DEEPSEEK
        api_key: str = ""
        api_base_url: str = ""
        model: str = "deepseek-v4-pro"
        max_tokens: int = 65536  # DeepSeek V4: 64K output
        temperature: float = 0.2
        timeout: float = 1200.0  # Long timeout for big code generations
        thinking: Optional[Dict[str, str]] = None  # e.g. {"type": "enabled"}
        reasoning_effort: str = ""  # "low" | "medium" | "high"
    
        # Default endpoints per provider
        _DEFAULT_URLS: dict = field(default_factory=lambda: {
            LLMProvider.OPENAI: "https://api.openai.com/v1",
            LLMProvider.ANTHROPIC: "https://api.anthropic.com/v1",
            LLMProvider.DEEPSEEK: "https://api.deepseek.com",
            LLMProvider.OPENROUTER: "https://openrouter.ai/api/v1",
            LLMProvider.LOCAL: "http://127.0.0.1:11434/v1",
            LLMProvider.GITHUB: "https://models.inference.ai.azure.com",
            LLMProvider.QWEN: "https://dashscope.aliyuncs.com/compatible-mode/v1",
        }, repr=False)
    
        def resolve_base_url(self) -> str:
            if self.api_base_url:
                return self.api_base_url.rstrip("/")
            return self._DEFAULT_URLS.get(self.provider, "http://127.0.0.1:11434/v1")
    
        @classmethod
        def from_env(cls) -> "ProviderConfig":
            """Build config from environment variables."""
            provider_str = os.getenv("AG_LLM_PROVIDER", "deepseek")
            try:
                provider = LLMProvider(provider_str)
            except ValueError:
                provider = LLMProvider.DEEPSEEK
    
            return cls(
                provider=provider,
                api_key=os.getenv("AG_LLM_API_KEY", os.getenv("DEEPSEEK_API_KEY", "")),
                api_base_url=os.getenv("AG_LLM_BASE_URL", ""),
                model=os.getenv("AG_LLM_MODEL", "deepseek-v4-pro"),
                max_tokens=int(os.getenv("AG_LLM_MAX_TOKENS", "65536")),
                temperature=float(os.getenv("AG_LLM_TEMPERATURE", "0.2")),
                thinking={"type": "enabled"},
                reasoning_effort="high",
            )
    
        @classmethod
        def from_settings(cls, settings: Dict[str, Any]) -> "ProviderConfig":
            """Build from config/settings.json llm section."""
            llm = settings.get("llm", {})
            provider_str = llm.get("provider", "local")
            try:
                provider = LLMProvider(provider_str)
            except ValueError:
                provider = LLMProvider.LOCAL
    
            return cls(
                provider=provider,
                api_key=llm.get("api_key", os.getenv("DEEPSEEK_API_KEY", "")),
                api_base_url=llm.get("local", llm.get("api_base_url", "")),
                model=llm.get("model", "deepseek-v4-pro"),
                max_tokens=llm.get("max_tokens", 65536),
                temperature=llm.get("temperature", 0.2),
                thinking=llm.get("thinking"),
                reasoning_effort=llm.get("reasoning_effort", ""),
            )
    
        @classmethod
        def from_model_config(cls, model_config: Any) -> "ProviderConfig":
            """Build from agents.models.ModelConfig."""
            provider_str = getattr(model_config, "provider", "deepseek")
            try:
                provider = LLMProvider(provider_str)
            except ValueError:
                provider = LLMProvider.DEEPSEEK
    
            return cls(
                provider=provider,
                api_key=getattr(model_config, "api_key", ""),
                api_base_url=getattr(model_config, "api_base_url", ""),
                model=getattr(model_config, "name", "deepseek-v4-pro"),
                max_tokens=getattr(model_config, "max_tokens", 65536),
                temperature=getattr(model_config, "temperature", 0.2),
                thinking={"type": "enabled"},
                reasoning_effort="high",
            )
    
    
    # ═══════════════════════════════════════════════════════════════
    # Turn / Session Data Models
    # ═══════════════════════════════════════════════════════════════
    
    
    @dataclass
    class UsageSummary:
        """Token usage tracking (mirrors claw-code UsageSummary)."""
        input_tokens: int = 0
        output_tokens: int = 0
        total_tokens: int = 0
    
        def add(self, inp: int, out: int) -> "UsageSummary":
            return UsageSummary(
                input_tokens=self.input_tokens + inp,
                output_tokens=self.output_tokens + out,
                total_tokens=self.total_tokens + inp + out,
            )
    
        def to_dict(self) -> Dict[str, int]:
            return {
                "input_tokens": self.input_tokens,
                "output_tokens": self.output_tokens,
                "total_tokens": self.total_tokens,
            }
    
    
    @dataclass
    class ToolInvocation:
        """A tool call extracted from the LLM response."""
        tool_name: str = ""
        arguments: Dict[str, Any] = field(default_factory=dict)
        result: str = ""
        permitted: bool = True
        denial_reason: str = ""
    
        def to_dict(self) -> Dict[str, Any]:
            return {
                "tool_name": self.tool_name,
                "arguments": self.arguments,
                "result": self.result,
                "permitted": self.permitted,
                "denial_reason": self.denial_reason,
            }
    
    
    @dataclass
    class TurnResult:
        """Result of a single chat turn (mirrors claw-code TurnResult)."""
        prompt: str = ""
        response: str = ""
        usage: UsageSummary = field(default_factory=UsageSummary)
        tool_invocations: List[ToolInvocation] = field(default_factory=list)
        stop_reason: str = "completed"
        model: str = ""
        provider: str = ""
        latency_ms: float = 0.0
        error: str = ""
        timestamp: str = field(
            default_factory=lambda: datetime.now(timezone.utc).isoformat()
        )
    
        def to_dict(self) -> Dict[str, Any]:
            return {
                "prompt": self.prompt,
                "response": self.response,
                "usage": self.usage.to_dict(),
                "tool_invocations": [t.to_dict() for t in self.tool_invocations],
                "stop_reason": self.stop_reason,
                "model": self.model,
                "provider": self.provider,
                "latency_ms": self.latency_ms,
                "error": self.error,
                "timestamp": self.timestamp,
            }
    
    
    @dataclass
    class ChatMessage:
        """A single message in a conversation."""
        role: str = "user"  # user | assistant | system | tool
        content: str = ""
        name: str = ""
        tool_calls: List[Dict[str, Any]] = field(default_factory=list)
        timestamp: str = field(
            default_factory=lambda: datetime.now(timezone.utc).isoformat()
        )
    
        def to_openai_dict(self) -> Dict[str, Any]:
            d: Dict[str, Any] = {"role": self.role, "content": self.content}
            if self.name:
                d["name"] = self.name
            return d
    
    
    @dataclass
    class ChatSession:
        """Stateful conversation session with compaction, history & transcript.
    
        Integrates claw-code-parity patterns:
        - HistoryLog for event tracking
        - TranscriptStore for persistence & replay
        - Permission tracking
        """
        session_id: str = field(default_factory=lambda: uuid4().hex[:12])
        agent_id: str = ""
        system_prompt: str = ""
        messages: List[ChatMessage] = field(default_factory=list)
        total_usage: UsageSummary = field(default_factory=UsageSummary)
        turn_count: int = 0
        created_at: str = field(
            default_factory=lambda: datetime.now(timezone.utc).isoformat()
        )
        max_turns: int = 100
        compact_after: int = 40
        # claw-code-parity extensions
        history: HistoryLog = field(default_factory=HistoryLog)
        transcript: TranscriptStore = field(default_factory=TranscriptStore)
        permission_denials: List[PermissionDenial] = field(default_factory=list)
    
        def add_user_message(self, content: str) -> None:
            self.messages.append(ChatMessage(role="user", content=content))
            self.transcript.append(content)
            self.history.add("user_message", content[:100])
    
        def add_assistant_message(self, content: str) -> None:
            self.messages.append(ChatMessage(role="assistant", content=content))
            self.turn_count += 1
            self.transcript.append(content)
            self.history.add("assistant_message", f"turn={self.turn_count}")
    
        def compact_if_needed(self) -> None:
            """Keep conversation manageable by dropping old turns."""
            if len(self.messages) > self.compact_after:
                # Keep system prompt context (first msg if system) + last N messages
                keep = self.compact_after // 2
                sys_msgs = [m for m in self.messages[:1] if m.role == "system"]
                self.messages = sys_msgs + self.messages[-keep:]
    
        def build_openai_messages(self) -> List[Dict[str, Any]]:
            """Build the messages array for OpenAI-compatible API calls."""
            msgs = []
            if self.system_prompt:
                msgs.append({"role": "system", "content": self.system_prompt})
            msgs.extend(m.to_openai_dict() for m in self.messages)
            return msgs
    
        def persist(self) -> str:
          
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

# 回归杀伤率门禁系统 — 技术方案设计

## 1. 架构概览

### 1.1 核心概念

```
┌─────────────────────────────────────────────────────────────┐
│                    回归杀伤率门禁系统                          │
├───��─────────────────────────────────────────────────────────┤
│                                                             │
│  修复模板库 ──→ 契约仿真引擎 ──→ 杀伤率评估 ──→ 门禁决策      │
│  (FixTemplate)   (ContractSim)   (KillRate)   (GateCheck)   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 关键定义

- **修复模板 (FixTemplate)**: 针对特定缺陷类型的标准化修复方案，包含修复代码、验证条件和同类缺陷特征
- **契约仿真 (ContractSim)**: 基于契约(Contract)的测试环境，模拟缺陷复现和修复验证
- **杀伤率 (KillRate)**: 修复模板在契约仿真中成功杀死同类缺陷的比例
- **门禁 (Gate)**: 发布流程中的质量检查点，杀伤率达标方可发布

## 2. 数据模型设计

### 2.1 新增文件: `src/backend/agents/regression_gate.py`

```python
# -*- coding: utf-8 -*-
"""回归杀伤率门禁系统 — 修复模板、契约仿真、杀伤率评估与门禁决策。

核心流程:
1. 缺陷修复后，创建修复模板 (FixTemplate)
2. 在契约仿真中复现缺陷 (ContractSim)
3. 验证修复能杀死同类缺陷 (KillRate)
4. 杀伤率达标后门禁放行 (GateCheck)
"""

from __future__ import annotations

import json
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Set

logger = logging.getLogger(__name__)


# ── 枚举 ──────────────────────────────────────────────────────

class DefectCategory(Enum):
    """缺陷分类 — 用于同类缺陷匹配。"""
    NULL_POINTER = "null_pointer"
    INDEX_OUT_OF_BOUNDS = "index_out_of_bounds"
    TYPE_MISMATCH = "type_mismatch"
    RACE_CONDITION = "race_condition"
    MEMORY_LEAK = "memory_leak"
    SQL_INJECTION = "sql_injection"
    XSS = "xss"
    AUTH_BYPASS = "auth_bypass"
    LOGIC_ERROR = "logic_error"
    CONFIG_ERROR = "config_error"
    API_MISUSE = "api_misuse"
    DATA_CORRUPTION = "data_corruption"
    TIMEOUT = "timeout"
    RESOURCE_EXHAUSTION = "resource_exhaustion"
    CUSTOM = "custom"


class GateStatus(Enum):
    """门禁状态。"""
    PENDING = "pending"          # 待评估
    PASSED = "passed"            # 通过
    FAILED = "failed"            # 未通过
    BLOCKED = "blocked"          # 阻塞（需要人工干预）
    BYPASSED = "bypassed"        # 绕过（管理员授权）


class SimResult(Enum):
    """仿真结果。"""
    KILLED = "killed"            # 修复成功杀死缺陷
    SURVIVED = "survived"        # 缺陷存活
    FALSE_POSITIVE = "false_positive"  # 误报
    ERROR = "error"              # 仿真执行错误


# ── 数据模型 ──────────────────────────────────────────────────

@dataclass
class DefectSignature:
    """缺陷特征签名 — 用于同类缺陷匹配。"""
    category: DefectCategory = DefectCategory.CUSTOM
    pattern: str = ""            # 缺陷模式（正则或AST模式）
    trigger_condition: str = ""  # 触发条件描述
    affected_component: str = "" # 受影响组件
    severity: str = "medium"     # 严重程度
    tags: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "category": self.category.value,
            "pattern": self.pattern,
            "trigger_condition": self.trigger_condition,
            "affected_component": self.affected_component,
            "severity": self.severity,
            "tags": self.tags,
        }


@dataclass
class FixTemplate:
    """修复模板 — 标准化修复方案。"""
    template_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    name: str = ""
    description: str = ""
    defect_signature: DefectSignature = field(default_factory=DefectSignature)
    
    # 修复代码
    fix_code: str = ""           # 修复后的代码
    original_code: str = ""      # 原始有缺陷的代码
    diff: str = ""               # 差异补丁
    
    # 验证条件
    validation_conditions: List[str] = field(default_factory=list)
    
    # 同类缺陷特征
    similar_defect_patterns: List[str] = field(default_factory=list)
    
    # 元数据
    created_by: str = ""         # 创建者 agent_id
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    version: int = 1
    tags: List[str] = field(default_factory=list)
    
    # 统计
    total_simulations: int = 0
    successful_kills: int = 0
    kill_rate: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "template_id": self.template_id,
            "name": self.name,
            "description": self.description,
            "defect_signature": self.defect_signature.to_dict(),
            "fix_code": self.fix_code[:200] + "..." if len(self.fix_code) > 200 else self.fix_code,
            "diff": self.diff[:200] + "..." if len(self.diff) > 200 else self.diff,
            "validation_conditions": self.validation_conditions,
            "similar_defect_patterns": self.similar_defect_patterns,
            "created_by": self.created_by,
            "created_at": self.created_at,
            "version": self.version,
            "tags": self.tags,
            "total_simulations": self.total_simulations,
            "successful_kills": self.successful_kills,
            "kill_rate": round(self.kill_rate, 4),
        }


@dataclass
class ContractSimulation:
    """契约仿真 — 在契约环境中复现和验证缺陷修复。"""
    sim_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    template_id: str = ""
    
    # 契约定义
    contract_name: str = ""
    contract_version: str = "1.0"
    contract_code: str = ""      # 契约代码（测试用例）
    
    # 仿真配置
    input_variations: List[Dict[str, Any]] = field(default_factory=list)
    mutation_strategy: str = "random"  # random | systematic | boundary
    
    # 仿真结果
    results: List[SimResult] = field(default_factory=list)
    total_tests: int = 0
    killed_count: int = 0
    survived_count: int = 0
    
    # 状态
    status: str = "pending"      # pending | running | completed | failed
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    error_message: str = ""
    
    # 元数据
    created_by: str = ""
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "sim_id": self.sim_id,
            "template_id": self.template_id,
            "contract_name": self.contract_name,
            "contract_version": self.contract_version,
            "input_variations": self.input_variations[:5],
            "mutation_strategy": self.mutation_strategy,
            "results": [r.value for r in self.results],
            "total_tests": self.total_tests,
            "killed_count": self.killed_count,
            "survived_count": self.survived_count,
            "status": self.status,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "error_message": self.error_message,
            "created_by": self.created_by,
            "created_at": self.created_at,
        }


@dataclass
class GateCheck:
    """门禁检查 — 发布流程中的质量检查点。"""
    gate_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    template_id: str = ""
    
    # 门禁配置
    min_kill_rate: float = 0.8   # 最低杀伤率（80%）
    required_simulations: int = 10  # 最少仿真次数
    allow_bypass: bool = False
    
    # 检查结果
    status: GateStatus = GateStatus.PENDING
    current_kill_rate: float = 0.0
    total_simulations: int = 0
    passed_simulations: int = 0
    
    # 决策信息
    checked_by: str = ""         # 检查者 agent_id
    checked_at: Optional[str] = None
    bypass_reason: str = ""
    bypassed_by: str = ""
    
    # 关联
    related_sim_ids: List[str] = field(default_factory=list)
    
    # 元数据
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "gate_id": self.gate_id,
            "template_id": self.template_id,
            "min_kill_rate": self.min_kill_rate,
            "required_simulations": self.required_simulations,
            "allow_bypass": self.allow_bypass,
            "status": self.status.value,
            "current_kill_rate": round(self.current_kill_rate, 4),
            "total_simulations": self.total_simulations,
            "passed_simulations": self.passed_simulations,
            "checked_by": self.checked_by,
            "checked_at": self.checked_at,
            "bypass_reason": self.bypass_reason,
            "bypassed_by": self.bypassed_by,
            "related_sim_ids": self.related_sim_ids,
            "created_at": self.created_at,
        }


# ── 存储 ──────────────────────────────────────────────────────

class RegressionGateStore:
    """回归门禁存储 — 管理修复模板、仿真和门禁检查的持久化。"""
    
    def __init__(self, storage_path: str = "data/regression_gate/"):
        self._storage_path = storage_path
        self._templates: Dict[str, FixTemplate] = {}
        self._simulations: Dict[str, ContractSimulation] = {}
        self._gates: Dict[str, GateCheck] = {}
        self._load_all()
    
    def _load_all(self) -> None:
        """从持久化存储加载所有数据。"""
        import os
        import json
        
        os.makedirs(self._storage_path, exist_ok=True)
        
        # 加载修复模板
        templates_file = os.path.join(self._storage_path, "templates.json")
        if os.path.exists(templates_file):
            try:
                with open(templates_file, "r") as f:
                    data = json.load(f)
                    for item in data:
                        template = FixTemplate(**item)
                        self._templates[template.template_id] = template
            except Exception as e:
                logger.error(f"加载修复模板失败: {e}")
        
        # 加载仿真记录
        sims_file = os.path.join(self._storage_path, "simulations.json")
        if os.path.exists(sims_file):
            try:
                with open(sims_file, "r") as f:
                    data = json.load(f)
                    for item in data:
                        sim = ContractSimulation(**item)
                        self._simulations[sim.sim_id] = sim
            except Exception as e:
                logger.error(f"加载仿真记录失败: {e}")
        
        # 加载门禁检查
        gates_file = os.path.join(self._storage_path, "gates.json")
        if os.path.exists(gates_file):
            try:
                with open(gates_file, "r") as f:
                    data = json.load(f)
                    for item in data:
                        gate = GateCheck(**item)
                        self._gates[gate.gate_id] = gate
            except Exception as e:
                logger.error(f"加载门禁检查失败: {e}")
    
    def _save_templates(self) -> None:
        """持久化修复模板。"""
        import os
        import json
        
        os.makedirs(self._storage_path, exist_ok=True)
        templates_file = os.path.join(self._storage_path, "templates.json")
        try:
            with open(templates_file, "w") as f:
                json.dump(
                    [t.to_dict() for t in self._templates.values()],
                    f, ensure_ascii=False, indent=2
                )
        except Exception as e:
            logger.error(f"保存修复模板失败: {e}")
    
    def _save_simulations(self) -> None:
        """持久化仿真记录。"""
        import os
        import json
        
        os.makedirs(self._storage_path, exist_ok=True)
        sims_file = os.path.join(self._storage_path, "simulations.json")
        try:
            with open(sims_file, "w") as f:
                json.dump(
                    [s.to_dict() for s in self._simulations.values()],
                    f, ensure_ascii=False, indent=2
                )
        except Exception as e:
            logger.error(f"保存仿真记录失败: {e}")
    
    def _save_gates(self) -> None:
        """持久化门禁检查。"""
        import os
        import json
        
        os.makedirs(self._storage_path, exist_ok=True)
        gates_file = os.path.join(self._storage_path, "gates.json")
        try:
            with open(gates_file, "w") as f:
                json.dump(
                    [g.to_dict() for g in self._gates.values()],
                    f, ensure_ascii=False, indent=2
                )
        except Exception as e:
            logger.error(f"保存门禁检查失败: {e}")
    
    # ── 修复模板 CRUD ──
    
    def save_template(self, template: FixTemplate) -> None:
        self._templates[template.template_id] = template
        self._save_templates()
    
    def get_template(self, template_id: str) -> Optional[FixTemplate]:
        return self._templates.get(template_id)
    
    def list_templates(self, category: Optional[DefectCategory] = None) -> List[FixTemplate]:
        if category:
            return [
                t for t in self._templates.values()
                if t.defect_signature.category == category
            ]
        return list(self._templates.values())
    
    def delete_template(self, template_id: str) -> bool:
        if template_id in self._templates:
            del self._templates[template_id]
            self._save_templates()
            return True
        return False
    
    # ── 仿真 CRUD ──
    
    def save_simulation(self, sim: ContractSimulation) -> None:
        self._simulations[sim.sim_id] = sim
        self._save_simulations()
    
    def get_simulation(self, sim_id: str) -> Optional[ContractSimulation]:
        return self._simulations.get(sim_id)
    
    def list_simulations(self, template_id: Optional[str] = None) -> List[ContractSimulation]:
        if template_id:
            return [
                s for s in self._simulations.values()
                if s.template_id == template_id
            ]
        return list(self._simulations.values())
    
    # ── 门禁检查 CRUD ──
    
    def save_gate(self, gate: GateCheck) -> None:
        self._gates[gate.gate_id] = gate
        self._save_gates()
    
    def get_gate(self, gate_id: str) -> Optional[GateCheck]:
        return self._gates.get(gate_id)
    
    def list_gates(self, template_id: Optional[str] = None) -> List[GateCheck]:
        if template_id:
            return [
                g for g in self._gates.values()
                if g.template_id == template_id
            ]
        return list(self._gates.values())
    
    def get_gate_by_template(self, template_id: str) -> Optional[GateCheck]:
        """获取指定修复模板的最新门禁检查。"""
        gates = [g for g in self._gates.values() if g.template_id == template_id]
        if not gates:
            return None
        return max(gates, key=lambda g: g.created_at)
```

### 2.2 修改文件: `src/backend/agents/models.py`

在 `AgentProfile` 类中添加门禁相关字段：

```python
@dataclass
class AgentProfile:
    """Individual agent profile — the Employee equivalent."""
    
    # ... 现有字段 ...
    
    # 回归门禁相关
    regression_gate_enabled: bool = False  # 是否启用回归门禁
    min_kill_rate: float = 0.8             # 最低杀伤率要求
    required_simulations: int = 10         # 最少仿真次数
```

## 3. 核心引擎设计

### 3.1 修复模板引擎

```python
class FixTemplateEngine:
    """修复模板引擎 — 创建、管理和匹配修复模板。"""
    
    def __init__(self, store: RegressionGateStore):
        self._store = store
    
    async def create_template(
        self,
        name: str,
        description: str,
        original_code: str,
        fix_code: str,
        defect_signature: DefectSignature,
        created_by: str = "",
    ) -> FixTemplate:
        """创建修复模板。"""
        # 生成差异补丁
        diff = self._generate_diff(original_code, fix_code)
        
        # 提取同类缺陷模式
        similar_patterns = self._extract_similar_patterns(defect_signature)
        
        template = FixTemplate(
            name=name,
            description=description,
            defect_signature=defect_signature,
            fix_code=fix_code,
            original_code=original_code,
            diff=diff,
            similar_defect_patterns=similar_patterns,
            created_by=created_by,
        )
        
        self._store.save_template(template)
        logger.info(f"修复模板创建: {template.template_id} - {name}")
        return template
    
    def _generate_diff(self, original: str, fixed: str) -> str:
        """生成代码差异补丁。"""
        import difflib
        diff = difflib.unified_diff(
            original.splitlines(keepends=True),
            fixed.splitlines(keepends=True),
            fromfile="original",
            tofile="fixed",
        )
        return "".join(diff)
    
    def _extract_similar_patterns(self, signature: DefectSignature) -> List[str]:
        """从缺陷特征提取同类缺陷模式。"""
        patterns = []
        
        # 基于缺陷分类生成模式
        category_patterns = {
            DefectCategory.NULL_POINTER: [
                "None check missing",
                "null dereference",
                "optional unwrap without check",
            ],
            DefectCategory.INDEX_OUT_OF_BOUNDS: [
                "array access without bounds check",
                "list index without length check",
            ],
            DefectCategory.TYPE_MISMATCH: [
                "type coercion without validation",
                "unsafe type cast",
            ],
            DefectCategory.RACE_CONDITION: [
                "shared state without lock",
                "concurrent access without synchronization",
            ],
        }
        
        patterns.extend(category_patterns.get(signature.category, []))
        
        # 基于标签生成模式
        for tag in signature.tags:
            patterns.append(f"pattern:{tag}")
        
        return patterns
    
    def find_similar_templates(
        self,
        defect_signature: DefectSignature,
        threshold: float = 0.6,
    ) -> List[FixTemplate]:
        """查找与缺陷特征相似的修复模板。"""
        similar = []
        
        for template in self._store.list_templates():
            similarity = self._calculate_similarity(
                defect_signature, template.defect_signature
            )
            if similarity >= threshold:
                similar.append((template, similarity))
        
        # 按相似度排序
        similar.sort(key=lambda x: x[1], reverse=True)
        return [t for t, _ in similar]
    
    def _calculate_similarity(
        self,
        sig1: DefectSignature,
        sig2: DefectSignature,
    ) -> float:
        """计算两个缺陷特征的相似度。"""
        score = 0.0
        
        # 分类匹配
        if sig1.category == sig2.category:
            score += 0.4
        
        # 组件匹配
        if sig1.affected_component == sig2.affected_component:
            score += 0.2
        
        # 标签匹配
        common_tags = set(sig1.tags) & set(sig2.tags)
        if sig1.tags or sig2.tags:
            score += 0.2 * len(common_tags) / max(len(set(sig1.tags + sig2.tags)), 1)
        
        # 模式匹配
        if sig1.pattern and sig2.pattern:
            import difflib
            score += 0.2 * difflib.SequenceMatcher(
                None, sig1.pattern, sig2.pattern
            ).ratio()
        
        return min(score, 1.0)
```

### 3.2 契约仿真引擎

```python
class ContractSimEngine:
    """契约仿真引擎 — 在契约环境中复现和验证缺陷修复。"""
    
    def __init__(self, store: RegressionGateStore):
        self._store = store
    
    async def run_simulation(
        self,
        template: FixTemplate,
        contract_name: str = "",
        mutation_strategy: str = "random",
        num_variations: int = 10,
    ) -> ContractSimulation:
        """运行契约仿真。"""
        sim = ContractSimulation(
            template_id=template.template_id,
            contract_name=contract_name or f"sim_{template.name}",
            mutation_strategy=mutation_strategy,
            created_by=template.created_by,
        )
        
        # 生成输入变体
        variations = self._generate_input_variations(
            template, num_variations, mutation_strategy
        )
        sim.input_variations = variations
        
        # 执行仿真
        sim.status = "running"
        sim.started_at = datetime.now(timezone.utc).isoformat()
        self._store.save_simulation(sim)
        
        try:
            for variation in variations:
                result = await self._execute_single_test(template, variation)
                sim.results.append(result)
                sim.total_tests += 1
                
                if result == SimResult.KILLED:
                    sim.killed_count += 1
                elif result == SimResult.SURVIVED:
                    sim.survived_count += 1
            
            sim.status = "completed"
            sim.completed_at = datetime.now(timezone.utc).isoformat()
            
            # 更新模板统计
            template.total_simulations += sim.total_tests
            template.successful_kills += sim.killed_count
            template.kill_rate = (
                template.successful_kills / template.total_simulations
                if template.total_simulations > 0 else 0.0
            )
            self._store.save_template(template)
            
        except Exception as e:
            sim.status = "failed"
            sim.error_message = str(e)
            logger.error(f"仿真执行失败: {e}")
        
        self._store.save_simulation(sim)
        return sim
    
    def _generate_input_variations(
        self,
        template: FixTemplate,
        count: int,
        strategy: str,
    ) -> List[Dict[str, Any]]:
        """生成输入变体用于仿真测试。"""
        variations = []
        
        if strategy == "random":
            variations = self._generate_random_variations(template, count)
        elif strategy == "systematic":
            variations = self._generate_systematic_variations(template, count)
        elif strategy == "boundary":
            variations = self._generate_boundary_variations(template, count)
        
        return variations[:count]
    
    def _generate_random_variations(
        self,
        template: FixTemplate,
        count: int,
    ) -> List[Dict[str, Any]]:
        """生成随机输入变体。"""
        import random
        
        variations = []
        patterns = template.similar_defect_patterns
        
        for i in range(count):
            variation = {
                "variation_id": i,
                "type": "random",
                "pattern": random.choice(patterns) if patterns else "generic",
                "input": {
                    "value": random.randint(-100, 100),
                    "is_null": random.random() < 0.3,
                    "is_empty": random.random() < 0.2,
                    "is_malformed": random.random() < 0.1,
                }
            }
            variations.append(variation)
        
        return variations
    
    def _generate_systematic_variations(
        self,
        template: FixTemplate,
        count: int,
    ) -> List[Dict[str, Any]]:
        """生成系统化输入变体。"""
        variations = []
        
        # 基于缺陷分类生成系统化变体
        systematic_cases = {
            DefectCategory.NULL_POINTER: [
                {"value": None, "description": "直接传入None"},
                {"value": "", "description": "空字符串"},
                {"value": [], "description": "空列表"},
                {"value": {}, "description": "空字典"},
                {"value": 0, "description": "零值"},
            ],
            DefectCategory.INDEX_OUT_OF_BOUNDS: [
                {"index": -1, "description": "负索引"},
                {"index": 100, "description": "超出范围索引"},
                {"index": 0, "description": "边界索引"},
                {"length": 0, "description": "空序列"},
            ],
        }
        
        cases = systematic_cases.get(
            template.defect_signature.category,
            [{"value": None, "description": "默认测试"}]
        )
        
        for i, case in enumerate(cases[:count]):
            variation = {
                "variation_id": i,
                "type": "systematic",
                "pattern": case.get("description", ""),
                "input": case,
            }
            variations.append(variation)
        
        return variations
    
    def _generate_boundary_variations(
        self,
        template: FixTemplate,
        count: int,
    ) -> List[Dict[str, Any]]:
        """生成边界值变体。"""
        variations = []
        
        boundary_cases = [
            {"value": None, "type": "null"},
            {"value": "", "type": "empty"},
            {"value": 0, "type": "zero"},
            {"value": -1, "type": "negative_one"},
            {"value": 1, "type": "positive_one"},
            {"value": float('inf'), "type": "infinity"},
            {"value": float('-inf'), "type": "negative_infinity"},
            {"value": float('nan'), "type": "nan"},
        ]
        
        for i, case in enumerate(boundary_cases[:count]):
            variation = {
                "variation_id": i,
                "type": "boundary",
                "pattern": f"boundary_{case['type']}",
                "input": case,
            }
            variations.append(variation)
        
        return variations
    
    async def _execute_single_test(
        self,
        template: FixTemplate,
        variation: Dict[str, Any],
    ) -> SimResult:
        """执行单个测试用例。"""
        try:
            # 这里应该调用实际的代码执行引擎
            # 目前使用模拟逻辑
            
            # 检查修复代码是否能处理该变体
            if self._check_fix_handles_variation(template, variation):
                return SimResult.KILLED
            else:
                return SimResult.SURVIVED
                
        except Exception as e:
            logger.error(f"测试执行失败: {e}")
            return SimResult.ERROR
    
    def _check_fix_handles_variation(
        self,
        template: FixTemplate,
        variation: Dict[str, Any],
    ) -> bool:
        """检查修��代码是否能处理特定变体。"""
        # 模拟检查逻辑
        # 实际实现应调用代码分析引擎
        
        input_data = variation.get("input", {})
        
        # 检查空值处理
        if input_data.get("is_null") or input_data.get("value") is None:
            return "None" not in template.original_code and "None" in template.fix_code
        
        # 检查边界值处理
        if input_data.get("type") in ["zero", "negative_one"]:
            return True
        
        return True
```

### 3.3 杀伤率评估引擎

```python
class KillRateEvaluator:
    """杀伤率评估引擎 — 计算和评估修复模板的杀伤率。"""
    
    def __init__(self, store: RegressionGateStore):
        self._store = store
    
    def calculate_kill_rate(self, template_id: str) -> float:
        """计算修复模板的杀伤率。"""
        template = self._store.get_template(template_id)
        if not template:
            return 0.0
        
        if template.total_simulations == 0:
            return 0.0
        
        return template.successful_kills / template.total_simulations
    
    def evaluate_kill_rate(
        self,
        template_id: str,
        min_rate: float = 0.8,
        min_simulations: int = 10,
    ) -> Dict[str, Any]:
        """评估杀伤率是否达标。"""
        template = self._store.get_template(template_id)
        if not template:
            return {
                "passed": False,
                "reason": "修复模板不存在",
                "kill_rate": 0.0,
                "total_simulations": 0,
            }
        
        kill_rate = self.calculate_kill_rate(template_id)
        
        result = {
            "kill_rate": round(kill_rate, 4),
            "total_simulations": template.total_simulations,
            "required_rate": min_rate,
            "required_simulations": min_simulations,
        }
        
        if template.total_simulations < min_simulations:
            result["passed"] = False
            result["reason"] = (
                f"仿真次数不足: {template.total_simulations}/{min_simulations}"
            )
        elif kill_rate < min_rate:
            result["passed"] = False
            result["reason"] = (
                f"杀伤率不足: {kill_rate:.2%}/{min_rate:.0%}"
            )
        else:
            result["passed"] = True
            result["reason"] = "杀伤率达标"
        
        return result
    
    def get_kill_rate_history(
        self,
        template_id: str,
    ) -> List[Dict[str, Any]]:
        """获取杀伤率历史变化。"""
        simulations = self._store.list_simulations(template_id)
        
        history = []
        cumulative_kills = 0
        cumulative_tests = 0
        
        for sim in sorted(simulations, key=lambda s: s.created_at):
            cumulative_kills += sim.killed_count
            cumulative_tests += sim.total_tests
            
            history.append({
                "sim_id": sim.sim_id,
                "timestamp": sim.completed_at or sim.created_at,
                "tests_in_round": sim.total_tests,
                "kills_in_round": sim.killed_count,
                "cumulative_kills": cumulative_kills,
                "cumulative_tests": cumulative_tests,
                "cumulative_kill_rate": (
                    cumulative_kills / cumulative_tests
                    if cumulative_tests > 0 else 0.0
                ),
            })
        
        return history
```

### 3.4 门禁决策引擎

```python
class GateDecisionEngine:
    """门禁决策引擎 — 根据杀伤率评估结果做出门禁决策。"""
    
    def __init__(self, store: RegressionGateStore):
        self._store = store
        self._evaluator = KillRateEvaluator(store)
    
    async def check_gate(
        self,
        template_id: str,
        min_kill_rate: float = 0.8,
        required_simulations: int = 10,
        checked_by: str = "",
    ) -> GateCheck:
        """执行门禁检查。"""
        gate = GateCheck(
            template_id=template_id,
            min_kill_rate=min_kill_rate,
            required_simulations=required_simulations,
            checked_by=checked_by,
        )
        
        # 获取评估结果
        evaluation = self._evaluator.evaluate_kill_rate(
            template_id, min_kill_rate, required_simulations
        )
        
        gate.current_kill_rate = evaluation["kill_rate"]
        gate.total_simulations = evaluation["total_simulations"]
        gate.passed_simulations = evaluation["total_simulations"]
        
        # 关联仿真记录
        simulations = self._store.list_simulations(template_id)
        gate.related_sim_ids = [s.sim_id for s in simulations]
        
        # 做出决策
        if evaluation["passed"]:
            gate.status = GateStatus.PASSED
        else:
            gate.status = GateStatus.FAILED
        
        gate.checked_at = datetime.now(timezone.utc).isoformat()
        
        self._store.save_gate(gate)
        logger.info(
            f"门禁检查: {gate.gate_id} - "
            f"杀伤率={gate.current_kill_rate:.2%}, "
            f"状态={gate.status.value}"
        )
        
        return gate
    
    def bypass_gate(
        self,
        gate_id: str,
        bypassed_by: str,
        reason: str,
    ) -> Optional[GateCheck]:
        """绕过门禁（管理员授权）。"""
        gate = self._store.get_gate(gate_id)
        if not gate:
            return None
        
        gate.status = GateStatus.BYPASSED
        gate.bypassed_by = bypassed_by
        gate.bypass_reason = reason
        
        self._store.save_gate(gate)
        logger.warning(
            f"门禁绕过: {gate_id} - 操作者={bypassed_by}, 原因={reason}"
        )
        
        return gate
    
    def get_gate_status_summary(
        self,
        template_id: str,
    ) -> Dict[str, Any]:
        """获取门禁状态摘要。"""
        gate = self._store.get_gate_by_template(template_id)
        template = self._store.get_template(template_id)
        
        if not gate:
            return {
                "template_id": template_id,
                "template_name": template.name if template else "未知",
                "status": "not_checked",
                "message": "尚未进行门禁检查",
            }
        
        return {
            "template_id": template_id,
            "template_name": template.name if template else "未知",
            "gate_id": gate.gate_id,
            "status": gate.status.value,
            "kill_rate": gate.current_kill_rate,
            "total_simulations": gate.total_simulations,
            "checked_at": gate.checked_at,
            "checked_by": gate.checked_by,
            "can_bypass": gate.allow_bypass,
        }
```

## 4. API 接口设计

### 4.1 新增文件: `src/backend/agents/regression_gate_routes.py`

```python
# -*- coding: utf-8 -*-
"""回归杀伤率门禁 API 路由。"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query

from .regression_gate import (
    RegressionGateStore,
    FixTemplateEngine,
    ContractSimEngine,
    KillRateEvaluator,
    GateDecisionEngine,
    FixTemplate,
    DefectSignature,
    DefectCategory,
    GateStatus,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/regression-gate", tags=["regression-gate"])

# 全局实例
_store = RegressionGateStore()
_template_engine = FixTemplateEngine(_store)
_sim_engine = ContractSimEngine(_store)
_evaluator = KillRateEvaluator(_store)
_gate_engine = GateDecisionEngine(_store)


# ── 修复模板 API ──

@router.post("/templates")
async def create_template(
    name: str,
    description: str,
    original_code: str,
    fix_code: str,
    category: str = "custom",
    pattern: str = "",
    trigger_condition: str = "",
    affected_component: str = "",
    severity: str = "medium",
    tags: List[str] = Query(default=[]),
    created_by: str = "",
):
    """创建修复模板。"""
    try:
        defect_category = DefectCategory(category)
    except ValueError:
        defect_category = DefectCategory.CUSTOM
    
    signature = DefectSignature(
        category=defect_category,
        pattern=pattern,
        trigger_condition=trigger_condition,
        affected_component=affected_component,
        severity=severity,
        tags=tags,
    )
    
    template = await _template_engine.create_template(
        name=name,
        description=description,
        original_code=original_code,
        fix_code=fix_code,
        defect_signature=signature,
        created_by=created_by,
    )
    
    return {"status": "ok", "template": template.to_dict()}


@router.get("/templates")
async def list_templates(
    category: Optional[str] = None,
):
    """列出修复模板。"""
    if category:
        try:
            cat = DefectCategory(category)
            templates = _store.list_templates(cat)
        except ValueError:
            templates = _store.list_templates()
    else:
        templates = _store.list_templates()
    
    return {
        "status": "ok",
        "templates": [t.to_dict() for t in templates],
        "total": len(templates),
    }


@router.get("/templates/{template_id}")
async def get_template(template_id: str):
    """获取修复模板详情。"""
    template = _store.get_template(template_id)
    if not template:
        raise HTTPException(status_code=404, detail="修复模板不存在")
    return {"status": "ok", "template": template.to_dict()}


@router.delete("/templates/{template_id}")
async def delete_template(template_id: str):
    """删除修复模板。"""
    if _store.delete_template(template_id):
        return {"status": "ok", "message": "删除成功"}
    raise HTTPException(status_code=404, detail="修复模板不存在")


@router.post("/templates/{template_id}/find-similar")
async def find_similar_templates(
    template_id: str,
    threshold: float = Query(default=0.6, ge=0.0, le=1.0),
):
    """查找相似修复模板。"""
    template = _store.get_template(template_id)
    if not template:
        raise HTTPException(status_code=404, detail="修复模板不存在")
    
    similar = _template_engine.find_similar_templates(
        template.defect_signature, threshold
    )
    
    return {
        "status": "ok",
        "similar_templates": [t.to_dict() for t in similar],
        "total": len(similar),
    }


# ── 契约仿真 API ──

@router.post("/simulations")
async def run_simulation(
    template_id: str,
    contract_name: str = "",
    mutation_strategy: str = "random",
    num_variations: int = Query(default=10, ge=1, le=100),
):
    """运行契约仿真。"""
    template = _store.get_template(template_id)
    if not template:
        raise HTTPException(status_code=404, detail="修复模板不存在")
    
    sim = await _sim_engine.run_simulation(
        template=template,
        contract_name=contract_name,
        mutation_strategy=mutation_strategy,
        num_variations=num_variations,
    )
    
    return {"status": "ok", "simulation": sim.to_dict()}


@router.get("/simulations")
async def list_simulations(
    template_id: Optional[str] = None,
):
    """列出仿真记录。"""
    sims = _store.list_simulations(template_id)
    return {
        "status": "ok",
        "simulations": [s.to_dict() for s in sims],
        "total": len(sims),
    }


@router.get("/simulations/{sim_id}")
async def get_simulation(sim_id: str):
    """获取仿真详情。"""
    sim = _store.get_simulation(sim_id)
    if not sim:
        raise HTTPException(status_code=404, detail="仿真记录不存在")
    return {"status": "ok", "simulation": sim.to_dict()}


# ── 杀伤率评估 API ──

@router.get("/kill-rate/{template_id}")
async def get_kill_rate(template_id: str):
    """获取杀伤率。"""
    template = _store.get_template(template_id)
    if not template:
        raise HTTPException(status_code=404, detail="修复模板不存在")
    
    kill_rate = _evaluator.calculate_kill_rate(template_id)
    history = _evaluator.get_kill_rate_history(template_id)
    
    return {
        "status": "ok",
        "template_id": template_id,
        "template_name": template.name,
        "kill_rate": round(kill_rate, 4),
        "total_simulations": template.total_simulations,
        "successful_kills": template.successful_kills,
        "history": history,
    }


@router.post("/kill-rate/{template_id}/evaluate")
async def evaluate_kill_rate(
    template_id: str,
    min_rate: float = Query(default=0.8, ge=0.0, le=1.0),
    min_simulations: int = Query(default=10, ge=1),
):
    """评估杀伤率是否达标。"""
    template = _store.get_template(template_id)
    if not template:
        raise HTTPException(status_code=404, detail="修复模板不存在")
    
    evaluation = _evaluator.evaluate_kill_rate(
        template_id, min_rate, min_simulations
    )
    
    return {
        "status": "ok",
        "evaluation": evaluation,
    }


# ── 门禁检查 API ──

@router.post("/gates")
async def check_gate(
    template_id: str,
    min_kill_rate: float = Query(default=0.8, ge=0.0, le=1.0),
    required_simulations: int = Query(default=10, ge=1),
    checked_by: str = "",
):
    """执行门禁检查。"""
    template = _store.get_template(template_id)
    if not template:
        raise HTTPException(status_code=404, detail="修复模板不存在")
    
    gate = await _gate_engine.check_gate(
        template_id=template_id,
        min_kill_rate=min_kill_rate,
        required_simulations=required_simulations,
        checked_by=checked_by,
    )
    
    return {"status": "ok", "gate": gate.to_dict()}


@router.get("/gates")
async def list_gates(
    template_id: Optional[str] = None,
):
    """列出门禁检查记录。"""
    gates = _store.list_gates(template_id)
    return {
        "status": "ok",
        "gates": [g.to_dict() for g in gates],
        "total": len(gates),
    }


@router.get("/gates/{gate_id}")
async def get_gate(gate_id: str):
    """获取门禁检查详情。"""
    gate = _store.get_gate(gate_id)
    if not gate:
        raise HTTPException(status_code=404, detail="门禁检查不存在")
    return {"status": "ok", "gate": gate.to_dict()}


@router.post("/gates/{gate_id}/bypass")
async def bypass_gate(
    gate_id: str,
    bypassed_by: str,
    reason: str,
):
    """绕过门禁（管理员授权）。"""
    gate = _gate_engine.bypass_gate(gate_id, bypassed_by, reason)
    if not gate:
        raise HTTPException(status_code=404, detail="门禁检查不存在")
    return {"status": "ok", "gate": gate.to_dict()}


@router.get("/gates/summary/{template_id}")
async def get_gate_summary(template_id: str):
    """获取门禁状态摘要。"""
    summary = _gate_engine.get_gate_status_summary(template_id)
    return {"status": "ok", "summary": summary}
```

### 4.2 修改文件: `src/backend/main.py`

在 FastAPI 应用中注册新路由：

```python
# 在现有路由注册后添加
from agents.regression_gate_routes import router as regression_gate_router
app.include_router(regression_gate_router)
```

## 5. 与现有系统的集成

### 5.1 集成到发布流程

```python
class ReleasePipeline:
    """发布流��线 — 集成回归杀伤率门禁。"""
    
    def __init__(self, gate_engine: GateDecisionEngine):
        self._gate_engine = gate_engine
    
    async def pre_release_check(
        self,
        template_id: str,
        release_id: str,
    ) -> Dict[str, Any]:
        """发布前门禁检查。"""
        gate = await self._gate_engine.check_gate(
            template_id=template_id,
            checked_by="release_pipeline",
        )
        
        return {
            "release_id": release_id,
            "template_id": template_id,
            "gate_id": gate.gate_id,
            "status": gate.status.value,
            "kill_rate": gate.current_kill_rate,
            "can_release": gate.status in [GateStatus.PASSED, GateStatus.BYPASSED],
            "message": (
                "门禁通过，可以发布"
                if gate.status == GateStatus.PASSED
                else "门禁未通过，请修复缺陷后重试"
                if gate.status == GateStatus.FAILED
                else f"门禁状态: {gate.status.value}"
            ),
        }
```

### 5.2 集成到 Agent 工作流

在 `src/backend/agents/agent_loop.py` 中添加门禁检查步骤：

```python
async def run_agent_with_gate(
    agent_id: str,
    task: Dict[str, Any],
    gate_engine: GateDecisionEngine,
) -> Dict[str, Any]:
    """带门禁检查的 Agent 执行。"""
    
    # 1. 执行任务
    result = await run_agent(agent_id, task)
    
    # 2. 如果有修复操作，创建修复模板
    if "fix" in task or "patch" in task:
        template = await create_fix_template_from_result(result)
        
        # 3. 运行契约仿真
        sim = await run_simulation(template)
        
        # 4. 执行门禁检查
        gate = await gate_engine.check_gate(
            template_id=template.template_id,
            checked_by=agent_id,
        )
        
        # 5. 根据门禁结果决定是否发布
        if gate.status == GateStatus.PASSED:
            result["can_release"] = True
            result["gate_status"] = "passed"
        else:
            result["can_release"] = False
            result["gate_status"] = "failed"
            result["gate_reason"] = "杀伤率不足，需要进一步修复"
    
    return result
```

## 6. 前端界面

### 6.1 新增文件: `src/frontend/regression-gate.html`

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>回归杀伤率门禁</title>
    <link rel="stylesheet" href="css/openbridge-theme.css">
    <style>
        .gate-container { padding: 20px; }
        .gate-header { margin-bottom: 20px; }
        .gate-stats { display: grid; grid-template-columns: repeat(4, 1fr); gap: 15px; margin-bottom: 20px; }
        .stat-card { background: var(--card-bg); padding: 15px; border-radius: 8px; }
        .stat-value { font-size: 24px; font-weight: bold; }
        .stat-label { font-size: 12px; color: var(--text-secondary); }
        .kill-rate-meter { height: 8px; background: var(--bg-secondary); border-radius: 4px; overflow: hidden; }
        .kill-rate-fill { height: 100%; border-radius: 4px; transition: width 0.3s; }
        .kill-rate-fill.passed { background: var(--success); }
        .kill-rate-fill.failed { background: var(--danger); }
        .template-list { margin-top: 20px; }
        .template-card { background: var(--card-bg); padding: 15px; margin-bottom: 10px; border-radius: 8px; }
        .gate-status { display: inline-block; padding: 4px 8px; border-radius: 4px; font-size: 12px; }
        .gate-status.passed { background: var(--success-bg); color: var(--success); }
        .gate-status.failed { background: var(--danger-bg); color: var(--danger); }
        .gate-status.pending { background: var(--warning-bg); color: var(--warning); }
    </style>
</head>
<body>
    <div class="gate-container">
        <div class="gate-header">
            <h1>回归杀伤率门禁</h1>
            <p>确保修复模板在契约仿真中复现并杀死同类缺陷方可发布</p>
        </div>
        
        <div class="gate-stats">
            <div class="stat-card">
                <div class="stat-value" id="totalTemplates">0</div>
                <div class="stat-label">修复模板总数</div>
            </div>
            <div class="stat-card">
                <div class="stat-value" id="passedGates">0</div>
                <div class="stat-label">通过门禁</div>
            </div>
            <div class="stat-card">
                <div class="stat-value" id="failedGates">0</div>
                <div class="stat-label">未通过门禁</div>
            </div>
            <div class="stat-card">
                <div class="stat-value" id="avgKillRate">0%</div>
                <div class="stat-label">平均杀伤率</div>
            </div>
        </div>
        
        <div class="template-list" id="templateList">
            <!-- 动态加载 -->
        </div>
    </div>
    
    <script>
        async function loadData() {
            try {
                const [templatesRes, gatesRes] = await Promise.all([
                    fetch('/api/regression-gate/templates'),
                    fetch('/api/regression-gate/gates')
                ]);
                
                const templates = (await templatesRes.json()).templates || [];
                const gates = (await gatesRes.json()).gates || [];
                
                // 更新统计
                document.getElementById('totalTemplates').textContent = templates.length;
                document.getElementById('passedGates').textContent = 
                    gates.filter(g => g.status === 'passed').length;
                document.getElementById('failedGates').textContent = 
                    gates.filter(g => g.status === 'failed').length;
                
                const avgRate = templates.reduce((sum, t) => sum + t.kill_rate, 0) / (templates.length || 1);
                document.getElementById('avgKillRate').textContent = 
                    (avgRate * 100).toFixed(1) + '%';
                
                // 渲染模板列表
                const list = document.getElementById('templateList');
                list.innerHTML = templates.map(t => {
                    const gate = gates.find(g => g.template_id === t.template_id);
                    const status = gate ? gate.status : 'pending';
                    const killRate = (t.kill_rate * 100).toFixed(1);
                    
                    return `
                        <div class="template-card">
                            <div style="display: flex; justify-content: space-between; align-items: center;">
                                <div>
                                    <h3>${t.name}</h3>
                                    <p>${t.description}</p>
                                    <small>分类: ${t.defect_signature.category}</small>
                                </div>
                                <div style="text-align: right;">
                                    <div class="gate-status ${status}">${status}</div>
                                    <div style="margin-top: 8px;">
                                        <div class="kill-rate-meter">
                                            <div class="kill-rate-fill ${status}" 
                                                 style="width: ${killRate}%"></div>
                                        </div>
                                        <small>杀伤率: ${killRate}%</small>
                                    </div>
                                </div>
                            </div>
                        </div>
                    `;
                }).join('');
                
            } catch (error) {
                console.error('加载数据失败:', error);
            }
        }
        
        // 每30秒刷新
        loadData();
        setInterval(loadData, 30000);
    </script>
</body>
</html>
```

## 7. 实施步骤

### 步骤 1: 创建核心数据模型
- 创建 `src/backend/agents/regression_gate.py`
- 实现所有数据模型和存储类

### 步骤 2: 实现核心引擎
- 实现 `FixTemplateEngine`
- 实现 `ContractSimEngine`
- 实现 `KillRateEvaluator`
- 实现 `GateDecisionEngine`

### 步骤 3: 创建 API 路由
- 创建 `src/backend/agents/regression_gate_routes.py`
- 在 `main.py` 中注册路由

### 步骤 4: 创建前端界面
- 创建 `src/frontend/regression-gate.html`

### 步骤 5: 集成到现有系统
- 修改 `agent_loop.py` 集成门禁检查
- 修改发布流程集成门禁

### 步骤 6: 测试
- 单元测试: 测试各引擎功能
- 集成测试: 测试完整流程
- 端到端测试: 测试 API 和前端

## 8. 测试计划

### 8.1 单元测试

```python
# tests/test_regression_gate.py

async def test_create_template():
    engine = FixTemplateEngine(store)
    template = await engine.create_template(
        name="空指针修复",
        description="修复空指针异常",
        original_code="return obj.value",
        fix_code="return obj.value if obj else None",
        defect_signature=DefectSignature(category=DefectCategory.NULL_POINTER),
    )
    assert template.template_id
    assert template.kill_rate == 0.0

async def test_run_simulation():
    engine = ContractSimEngine(store)
    template = create_test_template()
    sim = await engine.run_simulation(template, num_variations=10)
    assert sim.status == "completed"
    assert sim.total_tests == 10

async def test_gate_check():
    engine = GateDecisionEngine(store)
    template = create_test_template_with_simulations()
    gate = await engine.check_gate(template.template_id)
    assert gate.status in [GateStatus.PASSED, GateStatus.FAILED]
```

### 8.2 集成测试

```python
async def test_full_pipeline():
    # 1. 创建修复模板
    template = await create_template()
    
    # 2. 运行仿真
    sim = await run_simulation(template)
    
    # 3. 检查门禁
    gate = await check_gate(template)
    
    # 4. 验证结果
    assert gate.status == GateStatus.PASSED
    assert gate.current_kill_rate >= 0.8
```

## 9. 配置说明

在 `config/settings.json` 中添加门禁配置：

```json
{
    "regression_gate": {
        "enabled": true,
        "default_min_kill_rate": 0.8,
        "default_required_simulations": 10,
        "storage_path": "data/regression_gate/",
        "allow_bypass": false,
        "bypass_roles": ["admin", "architect"]
    }
}
```

## 10. 安全考虑

1. **门禁绕过权限控制**: 只有管理员和架构师可以绕过门禁
2. **仿真沙箱**: 契约仿真应在隔离环境中执行
3. **审计日志**: 所有门禁操作记录审计日志
4. **数据完整性**: 杀伤率计算应基于不可篡改的仿真记录

────────────────────────────────────────────────────────────
✅ deepseek-chat 完成
