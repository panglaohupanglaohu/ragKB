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
  
  ### 步骤 01: pm_decompose (完整产出)
  
  # PM分解 — project_manager
  
  任务: 集成回归杀伤率门禁，要求修复模板在对应契约仿真中复现并杀死同类缺陷方可发布
  步骤: pm_decompose
  Agent: build_pm
  
  ---
  
  📋 任务: 72652523-8a4
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

# 技术调研报告：集成回归杀伤率门禁

## 1. 任务理解

**核心需求**：实现一个回归杀伤率门禁系统，要求：
- 修复模板（bug fix template）必须在对应的契约仿真（contract simulation）中复现（reproduce）缺陷
- 修复必须能"杀死"（kill）同类缺陷（same-class defects）
- 通过门禁检查后方可发布

**涉及角色**：Tester + Architect

## 2. 现有系统分析

### 2.1 相关文件结构

根据项目上下文，以下文件与本次任务相关：

| 文件路径 | 角色 | 说明 |
|---------|------|------|
| `src/backend/agents/chat_harness.py` | 核心 | Chat Harness，LLM 调用管道 |
| `src/backend/agents/hermes_research.py` | 核心 | Hermes 研究代理 |
| `src/backend/agents/models.py` | 核心 | 数据模型 |
| `src/backend/agents/plaza_engine.py` | 核心 | 广场引擎，讨论编排 |
| `src/backend/agents/plaza.py` | 核心 | 广场数据模型 |
| `src/backend/agents/plaza_store.py` | 存储 | 广场持久化 |
| `src/backend/agents/execution_registry.py` | 核心 | 执行注册表 |
| `src/backend/agents/task_engine.py` | 核心 | 任务引擎 |
| `src/backend/agents/task_store.py` | 存储 | 任务存储 |
| `src/backend/agents/team_manager.py` | 核心 | 团队管理 |
| `src/backend/agents/agent_loop.py` | 核心 | 代理循环 |
| `src/backend/agents/api.py` | API | API 路由 |
| `src/backend/agent_team_api.py` | API | 团队 API |
| `src/backend/main.py` | 入口 | 应用入口 |

### 2.2 现有能力分析

#### 2.2.1 契约仿真（Contract Simulation）
- **`plaza_engine.py`** 提供了讨论编排引擎，支持多 Agent 协同讨论
- **`plaza.py`** 定义了 `Discussion`、`Participant`、`SeatTier`、`NicheRole` 等模型
- **`plaza_store.py`** 提供持久化存储
- **现有能力**：支持创建广场、添加参与者、发起讨论、多轮对话

#### 2.2.2 测试框架
- **`task_engine.py`** 和 **`task_store.py`** 提供任务执行和存储
- **`execution_registry.py`** 提供执行注册和权限管理
- **`agent_loop.py`** 提供代理循环执行

#### 2.2.3 缺陷管理
- **`hermes_research.py`** 提供研究能力，可进行缺陷分析
- **`chat_harness.py`** 提供 LLM 调用管道

### 2.3 缺失能力

1. **缺陷模板管理**：没有专门的缺陷模板（bug fix template）管理模块
2. **契约仿真引擎**：没有专门的契约仿真（contract simulation）引擎
3. **回归杀伤率计算**：没有回归杀伤率（regression kill rate）计算逻辑
4. **门禁检查**：没有发布门禁（release gate）检查机制
5. **缺陷分类系统**：没有缺陷分类（defect classification）系统
6. **同类缺陷识别**：没有同类缺陷（same-class defects）识别逻辑

## 3. 技术方案设计

### 3.1 架构设计

```
┌─────────────────────────────────────────────────────────────┐
│                    回归杀伤率门禁系统                          │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │ 缺陷模板管理  │  │ 契约仿真引擎  │  │ 门禁检查器   │        │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘        │
│         │                │                │                │
│  ┌──────┴──────┐  ┌──────┴──────┐  ┌──────┴──────┐        │
│  │ 缺陷分类系统  │  │ 杀伤率计算器 │  │ 发布管理器   │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
└─────────────────────────────────────────────────────────────┘
         │                │                │
         ▼                ▼                ▼
┌─────────────────────────────────────────────────────────────┐
│                    现有基础设施                                │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │ Plaza Engine │  │ Task Engine  │  │ Chat Harness │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
└─────────────────────────────────────────────────────────────┘
```

### 3.2 核心模块设计

#### 3.2.1 缺陷模板管理 (`src/backend/agents/defect_template.py`)

