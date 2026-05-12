# 架构设计 — architect

任务: 定义配置快照协议：固化 transaction_id、版本号、规则体、时间戳等字段，明确原子替换语义和初始化握手流程
步骤: architecture
Agent: build_architect

---

📋 任务: ba472f30-1a6
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
  定义配置快照协议：固化 transaction_id、版本号、规则体、时间戳等字段，明确原子替换语义和初始化握手流程
  Architect
  
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
  src/docs/agent_handoffs/d553cde7-ee1_executor_started_20260506T101306.md
  src/docs/agent_handoffs/d87c964b-c06_architecture_20260503T045321.md
  src/docs/agent_handoffs/d87c964b-c06_pm_decompose_20260503T045236.md
  src/docs/agent_handoffs/d87c964b-c06_research_20260503T045251.md
  src/docs/agent_handoffs/d87c964b-c06_task_init_20260503T045211.md
  src/docs/agent_handoffs/dbf24d0c-5cc_architecture_20260503T235205.md
  src/docs/agent_handoffs/dbf24d0c-5cc_deploy_FAILED_20260504T012356.md
  src/docs/agent_handoffs/dbf24d0c-5cc_develop_20260503T235646.md
  src/docs/agent_handoffs/dbf24d0c-5cc_develop_20260504T004702.md
  src/docs/agent_handoffs/dbf24d0c-5cc_develop_FAILED_20260504T001109.md
  src/docs/agent_handoffs/dbf24d0c-5cc_executor_started_20260503T234950.md
  src/docs/agent_handoffs/dbf24d0c-5cc_pm_decompose_20260503T235020.md
  src/docs/agent_handoffs/dbf24d0c-5cc_research_20260503T235105.md
  src/docs/agent_handoffs/dbf24d0c-5cc_test_FAILED_20260504T000157.md
  src/docs/agent_handoffs/dbf24d0c-5cc_test_FAILED_20260504T002112.md
  src/docs/agent_handoffs/dbf24d0c-5cc_test_FAILED_20260504T012326.md
  src/docs/agent_handoffs/dd0e3569-eb0_architecture_20260503T114837.md
  src/docs/agent_handoffs/dd0e3569-eb0_deploy_FAILED_20260503T121257.md
  src/docs/agent_handoffs/dd0e3569-eb0_develop_20260503T115309.md
  src/docs/agent_handoffs/dd0e3569-eb0_develop_FAILED_20260503T120023.md
  src/docs/agent_handoffs/dd0e3569-eb0_develop_FAILED_20260503T120906.md
  src/docs/agent_handoffs/dd0e3569-eb0_executor_started_20260503T114547.md
  src/docs/agent_handoffs/dd0e3569-eb0_pm_decompose_20260503T114622.md
  src/docs/agent_handoffs/dd0e3569-eb0_research_20260503T114712.md
  src/docs/agent_handoffs/dd0e3569-eb0_test_20260503T115557.md
  src/docs/agent_handoffs/dd0e3569-eb0_test_FAILED_20260503T120434.md
  src/docs/agent_handoffs/dd0e3569-eb0_test_FAILED_20260503T121242.md
  src/docs/workflow_artifacts/1ce78c0e-062_architecture.md
  src/docs/workflow_artifacts/1ce78c0e-062_deploy.md
  src/docs/workflow_artifacts/1ce78c0e-062_develop.md
  src/docs/workflow_artifacts/1ce78c0e-062_pm_decompose.md
  src/docs/workflow_artifacts/1ce78c0e-062_research.md
  src/docs/workflow_artifacts/1ce78c0e-062_test.md
  src/docs/workflow_artifacts/38e22004-b64_architecture.md
  src/docs/workflow_artifacts/38e22004-b64_pm_decompose.md
  src/docs/workflow_artifacts/38e22004-b64_research.md
  src/docs/workflow_artifacts/7c934759-39e_architecture.md
  src/docs/workflow_artifacts/7c934759-39e_deploy.md
  src/docs/workflow_artifacts/7c934759-39e_develop.md
  src/docs/workflow_artifacts/7c934759-39e_pm_decompose.md
  src/docs/workflow_artifacts/7c934759-39e_research.md
  src/docs/workflow_artifacts/7c934759-39e_test.md
  src/docs/workflow_artifacts/ba3b66b1-a77_architecture.md
  src/docs/workflow_artifacts/ba3b66b1-a77_deploy.md
  ... (共 169 个 src/ 文件)
  
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
  
  ### 文件: `src/backend/agents/plaza.py`
  ```py
  # -*- coding: utf-8 -*-
  """智能体广场 — 数据模型.
  
  灵感来源：维特鲁威环形比例 + 威尔士议事厅向心结构 + 科幻美学。
  广场是一个环形的多智能体讨论空间，中心为数字奇点（Digital Singularity），
  座席环绕其四周，12个壁龛提供私有交互接口。
  """
  
  from __future__ import annotations
  
  import enum
  from dataclasses import dataclass, field
  from datetime import datetime, timezone
  from typing import Any, Dict, List, Optional
  from uuid import uuid4
  
  
  class DiscussionStatus(str, enum.Enum):
      """讨论状态流转: open → in_progress → summarizing → closed."""
      OPEN = "open"
      IN_PROGRESS = "in_progress"
      SUMMARIZING = "summarizing"
      CLOSED = "closed"
  
  
  class SeatTier(str, enum.Enum):
      """座席层级 — 三层同心圆阶梯（致敬尤利亚议事堂）."""
      INNER = "inner"       # 内圈 — 核心讨论者
      MIDDLE = "middle"     # 中圈 — 积极参与者
      OUTER = "outer"       # 外圈 — 观察者/旁听
  
  
  class NicheRole(str, enum.Enum):
      """壁龛角色 — 12个弧形壁龛的功能定义."""
      MODERATOR = "moderator"         # 主持人壁龛
      ANALYST = "analyst"             # 分析师壁龛
      CHALLENGER = "challenger"       # 挑战者壁龛
      SYNTHESIZER = "synthesizer"     # 综合者壁龛
      OBSERVER = "observer"           # 观察者壁龛
  
  
  @dataclass
  class PlazaMessage:
      """广场讨论消息 — 在数字奇点中显示的信息流."""
      id: str = field(default_factory=lambda: uuid4().hex[:12])
      discussion_id: str = ""
      agent_id: str = ""
      agent_name: str = ""
      role: str = ""                    # agent的角色
      niche_role: str = ""              # 在本次讨论中的壁龛角色
      content: str = ""
      round_number: int = 0             # 第几轮讨论
      reply_to: Optional[str] = None    # 回复哪条消息
      created_at: str = field(
          default_factory=lambda: datetime.now(timezone.utc).isoformat()
      )
      metadata: Dict[str, Any] = field(default_factory=dict)
  
      def to_dict(self) -> Dict[str, Any]:
          return {
              "id": self.id,
              "discussion_id": self.discussion_id,
              "agent_id": self.agent_id,
              "agent_name": self.agent_name,
              "role": self.role,
              "niche_role": self.niche_role,
              "content": self.content,
              "round_number": self.round_number,
              "reply_to": self.reply_to,
              "created_at": self.created_at,
              "metadata": self.metadata,
          }
  
  
  @dataclass
  class Participant:
      """广场参与者 — 座席上的智能体."""
      agent_id: str
      agent_name: str = ""
      role: str = ""                    # 原始角色
      team_id: str = ""
      seat_tier: SeatTier = SeatTier.MIDDLE
      niche_role: NicheRole = NicheRole.OBSERVER
      niche_index: int = -1             # 壁龛编号 0-11
      joined_at: str = field(
          default_factory=lambda: datetime.now(timezone.utc).isoformat()
      )
  
      def to_dict(self) -> Dict[str, Any]:
          return {
              "agent_id": self.agent_id,
              "agent_name": self.agent_name,
              "role": self.role,
              "team_id": self.team_id,
              "seat_tier": self.seat_tier.value,
              "niche_role": self.niche_role.value,
              "niche_index": self.niche_index,
              "joined_at": self.joined_at,
          }
  
  
  @dataclass
  class Discussion:
      """广场讨论 — 在数字奇点上方投影的全息话题."""
      id: str = field(default_factory=lambda: uuid4().hex[:12])
      plaza_id: str = ""
      topic: str = ""
      description: str = ""
      status: DiscussionStatus = DiscussionStatus.OPEN
      moderator_agent_id: str = ""      # 主持人
      max_rounds: int = 5               # 最大讨论轮次
      current_round: int = 0
      messages: List[PlazaMessage] = field(default_factory=list)
      goal: str = ""                    # 讨论目标
      summary: str = ""                 # 讨论总结
      key_conclusions: List[str] = field(default_factory=list)
      plan: Dict[str, Any] = field(default_factory=dict)  # 议事长生成的执行计划
      assigned_team_id: str = ""        # 计划指派给的团队
      created_at: str = field(
          default_factory=lambda: datetime.now(timezone.utc).isoformat()
      )
      started_at: Optional[str] = None
      ended_at: Optional[str] = None
      metadata: Dict[str, Any] = field(default_factory=dict)
  
      def to_dict(self, include_messages: bool = False) -> Dict[str, Any]:
          d = {
              "id": self.id,
              "plaza_id": self.plaza_id,
              "topic": self.topic,
              "description": self.description,
              "status": self.status.value,
              "moderator_agent_id": self.moderator_agent_id,
              "max_rounds": self.max_rounds,
              "current_round": self.current_round,
              "message_count": len(self.messages),
              "goal": self.goal,
              "summary": self.summary,
              "key_conclusions": self.key_conclusions,
              "plan": self.plan,
              "assigned_team_id": self.assigned_team_id,
              "created_at": self.created_at,
              "started_at": self.started_at,
              "ended_at": self.ended_at,
          }
          if include_messages:
              d["messages"] = [m.to_dict() for m in self.messages]
          return d
  
  
  @dataclass
  class Plaza:
      """智能体广场 — 维特鲁威环形议事空间.
  
      几何参数:
      - diameter: 广场直径 D
      - height: 穹顶高度 H = D/2 (维特鲁威声学公式)
      - oculus_diameter: 穹顶开孔直径 (万神殿 Oculus)
      - niche_count: 壁龛数量 (固定 12)
      - seat_tiers: 座席层数 (固定 3)
      """
      id: str = field(default_factory=lambda: uuid4().hex[:12])
      name: str = ""
      description: str = ""
  
      # 维特鲁威几何参数
      diameter: float = 60.0            # 广场直径 D (米)
      height: float = 30.0              # H = D/2
      oculus_diameter: float = 9.0      # 穹顶开孔直径
      niche_count: int = 12             # 12 个壁龛
      seat_tiers: int = 3               # 三层座席
  
      # 参与者与讨论
      participants: Dict[str, Participant] = field(default_factory=dict)
      discussions: Dict[str, Discussion] = field(default_factory=dict)
  
      # 数字孪生层模式
      visual_mode: str = "modern"       # modern | rome_320ad | senedd
  
      created_at: str = field(
          default_factory=lambda: datetime.now(timezone.utc).isoformat()
      )
      metadata: Dict[str, Any] = field(default_factory=dict)
  
      def to_dict(self, include_details: bool = False) -> Dict[str, Any]:
          d = {
              "id": self.id,
              "name": self.name,
              "description": self.description,
              "diameter": self.diameter,
              "height": self.height,
              "oculus_diameter": self.oculus_diameter,
              "niche_count": self.niche_count,
              "seat_tiers": self.seat_tiers,
              "visual_mode": self.visual_mode,
              "participant_count": len(self.participants),
              "discussion_count": len(self.discussions),
              "active_discussions": sum(
                  1 for d in self.discussions.values()
                  if d.status in (DiscussionStatus.OPEN, DiscussionStatus.IN_PROGRESS)
              ),
              "created_at": self.created_at,
          }
          if include_details:
              d["participants"] = [p.to_dict() for p in self.participants.values()]
              d["discussions"] = [
                  disc.to_dict() for disc in self.discussions.values()
              ]
          return d
  
  
  # ── 预设话题模板 ──────────────────────────────────────────────
  
  PRESET_TOPICS = [
      {
          "topic": "如何设计一个高效的智能体协作系统？",
          "description": "探讨多智能体系统中的通信协议、任务分配策略和冲突解决机制。",
      },
      {
          "topic": "构建 Agent 广场功能的技术方案讨论",
          "description": "讨论广场的后端架构、实时消息推送、讨论编排逻辑和前端可视化方案。",
      },
      {
          "topic": "代码质量保障的最佳实践",
          "description": "从单元测试、集成测试、代码审查、CI/CD 等维度讨论如何保障代码质量。",
      },
      {
          "topic": "AI 时代的软件架构演进",
          "description": "LLM 驱动的智能体如何改变传统的微服务架构？讨论 Agent-native 架构模式。",
      },
      {
          "topic": "从维特鲁威到数字孪生：建筑智慧的传承",
          "description": "古罗马建筑的比例法则如何启发现代数字空间设计？讨论物理与虚拟的融合。",
      },
  ]
  
  ```
  
  (后续文件因 token 预算已省略)
  
  (后续文件因 token 预算已省略)
  
  (后续文件因 token 预算已省略)
  
  
  ## 前序步骤的产出 (递进式摘要)
  
  ### 步骤 01: pm_decompose
  任务: 定义配置快照协议：固化 transaction_id、版本号、规则体、时间戳等字段，明确原子替换语义和初始化握手流程
  步骤: pm_decompose
  📋 任务: ba472f30-1a6
  🤖 Agent: PM (project_manager)
  📂 工作目录: /Users/panglaohu/Downloads/AgentsGroup2026
  🔧 执行方式: DeepSeek API (直连)
  ────────────────────────────────────────────────────────────
  你是 AgentsGroup2026 系统的 PM (project_manager)。
  你是项目经理 (PM)。请对以下任务进行分解和规划:
  定义配置快照协议：固化 transaction_id、版本号、规则体、时间戳等字段，明确原子替换语义和初始化握手流程
  ## 📂 项目上下文 (系统自动预加载)
  ### 项目文件结构 (src/ 目录)
  ### 文件: `src/backend/agents/chat_harness.py`
  ### 文件: `src/backend/agents/hermes_research.py`
  ### 文件: `src/backend/agents/models.py`
  **子任务拆解:**
    - *任务ID:** `TASK-CONFIG-SNAPSHOT-PROTOCOL`
    - *任务标题:** 定义配置快照协议：固化 transaction_id、版本号、规则体、时间戳等字段，明确原子替换语义和初始化握手流程
    - *指派人:** Architect
    - *状态:** 待分解
    - **固化数据模型:** 定义 `ConfigSnapshot` 的核心字段，包括 `transaction_id`, `version`, `rules`, `timestamp` 等。
    - **明确原子替换语义:** 定义如何通过一个快照原子性地替换当前生效的配置，确保配置更新不会出现中间状态。
    - **定义初始化握手流程:** 定义系统启动或新节点加入时，如何通过快照协议与配置中心（或主节点）进行同步，确保所有节点配置一致。
    - **负责人:** Architect
  
  ### 步骤 02: research (完整产出)
  
  # 研究分析 — researcher
  
  任务: 定义配置快照协议：固化 transaction_id、版本号、规则体、时间戳等字段，明确原子替换语义和初始化握手流程
  步骤: research
  Agent: build_researcher
  
  ---
  
  📋 任务: ba472f30-1a6
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
    定义配置快照协议：固化 transaction_id、版本号、规则体、时间戳等字段，明确原子替换语义和初始化握手流程
    Architect
    
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
    src/docs/agent_handoffs/d553cde7-ee1_executor_started_20260506T101306.md
    src/docs/agent_handoffs/d87c964b-c06_architecture_20260503T045321.md
    src/docs/agent_handoffs/d87c964b-c06_pm_decompose_20260503T045236.md
    src/docs/agent_handoffs/d87c964b-c06_research_20260503T045251.md
    src/docs/agent_handoffs/d87c964b-c06_task_init_20260503T045211.md
    src/docs/agent_handoffs/dbf24d0c-5cc_architecture_20260503T235205.md
    src/docs/agent_handoffs/dbf24d0c-5cc_deploy_FAILED_20260504T012356.md
    src/docs/agent_handoffs/dbf24d0c-5cc_develop_20260503T235646.md
    src/docs/agent_handoffs/dbf24d0c-5cc_develop_20260504T004702.md
    src/docs/agent_handoffs/dbf24d0c-5cc_develop_FAILED_20260504T001109.md
    src/docs/agent_handoffs/dbf24d0c-5cc_executor_started_20260503T234950.md
    src/docs/agent_handoffs/dbf24d0c-5cc_pm_decompose_20260503T235020.md
    src/docs/agent_handoffs/dbf24d0c-5cc_research_20260503T235105.md
    src/docs/agent_handoffs/dbf24d0c-5cc_test_FAILED_20260504T000157.md
    src/docs/agent_handoffs/dbf24d0c-5cc_test_FAILED_20260504T002112.md
    src/docs/agent_handoffs/dbf24d0c-5cc_test_FAILED_20260504T012326.md
    src/docs/agent_handoffs/dd0e3569-eb0_architecture_20260503T114837.md
    src/docs/agent_handoffs/dd0e3569-eb0_deploy_FAILED_20260503T121257.md
    src/docs/agent_handoffs/dd0e3569-eb0_develop_20260503T115309.md
    src/docs/agent_handoffs/dd0e3569-eb0_develop_FAILED_20260503T120023.md
    src/docs/agent_handoffs/dd0e3569-eb0_develop_FAILED_20260503T120906.md
    src/docs/agent_handoffs/dd0e3569-eb0_executor_started_20260503T114547.md
    src/docs/agent_handoffs/dd0e3569-eb0_pm_decompose_20260503T114622.md
    src/docs/agent_handoffs/dd0e3569-eb0_research_20260503T114712.md
    src/docs/agent_handoffs/dd0e3569-eb0_test_20260503T115557.md
    src/docs/agent_handoffs/dd0e3569-eb0_test_FAILED_20260503T120434.md
    src/docs/agent_handoffs/dd0e3569-eb0_test_FAILED_20260503T121242.md
    src/docs/workflow_artifacts/1ce78c0e-062_architecture.md
    src/docs/workflow_artifacts/1ce78c0e-062_deploy.md
    src/docs/workflow_artifacts/1ce78c0e-062_develop.md
    src/docs/workflow_artifacts/1ce78c0e-062_pm_decompose.md
    src/docs/workflow_artifacts/1ce78c0e-062_research.md
    src/docs/workflow_artifacts/1ce78c0e-062_test.md
    src/docs/workflow_artifacts/38e22004-b64_architecture.md
    src/docs/workflow_artifacts/38e22004-b64_pm_decompose.md
    src/docs/workflow_artifacts/38e22004-b64_research.md
    src/docs/workflow_artifacts/7c934759-39e_architecture.md
    src/docs/workflow_artifacts/7c934759-39e_deploy.md
    src/docs/workflow_artifacts/7c934759-39e_develop.md
    src/docs/workflow_artifacts/7c934759-39e_pm_decompose.md
    src/docs/workflow_artifacts/7c934759-39e_research.md
    src/docs/workflow_artifacts/7c934759-39e_test.md
    src/docs/workflow_artifacts/ba3b66b1-a77_architecture.md
    src/docs/workflow_artifacts/ba3b66b1-a77_deploy.md
    ... (共 169 个 src/ 文件)
    
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
            system_prompt="",  # Built dynamically via build_research_
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