```python
@dataclass
class DefectTemplate:
    """缺陷修复模板"""
    template_id: str
    defect_id: str
    defect_class: str  # 缺陷分类
    description: str
    fix_code: str  # 修复代码
    test_cases: List[str]  # 测试用例
    created_at: str
    updated_at: str
    status: DefectStatus  # OPEN, FIXED, VERIFIED, CLOSED

@dataclass
class DefectClassification:
    """缺陷分类"""
    class_id: str
    class_name: str  # 如: NullPointer, SQLInjection, RaceCondition
    severity: SeverityLevel
    pattern: str  # 缺陷模式描述
    detection_rules: List[str]  # 检测规则
```

#### 3.2.2 契约仿真引擎 (`src/backend/agents/contract_simulation.py`)

```python
@dataclass
class ContractSimulation:
    """契约仿真"""
    simulation_id: str
    defect_template_id: str
    contract_code: str  # 契约代码
    simulation_config: SimulationConfig
    results: List[SimulationResult]
    status: SimulationStatus

@dataclass
class SimulationResult:
    """仿真结果"""
    test_case_id: str
    input: Any
    expected_output: Any
    actual_output: Any
    passed: bool
    defect_reproduced: bool  # 缺陷是否复现
    defect_killed: bool  # 缺陷是否被杀死
```

#### 3.2.3 回归杀伤率计算器 (`src/backend/agents/regression_kill_rate.py`)

```python
@dataclass
class RegressionKillRate:
    """回归杀伤率"""
    total_defects: int  # 总缺陷数
    reproduced_defects: int  # 复现的缺陷数
    killed_defects: int  # 杀死的缺陷数
    kill_rate: float  # 杀伤率 = killed / total
    reproduction_rate: float  # 复现率 = reproduced / total
    
    def can_release(self, threshold: float = 0.8) -> bool:
        """检查是否可以通过门禁"""
        return self.kill_rate >= threshold
```

#### 3.2.4 门禁检查器 (`src/backend/agents/release_gate.py`)

```python
@dataclass
class ReleaseGate:
    """发布门禁"""
    gate_id: str
    defect_template_id: str
    simulation_id: str
    kill_rate: RegressionKillRate
    passed: bool
    checked_at: str
    checked_by: str  # Tester + Architect
    
    def check(self) -> bool:
        """执行门禁检查"""
        # 1. 运行契约仿真
        simulation = self.run_simulation()
        
        # 2. 计算杀伤率
        kill_rate = self.calculate_kill_rate(simulation)
        
        # 3. 检查是否通过
        self.passed = kill_rate.can_release()
        
        return self.passed
```

### 3.3 数据流

```
1. Tester 创建缺陷模板
   ↓
2. Architect 定义契约仿真
   ↓
3. 系统运行契约仿真
   ↓
4. 计算回归杀伤率
   ↓
5. 门禁检查
   ↓
6. 通过 → 允许发布
   失败 → 返回修复
```

## 4. 需要修改的文件

### 4.1 新增文件

| 文件路径 | 说明 |
|---------|------|
| `src/backend/agents/defect_template.py` | 缺陷模板管理模块 |
| `src/backend/agents/contract_simulation.py` | 契约仿真引擎 |
| `src/backend/agents/regression_kill_rate.py` | 回归杀伤率计算器 |
| `src/backend/agents/release_gate.py` | 发布门禁检查器 |
| `src/backend/agents/defect_classification.py` | 缺陷分类系统 |

### 4.2 修改文件

| 文件路径 | 修改内容 |
|---------|---------|
| `src/backend/agents/models.py` | 添加缺陷模板、契约仿真、门禁相关数据模型 |
| `src/backend/agents/api.py` | 添加门禁检查 API 路由 |
| `src/backend/agents/plaza_engine.py` | 扩展讨论引擎支持契约仿真讨论 |
| `src/backend/agents/task_engine.py` | 扩展任务引擎支持门禁检查任务 |
| `src/backend/agents/team_manager.py` | 添加 Tester + Architect 团队配置 |
| `src/backend/main.py` | 注册新模块路由 |

### 4.3 具体修改点

#### 4.3.1 `src/backend/agents/models.py` 修改

在 `models.py` 中添加以下数据模型（约 150 行）：

```python
# 在文件末尾添加

@dataclass
class DefectStatus(Enum):
    OPEN = "open"
    FIXED = "fixed"
    VERIFIED = "verified"
    CLOSED = "closed"

@dataclass
class SeverityLevel(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

@dataclass
class DefectTemplate:
    template_id: str = ""
    defect_id: str = ""
    defect_class: str = ""
    description: str = ""
    fix_code: str = ""
    test_cases: List[str] = field(default_factory=list)
    created_at: str = ""
    updated_at: str = ""
    status: str = "open"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "template_id": self.template_id,
            "defect_id": self.defect_id,
            "defect_class": self.defect_class,
            "description": self.description,
            "fix_code": self.fix_code,
            "test_cases": self.test_cases,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "status": self.status,
        }

@dataclass
class ContractSimulation:
    simulation_id: str = ""
    defect_template_id: str = ""
    contract_code: str = ""
    config: Dict[str, Any] = field(default_factory=dict)
    results: List[Dict[str, Any]] = field(default_factory=list)
    status: str = "pending"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "simulation_id": self.simulation_id,
            "defect_template_id": self.defect_template_id,
            "contract_code": self.contract_code,
            "config": self.config,
            "results": self.results,
            "status": self.status,
        }

@dataclass
class RegressionKillRate:
    total_defects: int = 0
    reproduced_defects: int = 0
    killed_defects: int = 0
    
    @property
    def kill_rate(self) -> float:
        if self.total_defects == 0:
            return 1.0
        return self.killed_defects / self.total_defects
    
    @property
    def reproduction_rate(self) -> float:
        if self.total_defects == 0:
            return 1.0
        return self.reproduced_defects / self.total_defects
    
    def can_release(self, threshold: float = 0.8) -> bool:
        return self.kill_rate >= threshold
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_defects": self.total_defects,
            "reproduced_defects": self.reproduced_defects,
            "killed_defects": self.killed_defects,
            "kill_rate": self.kill_rate,
            "reproduction_rate": self.reproduction_rate,
            "can_release": self.can_release(),
        }

@dataclass
class ReleaseGate:
    gate_id: str = ""
    defect_template_id: str = ""
    simulation_id: str = ""
    kill_rate: Optional[RegressionKillRate] = None
    passed: bool = False
    checked_at: str = ""
    checked_by: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "gate_id": self.gate_id,
            "defect_template_id": self.defect_template_id,
            "simulation_id": self.simulation_id,
            "kill_rate": self.kill_rate.to_dict() if self.kill_rate else None,
            "passed": self.passed,
            "checked_at": self.checked_at,
            "checked_by": self.checked_by,
        }
```

#### 4.3.2 `src/backend/agents/api.py` 修改

在 `api.py` 中添加门禁检查 API 路由（约 80 行）：

```python
# 在文件末尾添加

@router.post("/release-gate/check")
async def check_release_gate(
    defect_template_id: str,
    simulation_config: Dict[str, Any],
    checked_by: str = "tester+architect"
):
    """执行门禁检查"""
    # 1. 加载缺陷模板
    template = await defect_template_service.get(defect_template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Defect template not found")
    
    # 2. 运行契约仿真
    simulation = await contract_simulation_service.run(
        template=template,
        config=simulation_config
    )
    
    # 3. 计算杀伤率
    kill_rate = regression_kill_rate_service.calculate(simulation)
    
    # 4. 执行门禁检查
    gate = ReleaseGate(
        defect_template_id=defect_template_id,
        simulation_id=simulation.simulation_id,
        kill_rate=kill_rate,
        checked_by=checked_by,
        checked_at=datetime.now(timezone.utc).isoformat(),
        passed=kill_rate.can_release()
    )
    
    # 5. 保存结果
    await release_gate_service.save(gate)
    
    return gate.to_dict()

@router.get("/release-gate/{gate_id}")
async def get_release_gate(gate_id: str):
    """获取门禁检查结果"""
    gate = await release_gate_service.get(gate_id)
    if not gate:
        raise HTTPException(status_code=404, detail="Release gate not found")
    return gate.to_dict()

@router.get("/defect-templates")
async def list_defect_templates(
    defect_class: Optional[str] = None,
    status: Optional[str] = None
):
    """列出缺陷模板"""
    return await defect_template_service.list(
        defect_class=defect_class,
        status=status
    )
```

#### 4.3.3 `src/backend/agents/plaza_engine.py` 修改

在 `plaza_engine.py` 中添加契约仿真讨论支持（约 50 行）：