# 配置快照协议 — 技术方案设计

## 1. 概述

### 1.1 目标
定义一套**配置快照协议**，用于 AgentsGroup2026 系统中所有配置（团队配置、智能体配置、工具配置、技能配置等）的版本化管理和原子替换。

### 1.2 核心需求
- **固化字段**：`transaction_id`、`version`、`rules`（规则体）、`timestamp`
- **原子替换语义**：一次快照替换 = 完整替换当前配置，无中间状态
- **初始化握手流程**：系统启动/节点加入时，通过快照协议同步配置

### 1.3 设计原则
- **不可变性**：快照一旦创建不可修改，只能通过新快照替换
- **线性版本**：版本号单调递增，无分支
- **幂等性**：相同快照多次应用结果一致
- **可追溯**：每个快照记录谁在何时做了什么变更

---

## 2. 数据模型

### 2.1 ConfigSnapshot 核心模型

```python
# 新增文件: src/backend/agents/config_snapshot.py

from __future__ import annotations

import json
import hashlib
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from uuid import uuid4


class SnapshotStatus(str, Enum):
    """快照生命周期状态"""
    PENDING = "pending"           # 创建但未应用
    APPLIED = "applied"           # 已成功应用
    REJECTED = "rejected"         # 被拒绝（版本冲突等）
    ROLLED_BACK = "rolled_back"   # 已回滚


class ConfigDomain(str, Enum):
    """配置域 — 标识快照所属的配置类别"""
    TEAM = "team"                 # 团队配置
    AGENT = "agent"               # 智能体配置
    TOOL = "tool"                 # 工具配置
    SKILL = "skill"               # 技能配置
    MODEL = "model"               # 模型配置
    SYSTEM = "system"             # 系统级配置
    CHANNEL = "channel"           # 通道配置
    PLAZA = "plaza"               # 广场配置


@dataclass
class ConfigSnapshot:
    """
    配置快照 — 不可变版本化配置单元
    
    核心设计：
    - 每个快照代表一次完整的配置替换
    - 快照之间通过 version 形成线性序列
    - 应用快照 = 原子替换目标配置
    """
    # ── 标识字段 ──
    snapshot_id: str = field(default_factory=lambda: uuid4().hex[:16])
    transaction_id: str = ""          # 事务ID，关联变更操作
    domain: ConfigDomain = ConfigDomain.SYSTEM  # 配置域
    config_key: str = ""              # 配置键（如 team_id, agent_id）
    
    # ── 版本控制 ──
    version: int = 1                  # 版本号（单调递增）
    parent_version: int = 0           # 父版本号（0 表示初始版本）
    
    # ── 规则体 ──
    rules: Dict[str, Any] = field(default_factory=dict)  # 完整配置内容
    
    # ── 元数据 ──
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    created_by: str = ""              # 创建者（agent_id 或 user_id）
    description: str = ""             # 变更描述
    checksum: str = ""                # 内容校验和（SHA256）
    status: SnapshotStatus = SnapshotStatus.PENDING
    
    # ── 签名/认证（可选） ──
    signature: Optional[str] = None   # 数字签名
    
    def __post_init__(self) -> None:
        """自动计算校验和"""
        if not self.checksum:
            self.checksum = self._compute_checksum()
    
    def _compute_checksum(self) -> str:
        """计算规则体的 SHA256 校验和"""
        content = json.dumps(self.rules, sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(content.encode('utf-8')).hexdigest()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "snapshot_id": self.snapshot_id,
            "transaction_id": self.transaction_id,
            "domain": self.domain.value,
            "config_key": self.config_key,
            "version": self.version,
            "parent_version": self.parent_version,
            "rules": self.rules,
            "timestamp": self.timestamp,
            "created_by": self.created_by,
            "description": self.description,
            "checksum": self.checksum,
            "status": self.status.value,
            "signature": self.signature,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ConfigSnapshot":
        """从字典重建快照"""
        return cls(
            snapshot_id=data.get("snapshot_id", uuid4().hex[:16]),
            transaction_id=data.get("transaction_id", ""),
            domain=ConfigDomain(data.get("domain", "system")),
            config_key=data.get("config_key", ""),
            version=data.get("version", 1),
            parent_version=data.get("parent_version", 0),
            rules=data.get("rules", {}),
            timestamp=data.get("timestamp", datetime.now(timezone.utc).isoformat()),
            created_by=data.get("created_by", ""),
            description=data.get("description", ""),
            checksum=data.get("checksum", ""),
            status=SnapshotStatus(data.get("status", "pending")),
            signature=data.get("signature"),
        )
```

### 2.2 快照链模型

```python
@dataclass
class SnapshotChain:
    """
    快照链 — 管理某个配置键的版本历史
    
    维护一个线性版本序列，支持：
    - 追加新快照（版本号递增）
    - 查询当前生效快照
    - 回滚到指定版本
    - 验证链的完整性
    """
    domain: ConfigDomain = ConfigDomain.SYSTEM
    config_key: str = ""
    snapshots: Dict[int, ConfigSnapshot] = field(default_factory=dict)  # version -> snapshot
    current_version: int = 0
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    updated_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    
    def append(self, snapshot: ConfigSnapshot) -> bool:
        """
        追加新快照到链尾
        
        原子替换语义：
        - 新快照的 version 必须 = current_version + 1
        - 新快照的 parent_version 必须 = current_version
        - 成功后 current_version 更新为新版本
        """
        expected_version = self.current_version + 1
        if snapshot.version != expected_version:
            raise ValueError(
                f"版本冲突：期望 {expected_version}，实际 {snapshot.version}"
            )
        if snapshot.parent_version != self.current_version:
            raise ValueError(
                f"父版本冲突：期望 {self.current_version}，实际 {snapshot.parent_version}"
            )
        
        # 校验内容完整性
        expected_checksum = snapshot._compute_checksum()
        if snapshot.checksum != expected_checksum:
            raise ValueError("校验和不匹配：快照内容已被篡改")
        
        self.snapshots[snapshot.version] = snapshot
        self.current_version = snapshot.version
        self.updated_at = datetime.now(timezone.utc).isoformat()
        return True
    
    def get_current(self) -> Optional[ConfigSnapshot]:
        """获取当前生效的快照"""
        if self.current_version == 0:
            return None
        return self.snapshots.get(self.current_version)
    
    def rollback_to(self, target_version: int) -> Optional[ConfigSnapshot]:
        """
        回滚到指定版本
        
        回滚语义：
        - 创建一个新的快照，其 rules 等于目标版本的 rules
        - 新快照的 version = current_version + 1
        - 新快照的 parent_version = target_version
        """
        target = self.snapshots.get(target_version)
        if not target:
            return None
        
        rollback_snapshot = ConfigSnapshot(
            transaction_id=f"rollback_to_v{target_version}",
            domain=self.domain,
            config_key=self.config_key,
            version=self.current_version + 1,
            parent_version=target_version,
            rules=dict(target.rules),  # 深拷贝规则体
            created_by="system",
            description=f"回滚到版本 {target_version}",
        )
        self.append(rollback_snapshot)
        return rollback_snapshot
    
    def verify_chain_integrity(self) -> bool:
        """验证整个快照链的完整性"""
        sorted_versions = sorted(self.snapshots.keys())
        if not sorted_versions:
            return True
        
        # 检查版本连续性
        for i, v in enumerate(sorted_versions):
            if i > 0 and v != sorted_versions[i-1] + 1:
                return False
        
        # 检查父版本链接
        for v in sorted_versions[1:]:
            snap = self.snapshots[v]
            if snap.parent_version != v - 1:
                return False
        
        # 检查每个快照的校验和
        for snap in self.snapshots.values():
            if snap.checksum != snap._compute_checksum():
                return False
        
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "domain": self.domain.value,
            "config_key": self.config_key,
            "current_version": self.current_version,
            "snapshot_count": len(self.snapshots),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
```