```python
# 在 PlazaEngine 类中添加方法

async def run_contract_simulation_discussion(
    self,
    plaza_id: str,
    defect_template_id: str,
    participants: List[str]  # [tester_id, architect_id]
) -> Discussion:
    """运行契约仿真讨论"""
    plaza = self._plazas.get(plaza_id)
    if not plaza:
        raise ValueError(f"Plaza {plaza_id} not found")
    
    # 创建讨论
    disc = self.create_discussion(
        plaza_id=plaza_id,
        topic=f"Contract Simulation for Defect Template {defect_template_id}",
        description="Regression kill rate gate check discussion",
        moderator_agent_id=participants[0],  # Tester as moderator
        max_rounds=3
    )
    
    # 添加参与者
    for agent_id in participants:
        self.add_participant(
            plaza_id=plaza_id,
            agent_id=agent_id,
            seat_tier=SeatTier.INNER,
            niche_role=NicheRole.SPEAKER
        )
    
    # 启动讨论
    await self.start_discussion(plaza_id, disc.id)
    
    return disc
```

#### 4.3.4 `src/backend/agents/task_engine.py` 修改

在 `task_engine.py` 中添加门禁检查任务支持（约 40 行）：

```python
# 在 TaskEngine 类中添加方法

async def execute_release_gate_task(
    self,
    task_id: str,
    defect_template_id: str,
    simulation_config: Dict[str, Any]
) -> TaskResult:
    """执行门禁检查任务"""
    # 1. 加载任务
    task = await self._task_store.get(task_id)
    if not task:
        raise ValueError(f"Task {task_id} not found")
    
    # 2. 更新任务状态
    task.status = "running"
    await self._task_store.save(task)
    
    try:
        # 3. 运行契约仿真
        simulation = await self._contract_simulation_service.run(
            defect_template_id=defect_template_id,
            config=simulation_config
        )
        
        # 4. 计算杀伤率
        kill_rate = self._regression_kill_rate_service.calculate(simulation)
        
        # 5. 执行门禁检查
        gate = ReleaseGate(
            defect_template_id=defect_template_id,
            simulation_id=simulation.simulation_id,
            kill_rate=kill_rate,
            passed=kill_rate.can_release()
        )
        
        # 6. 更新任务结果
        task.status = "completed" if gate.passed else "failed"
        task.result = gate.to_dict()
        await self._task_store.save(task)
        
        return TaskResult(
            task_id=task_id,
            status=task.status,
            result=task.result
        )
        
    except Exception as e:
        task.status = "failed"
        task.error = str(e)
        await self._task_store.save(task)
        raise
```

## 5. 可行性分析

### 5.1 技术可行性

1. **现有基础设施完善**：系统已有 Plaza Engine（讨论编排）、Task Engine（任务执行）、Chat Harness（LLM 调用）等基础设施
2. **数据模型可扩展**：`models.py` 使用 dataclass，易于扩展
3. **API 架构清晰**：FastAPI 路由易于添加新端点
4. **存储层支持**：Plaza Store、Task Store 提供持久化支持

### 5.2 实现难度

| 模块 | 难度 | 说明 |
|-----|------|------|
| 缺陷模板管理 | 低 | 基于现有数据模型扩展 |
| 契约仿真引擎 | 中 | 需要定义仿真逻辑和结果评估 |
| 回归杀伤率计算 | 低 | 数学计算，逻辑清晰 |
| 门禁检查器 | 中 | 需要集成多个模块 |
| 缺陷分类系统 | 中 | 需要定义分类规则 |

### 5.3 风险点

1. **契约仿真准确性**：仿真结果需要准确反映实际缺陷修复效果
2. **同类缺陷识别**：需要明确定义"同类缺陷"的判定标准
3. **性能考虑**：大规模仿真可能影响系统性能
4. **集成测试**：需要确保新模块与现有系统的兼容性

## 6. 实施建议

### 6.1 分阶段实施

**Phase 1：基础框架**
- 实现缺陷模板管理
- 实现缺陷分类系统
- 添加数据模型

**Phase 2：核心功能**
- 实现契约仿真引擎
- 实现回归杀伤率计算器
- 实现门禁检查器

**Phase 3：集成测试**
- 集成到现有 API
- 集成到 Plaza Engine
- 集成到 Task Engine

**Phase 4：优化完善**
- 性能优化
- 添加监控和日志
- 编写文档

### 6.2 测试策略

1. **单元测试**：每个模块独立测试
2. **集成测试**：测试模块间交互
3. **端到端测试**：模拟完整门禁检查流程
4. **回归测试**：确保不影响现有功能

## 7. 总结

本次技术调研确认了实现"回归杀伤率门禁"的可行性。系统现有基础设施（Plaza Engine、Task Engine、Chat Harness）为功能实现提供了良好基础。需要新增 5 个模块，修改 6 个现有文件，建议分 4 个阶段实施。主要风险在于契约仿真的准确性和同类缺陷的判定标准，需要在实现过程中重点关注。

────────────────────────────────────────────────────────────
✅ deepseek-chat 完成