---

## 3. 原子替换语义

### 3.1 核心原则

```
原子替换 = 一次快照应用 = 完整替换当前配置
```

- **全量替换**：快照中的 `rules` 包含完整的配置内容，不是增量 diff
- **无中间状态**：应用过程中，要么旧配置完全生效，要么新配置完全生效
- **失败回滚**：如果应用失败，配置保持应用前的状态

### 3.2 应用流程

```python
class SnapshotApplier:
    """
    快照应用器 — 负责将快照原子性地应用到目标配置存储
    
    使用文件锁 + 临时文件 + 重命名策略实现原子替换
    """
    
    def __init__(self, storage_path: str):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
    
    def apply_snapshot(self, snapshot: ConfigSnapshot) -> bool:
        """
        原子应用快照
        
        步骤：
        1. 获取配置锁
        2. 验证版本号
        3. 写入临时文件
        4. 原子重命名
        5. 更新快照链
        6. 释放锁
        """
        config_file = self._get_config_path(snapshot.domain, snapshot.config_key)
        lock_file = config_file.with_suffix(config_file.suffix + ".lock")
        
        try:
            # 1. 获取文件锁
            with self._acquire_lock(lock_file):
                # 2. 验证当前版本
                current_chain = self._load_chain(snapshot.domain, snapshot.config_key)
                if current_chain.current_version != snapshot.parent_version:
                    snapshot.status = SnapshotStatus.REJECTED
                    self._save_snapshot(snapshot)
                    return False
                
                # 3. 写入临时文件
                temp_file = config_file.with_suffix(config_file.suffix + ".tmp")
                with open(temp_file, 'w', encoding='utf-8') as f:
                    json.dump(snapshot.rules, f, ensure_ascii=False, indent=2)
                
                # 4. 原子重命名（POSIX 原子操作）
                temp_file.rename(config_file)
                
                # 5. 更新快照链
                current_chain.append(snapshot)
                snapshot.status = SnapshotStatus.APPLIED
                self._save_chain(current_chain)
                self._save_snapshot(snapshot)
                
                return True
                
        except Exception as e:
            logger.error(f"应用快照失败: {e}")
            snapshot.status = SnapshotStatus.REJECTED
            self._save_snapshot(snapshot)
            return False
        finally:
            self._release_lock(lock_file)
            # 清理临时文件
            temp_file = config_file.with_suffix(config_file.suffix + ".tmp")
            if temp_file.exists():
                temp_file.unlink()
```

---

## 4. 初始化握手流程

### 4.1 握手协议概述

```
节点 A（新加入）                   节点 B（配置中心/主节点）
    |                                      |
    |--- 1. HANDSHAKE_REQUEST ----------->|
    |    {node_id, current_versions}       |
    |                                      |
    |<-- 2. HANDSHAKE_RESPONSE ------------|
    |    {status, required_snapshots}      |
    |                                      |
    |--- 3. SNAPSHOT_REQUEST ------------->|
    |    {snapshot_ids}                    |
    |                                      |
    |<-- 4. SNAPSHOT_RESPONSE -------------|
    |    {snapshots: [...]}                |
    |                                      |
    |--- 5. APPLY_CONFIRM ---------------->|
    |    {applied_versions}                |
    |                                      |
```

### 4.2 握手消息定义

```python
@dataclass
class HandshakeRequest:
    """握手请求 — 节点向配置中心发起同步"""
    node_id: str
    node_type: str  # "primary" | "replica" | "agent"
    current_versions: Dict[str, int]  # {domain:config_key: version}
    capabilities: List[str] = field(default_factory=list)
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


@dataclass
class HandshakeResponse:
    """握手响应 — 配置中心返回需要同步的快照列表"""
    status: str  # "ok" | "outdated" | "error"
    required_snapshots: List[Dict[str, Any]] = field(default_factory=list)
    # [{domain, config_key, from_version, to_version}]
    message: str = ""
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


@dataclass
class SnapshotSyncRequest:
    """快照同步请求 — 请求具体的快照内容"""
    node_id: str
    requests: List[Dict[str, Any]] = field(default_factory=list)
    # [{domain, config_key, version}]


@dataclass
class SnapshotSyncResponse:
    """快照同步响应 — 返回快照内容"""
    status: str
    snapshots: List[ConfigSnapshot] = field(default_factory=list)
    missing_snapshots: List[Dict[str, Any]] = field(default_factory=list)
```

### 4.3 握手实现

```python
class HandshakeProtocol:
    """
    初始化握手协议实现
    
    负责：
    - 节点启动时与配置中心同步
    - 检测版本差异
    - 拉取缺失的快照
    - 应用快照使节点达到最新状态
    """
    
    def __init__(self, node_id: str, storage: SnapshotStorage):
        self.node_id = node_id
        self.storage = storage
    
    async def perform_handshake(
        self, 
        config_center_url: str
    ) -> bool:
        """
        执行完整的握手流程
        
        返回 True 表示同步成功，节点已处于最新状态
        """
        # 1. 收集本地版本信息
        local_versions = self.storage.get_all_current_versions()
        
        # 2. 发送握手请求
        request = HandshakeRequest(
            node_id=self.node_id,
            node_type="agent",
            current_versions=local_versions,
        )
        
        response = await self._send_handshake(config_center_url, request)
        
        if response.status == "ok":
            logger.info("节点已是最新状态，无需同步")
            return True
        
        if response.status == "error":
            logger.error(f"握手失败: {response.message}")
            return False
        
        # 3. 拉取缺失的快照
        for req in response.required_snapshots:
            snapshots = await self._fetch_snapshots(
                config_center_url,
                req["domain"],
                req["config_key"],
                req["from_version"],
                req["to_version"],
            )
            
            # 4. 按版本顺序应用快照
            for snapshot in sorted(snapshots, key=lambda s: s.version):
                success = self.storage.apply_snapshot(snapshot)
                if not success:
                    logger.error(
                        f"应用快照失败: {snapshot.snapshot_id}"
                    )
                    return False
        
        # 5. 发送确认
        await self._send_confirm(config_center_url)
        
        logger.info("握手同步完成")
        return True
    
    async def _send_handshake(
        self, 
        url: str, 
        request: HandshakeRequest
    ) -> HandshakeResponse:
        """发送握手请求到配置中心"""
        # 实现 HTTP 调用
        pass
    
    async def _fetch_snapshots(
        self,
        url: str,
        domain: str,
        config_key: str,
        from_version: int,
        to_version: int,
    ) -> List[ConfigSnapshot]:
        """拉取指定范围的快照"""
        # 实现批量拉取
        pass
```

---

## 5. 存储层设计

### 5.1 文件存储结构

```
config_snapshots/
├── chains/
│   ├── team_team-001.json          # 团队配置快照链
│   ├── agent_agent-001.json        # 智能体配置快照链
│   └── system_global.json          # 系统级配置快照链
├── snapshots/
│   ├── abc123...                   # 快照文件（按 snapshot_id 存储）
│   ├── def456...
│   └── ...
└── index.json                      # 索引文件
```

### 5.2 存储实现

```python
class SnapshotStorage:
    """
    快照存储 — 管理快照的持久化
    
    使用文件系统存储，支持：
    - 快照的创建和读取
    - 快照链的管理
    - 版本查询
    - 垃圾回收（旧版本清理）
    """
    
    def __init__(self, base_path: str = "data/config_snapshots"):
        self.base_path = Path(base_path)
        self.chains_path = self.base_path / "chains"
        self.snapshots_path = self.base_path / "snapshots"
        self.index_path = self.base_path / "index.json"
        
        self.chains_path.mkdir(parents=True, exist_ok=True)
        self.snapshots_path.mkdir(parents=True, exist_ok=True)
        
        self._load_index()
    
    def _load_index(self) -> None:
        """加载索引"""
        if self.index_path.exists():
            with open(self.index_path, 'r') as f:
                self.index = json.load(f)
        else:
            self.index = {}
    
    def _save_index(self) -> None:
        """保存索引"""
        with open(self.index_path, 'w') as f:
            json.dump(self.index, f, indent=2)
    
    def _chain_path(self, domain: ConfigDomain, config_key: str) -> Path:
        """获取快照链文件路径"""
        return self.chains_path / f"{domain.value}_{config_key}.json"
    
    def _snapshot_path(self, snapshot_id: str) -> Path:
        """获取快照文件路径"""
        return self.snapshots_path / f"{snapshot_id}.json"
    
    def save_snapshot(self, snapshot: ConfigSnapshot) -> None:
        """保存单个快照"""
        path = self._snapshot_path(snapshot.snapshot_id)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(snapshot.to_dict(), f, ensure_ascii=False, indent=2)
    
    def load_snapshot(self, snapshot_id: str) -> Optional[ConfigSnapshot]:
        """加载单个快照"""
        path = self._snapshot_path(snapshot_id)
        if not path.exists():
            return None
        with open(path, 'r') as f:
            data = json.load(f)
        return ConfigSnapshot.from_dict(data)
    
    def save_chain(self, chain: SnapshotChain) -> None:
        """保存快照链"""
        path = self._chain_path(chain.domain, chain.config_key)
        chain_data = {
            "domain": chain.domain.value,
            "config_key": chain.config_key,
            "current_version": chain.current_version,
            "snapshot_ids": {
                str(v): s.snapshot_id 
                for v, s in chain.snapshots.items()
            },
            "created_at": chain.created_at,
            "updated_at": chain.updated_at,
        }
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(chain_data, f, ensure_ascii=False, indent=2)
        
        # 更新索引
        index_key = f"{chain.domain.value}:{chain.config_key}"
        self.index[index_key] = {
            "current_version": chain.current_version,
            "snapshot_count": len(chain.snapshots),
            "updated_at": chain.updated_at,
        }
        self._save_index()
    
    def load_chain(self, domain: ConfigDomain, config_key: str) -> SnapshotChain:
        """加载快照链"""
        path = self._chain_path(domain, config_key)
        if not path.exists():
            return SnapshotChain(domain=domain, config_key=config_key)
        
        with open(path, 'r') as f:
            chain_data = json.load(f)
        
        chain = SnapshotChain(
            domain=ConfigDomain(chain_data["domain"]),
            config_key=chain_data["config_key"],
            current_version=chain_data["current_version"],
            created_at=chain_data.get("created_at", ""),
            updated_at=chain_data.get("updated_at", ""),
        )
        
        # 加载快照
        for version_str, snapshot_id in chain_data.get("snapshot_ids", {}).items():
            snapshot = self.load_snapshot(snapshot_id)
            if snapshot:
                chain.snapshots[int(version_str)] = snapshot
        
        return chain
    
    def get_all_current_versions(self) -> Dict[str, int]:
        """获取所有配置的当前版本号"""
        return {
            key: info["current_version"]
            for key, info in self.index.items()
        }
```

---

## 6. API 接口设计

### 6.1 REST API

```python
# 新增文件: src/backend/agents/config_snapshot_api.py

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

router = APIRouter(prefix="/api/v1/config-snapshots", tags=["config-snapshots"])


# ── 请求/响应模型 ──

class CreateSnapshotRequest(BaseModel):
    transaction_id: str
    domain: str
    config_key: str
    rules: Dict[str, Any]
    created_by: str = "system"
    description: str = ""


class ApplySnapshotRequest(BaseModel):
    snapshot_id: str


class RollbackRequest(BaseModel):
    domain: str
    config_key: str
    target_version: int


class HandshakeRequest(BaseModel):
    node_id: str
    node_type: str = "agent"
    current_versions: Dict[str, int] = {}


# ── API 端点 ──

@router.post("/snapshots", response_model=Dict[str, Any])
async def create_snapshot(request: CreateSnapshotRequest):
    """创建配置快照"""
    snapshot = ConfigSnapshot(
        transaction_id=request.transaction_id,
        domain=ConfigDomain(request.domain),
        config_key=request.config_key,
        version=0,  # 由 applier 自动设置
        parent_version=0,
        rules=request.rules,
        created_by=request.created_by,
        description=request.description,
    )
    # 保存快照
    storage.save_snapshot(snapshot)
    return snapshot.to_dict()


@router.post("/apply", response_model=Dict[str, Any])
async def apply_snapshot(request: ApplySnapshotRequest):
    """原子应用快照"""
    snapshot = storage.load_snapshot(request.snapshot_id)
    if not snapshot:
        raise HTTPException(status_code=404, detail="快照不存在")
    
    applier = SnapshotApplier(storage_path="data/config_snapshots")
    success = applier.apply_snapshot(snapshot)
    
    return {
        "success": success,
        "snapshot": snapshot.to_dict(),
    }


@router.post("/rollback", response_model=Dict[str, Any])
async def rollback_config(request: RollbackRequest):
    """回滚配置到指定版本"""
    chain = storage.load_chain(
        ConfigDomain(request.domain), 
        request.config_key
    )
    rollback_snapshot = chain.rollback_to(request.target_version)
    if not rollback_snapshot:
        raise HTTPException(status_code=404, detail="目标版本不存在")
    
    # 应用回滚快照
    applier = SnapshotApplier(storage_path="data/config_snapshots")
    success = applier.apply_snapshot(rollback_snapshot)
    
    return {
        "success": success,
        "rollback_snapshot": rollback_snapshot.to_dict(),
    }


@router.get("/chains/{domain}/{config_key}", response_model=Dict[str, Any])
async def get_config_chain(domain: str, config_key: str):
    """获取配置的快照链信息"""
    chain = storage.load_chain(ConfigDomain(domain), config_key)
    return chain.to_dict()


@router.get("/chains/{domain}/{config_key}/versions", response_model=List[Dict[str, Any]])
async def get_config_versions(domain: str, config_key: str):
    """获取配置的所有版本"""
    chain = storage.load_chain(ConfigDomain(domain), config_key)
    return [
        {
            "version": v,
            "snapshot_id": s.snapshot_id,
            "timestamp": s.timestamp,
            "created_by": s.created_by,
            "description": s.description,
            "status": s.status.value,
        }
        for v, s in sorted(chain.snapshots.items())
    ]


@router.post("/handshake", response_model=Dict[str, Any])
async def handshake(request: HandshakeRequest):
    """初始化握手 — 节点同步配置"""
    protocol = HandshakeProtocol(
        node_id=request.node_id,
        storage=storage,
    )
    
    # 计算需要同步的快照
    required = []
    for key, local_version in request.current_versions.items():
        domain_str, config_key = key.split(":", 1)
        chain = storage.load_chain(ConfigDomain(domain_str), config_key)
        if chain.current_version > local_version:
            required.append({
                "domain": domain_str,
                "config_key": config_key,
                "from_version": local_version,
                "to_version": chain.current_version,
            })
    
    return {
        "status": "ok" if not required else "outdated",
        "required_snapshots": required,
        "message": f"需要同步 {len(required)} 个配置",
    }
```

---

## 7. 与现有系统的集成

### 7.1 需要修改的文件

| 文件 | 修改内容 |
|------|----------|
| `src/backend/agents/__init__.py` | 导出 `ConfigSnapshot`, `SnapshotChain` 等新模型 |
| `src/backend/agents/models.py` | 在 `AgentTeam` 中添加 `config_version` 字段 |
| `src/backend/agents/team_store.py` | 集成快照协议进行团队配置的版本管理 |
| `src/backend/agents/agent_team_api.py` | 添加配置快照相关的 API 端点 |
| `src/backend/main.py` | 注册新的路由 |

### 7.2 集成点

```python
# 在 team_store.py 中集成快照协议

class TeamStore:
    """团队存储 — 集成配置快照协议"""
    
    def __init__(self, storage_path: str = "data"):
        self.snapshot_storage = SnapshotStorage(
            base_path=os.path.join(storage_path, "config_snapshots")
        )
        self.snapshot_applier = SnapshotApplier(
            storage_path=os.path.join(storage_path, "config_snapshots")
        )
    
    def save_team(self, team: AgentTeam) -> bool:
        """保存团队配置（通过快照协议）"""
        # 创建快照
        snapshot = ConfigSnapshot(
            transaction_id=f"save_team_{team.team_id}",
            domain=ConfigDomain.TEAM,
            config_key=team.team_id,
            version=0,  # 由 applier 设置
            parent_version=team.config_version or 0,
            rules=team.to_dict(),
            created_by="system",
            description=f"保存团队 {team.name} 配置",
        )
        
        # 原子应用
        success = self.snapshot_applier.apply_snapshot(snapshot)
        if success:
            team.config_version = snapshot.version
        
        return success
    
    def load_team(self, team_id: str) -> Optional[AgentTeam]:
        """加载团队配置"""
        chain = self.snapshot_storage.load_chain(
            ConfigDomain.TEAM, team_id
        )
        current = chain.get_current()
        if not current:
            return None
        
        # 从快照重建团队
        team_data = current.rules
        team = AgentTeam.from_dict(team_data)
        team.config_version = current.version
        return team
```

---

## 8. 实施指南

### 8.1 实施步骤

1. **创建数据模型**（第1天）
   - 创建 `src/backend/agents/config_snapshot.py`
   - 实现 `ConfigSnapshot`, `SnapshotChain`, `SnapshotStatus`, `ConfigDomain`

2. **实现存储层**（第1-2天）
   - 实现 `SnapshotStorage` 类
   - 实现文件读写、索引管理

3. **实现原子替换**（第2天）
   - 实现 `SnapshotApplier` 类
   - 实现文件锁 + 临时文件 + 重命名策略

4. **实现握手协议**（第2-3天）
   - 实现 `HandshakeProtocol` 类
   - 实现握手消息模型

5. **创建 API 端点**（第3天）
   - 创建 `src/backend/agents/config_snapshot_api.py`
   - 实现所有 REST API

6. **集成现有系统**（第3-4天）
   - 修改 `team_store.py` 集成快照协议
   - 修改 `agent_team_api.py` 添加新端点
   - 注册路由

7. **测试**（第4天）
   - 单元测试：快照创建、应用、回滚
   - 集成测试：握手流程
   - 压力测试：并发快照应用

### 8.2 测试用例

```python
# 测试文件: tests/test_config_snapshot.py

def test_create_snapshot():
    """测试快照创建"""
    snapshot = ConfigSnapshot(
        transaction_id="txn_001",
        domain=ConfigDomain.TEAM,
        config_key="team_001",
        rules={"name": "Test Team", "agents": []},
        created_by="admin",
    )
    assert snapshot.version == 1
    assert snapshot.checksum is not None
    assert snapshot.status == SnapshotStatus.PENDING

def test_atomic_apply():
    """测试原子替换语义"""
    storage = SnapshotStorage(base_path="/tmp/test_snapshots")
    applier = SnapshotApplier(storage_path="/tmp/test_snapshots")
    
    # 创建初始快照
    snap1 = ConfigSnapshot(
        transaction_id="txn_001",
        domain=ConfigDomain.TEAM,
        config_key="team_001",
        rules={"name": "Team A", "agents": ["agent_1"]},
    )
    assert applier.apply_snapshot(snap1)
    
    # 创建新快照（原子替换）
    snap2 = ConfigSnapshot(
        transaction_id="txn_002",
        domain=ConfigDomain.TEAM,
        config_key="team_001",
        version=2,
        parent_version=1,
        rules={"name": "Team B", "agents": ["agent_1", "agent_2"]},
    )
    assert applier.apply_snapshot(snap2)
    
    # 验证当前配置已被完整替换
    chain = storage.load_chain(ConfigDomain.TEAM, "team_001")
    current = chain.get_current()
    assert current.rules["name"] == "Team B"
    assert len(current.rules["agents"]) == 2

def test_handshake():
    """测试初始化握手"""
    # 模拟配置中心
    center_storage = SnapshotStorage(base_path="/tmp/center_snapshots")
    center_storage.save_snapshot(snap1)
    center_storage.save_chain(chain1)
    
    # 模拟新节点
    node_storage = SnapshotStorage(base_path="/tmp/node_snapshots")
    protocol = HandshakeProtocol(node_id="node_001", storage=node_storage)
    
    # 执行握手
    success = protocol.perform_handshake(config_center_url="http://center:8000")
    assert success
    
    # 验证节点已同步
    node_chain = node_storage.load_chain(ConfigDomain.TEAM, "team_001")
    assert node_chain.current_version == 2
```

---

## 9. 总结

### 9.1 关键设计决策

| 决策 | 选择 | 理由 |
|------|------|------|
| 版本策略 | 线性单调递增 | 简单可靠，无分支冲突 |
| 替换语义 | 全量替换 | 避免增量 diff 的复杂性和一致性问题 |
| 存储格式 | JSON 文件 | 与现有系统一致，便于调试 |
| 原子性保证 | 文件锁 + 临时文件 + 重命名 | POSIX 原子操作，无需外部依赖 |
| 握手协议 | 拉取模式（Pull） | 新节点主动同步，配置中心无状态 |

### 9.2 安全考虑

- **校验和**：每个快照包含 SHA256 校验和，防止内容篡改
- **版本验证**：应用快照时验证 parent_version，防止并发冲突
- **文件锁**：使用文件锁防止并发写入
- **签名支持**：预留数字签名字段，未来可扩展

### 9.3 未来扩展

- **分布式支持**：使用 etcd/Consul 替代文件锁
- **增量同步**：支持只同步差异部分（大配置场景）
- **配置审计**：记录每次配置变更的详细审计日志
- **配置模板**：支持从模板创建快照

────────────────────────────────────────────────────────────
✅ deepseek-chat 完成
