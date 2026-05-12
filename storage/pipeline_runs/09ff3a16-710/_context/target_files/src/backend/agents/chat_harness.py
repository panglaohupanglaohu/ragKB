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
    model: str = "deepseek-v4-flash"
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
            model=os.getenv("AG_LLM_MODEL", "deepseek-v4-flash"),
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
            model=llm.get("model", "deepseek-v4-flash"),
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
            model=getattr(model_config, "name", "deepseek-v4-flash"),
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
        """Persist session to disk. Returns the file path."""
        stored = StoredSession(
            session_id=self.session_id,
            agent_id=self.agent_id,
            messages=[m.content for m in self.messages],
            input_tokens=self.total_usage.input_tokens,
            output_tokens=self.total_usage.output_tokens,
            turn_count=self.turn_count,
        )
        self.transcript.flush()
        path = save_session(stored)
        self.history.add("session_persist", str(path))
        return str(path)

    def replay_messages(self) -> tuple:
        """Replay transcript entries."""
        return self.transcript.replay()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "agent_id": self.agent_id,
            "turn_count": self.turn_count,
            "message_count": len(self.messages),
            "usage": self.total_usage.to_dict(),
            "created_at": self.created_at,
            "transcript_size": len(self.transcript.entries),
            "history_events": len(self.history.events),
            "permission_denials": len(self.permission_denials),
        }


# ═══════════════════════════════════════════════════════════════
# LLM Client — Provider-Agnostic HTTP Client
# ═══════════════════════════════════════════════════════════════


class LLMClient:
    """Lightweight OpenAI-compatible chat completions client.

    Supports any provider that exposes /chat/completions (OpenAI, DeepSeek,
    Ollama, vLLM, OpenRouter, Qwen/DashScope).
    Falls back to a simulated response when no API key is configured.
    """

    def __init__(self, config: ProviderConfig) -> None:
        self._config = config
        self._base_url = config.resolve_base_url()

    async def chat_completion(
        self,
        messages: List[Dict[str, Any]],
        *,
        model: str = "",
        max_tokens: int = 0,
        temperature: float = -1.0,
        tools: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """Call the chat completions endpoint."""
        import aiohttp

        model = model or self._config.model
        max_tokens = max_tokens or self._config.max_tokens
        temp = temperature if temperature >= 0 else self._config.temperature

        payload: Dict[str, Any] = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temp,
        }
        if self._config.thinking:
            payload["thinking"] = self._config.thinking
        if self._config.reasoning_effort:
            payload["reasoning_effort"] = self._config.reasoning_effort
        if tools:
            payload["tools"] = tools

        headers: Dict[str, str] = {
            "Content-Type": "application/json",
        }

        api_key = self._config.api_key
        if not api_key:
            # Try environment fallbacks
            api_key = (
                os.getenv("DEEPSEEK_API_KEY", "")
                or os.getenv("OPENAI_API_KEY", "")
                or os.getenv("ANTHROPIC_API_KEY", "")
                or os.getenv("AG_LLM_API_KEY", "")
            )

        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"

        url = f"{self._base_url}/chat/completions"

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url, json=payload, headers=headers,
                    timeout=aiohttp.ClientTimeout(total=self._config.timeout),
                ) as resp:
                    if resp.status != 200:
                        error_text = await resp.text()
                        return {
                            "error": True,
                            "status": resp.status,
                            "message": error_text[:500],
                        }
                    return await resp.json()
        except Exception as exc:
            return {
                "error": True,
                "status": 0,
                "message": str(exc)[:500],
            }

    async def stream_chat_completion(
        self,
        messages: List[Dict[str, Any]],
        *,
        model: str = "",
        max_tokens: int = 0,
        temperature: float = -1.0,
    ) -> AsyncIterator[Dict[str, Any]]:
        """Stream chat completions via SSE."""
        import aiohttp

        model = model or self._config.model
        max_tokens = max_tokens or self._config.max_tokens
        temp = temperature if temperature >= 0 else self._config.temperature

        payload = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temp,
            "stream": True,
        }
        if self._config.thinking:
            payload["thinking"] = self._config.thinking
        if self._config.reasoning_effort:
            payload["reasoning_effort"] = self._config.reasoning_effort
        headers: Dict[str, str] = {"Content-Type": "application/json"}
        api_key = self._config.api_key or os.getenv("DEEPSEEK_API_KEY", "")
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"

        url = f"{self._base_url}/chat/completions"

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url, json=payload, headers=headers,
                    timeout=aiohttp.ClientTimeout(total=self._config.timeout),
                ) as resp:
                    if resp.status != 200:
                        yield {"error": True, "message": await resp.text()}
                        return
                    async for line in resp.content:
                        text = line.decode("utf-8", errors="replace").strip()
                        if text.startswith("data: "):
                            data = text[6:]
                            if data == "[DONE]":
                                break
                            try:
                                yield json.loads(data)
                            except json.JSONDecodeError:
                                continue
        except Exception as exc:
            yield {"error": True, "message": str(exc)[:500]}


# ═══════════════════════════════════════════════════════════════
# Chat Harness — The Unified Chat Engine
# ═══════════════════════════════════════════════════════════════


class ChatHarness:
    """Unified chat harness for all AgentsGroup2026 agents and bridge commands.

    Architecture (inspired by claw-code Runtime + QueryEngine):
    - Manages sessions per agent
    - Routes to configured LLM provider
    - Handles tool invocation pipeline
    - Tracks usage metrics
    - Supports streaming
    """

    def __init__(
        self,
        default_config: Optional[ProviderConfig] = None,
    ) -> None:
        self._default_config = default_config or ProviderConfig.from_env()
        self._sessions: Dict[str, ChatSession] = {}
        # Per-agent provider overrides (agent_id -> ProviderConfig)
        self._agent_configs: Dict[str, ProviderConfig] = {}
        # Global fallback tools
        self._global_tools: List[Dict[str, Any]] = []
        # Metrics
        self._total_calls: int = 0
        self._total_tokens: int = 0
        self._errors: int = 0

    @classmethod
    def from_settings_file(cls, path: str = "config/settings.json") -> "ChatHarness":
        """Create harness from the project settings file."""
        try:
            settings_path = Path(path)
            if not settings_path.is_absolute():
                repo_root = Path(__file__).resolve().parents[3]
                settings_path = repo_root / settings_path
            with settings_path.open() as f:
                settings = json.load(f)
            config = ProviderConfig.from_settings(settings)
        except (FileNotFoundError, json.JSONDecodeError):
            config = ProviderConfig.from_env()
        return cls(default_config=config)

    # ── Provider Management ──────────────────────────────────

    def set_agent_provider(
        self, agent_id: str, config: ProviderConfig
    ) -> None:
        """Override the LLM provider for a specific agent."""
        self._agent_configs[agent_id] = config

    def get_provider_config(self, agent_id: str = "") -> ProviderConfig:
        """Get the provider config for an agent (or default)."""
        if agent_id and agent_id in self._agent_configs:
            return self._agent_configs[agent_id]
        return self._default_config

    def update_default_provider(
        self,
        provider: str = "",
        api_key: str = "",
        api_base_url: str = "",
        model: str = "",
    ) -> ProviderConfig:
        """Update the default provider config."""
        if provider:
            try:
                self._default_config.provider = LLMProvider(provider)
            except ValueError:
                pass
        if api_key:
            self._default_config.api_key = api_key
        if api_base_url:
            self._default_config.api_base_url = api_base_url
        if model and any(c.isalpha() for c in model):
            self._default_config.model = model
        return self._default_config

    # ── Session Management ───────────────────────────────────

    def get_or_create_session(
        self,
        session_id: str = "",
        agent_id: str = "",
        system_prompt: str = "",
    ) -> ChatSession:
        """Get existing session or create a new one."""
        if session_id and session_id in self._sessions:
            return self._sessions[session_id]
        session = ChatSession(
            session_id=session_id or uuid4().hex[:12],
            agent_id=agent_id,
            system_prompt=system_prompt,
        )
        self._sessions[session.session_id] = session
        return session

    def get_session(self, session_id: str) -> Optional[ChatSession]:
        return self._sessions.get(session_id)

    def list_sessions(self, agent_id: str = "") -> List[ChatSession]:
        if agent_id:
            return [s for s in self._sessions.values() if s.agent_id == agent_id]
        return list(self._sessions.values())

    def persist_session(self, session_id: str) -> str:
        """Persist a session to disk. Returns the file path."""
        session = self._sessions.get(session_id)
        if session is None:
            return ""
        return session.persist()

    def load_persisted_session(self, session_id: str) -> Optional[ChatSession]:
        """Load a previously persisted session from disk."""
        try:
            stored = _load_stored_session(session_id)
        except (FileNotFoundError, OSError):
            return None
        session = ChatSession(
            session_id=stored.session_id,
            agent_id=stored.agent_id,
            turn_count=stored.turn_count,
            total_usage=UsageSummary(
                input_tokens=stored.input_tokens,
                output_tokens=stored.output_tokens,
                total_tokens=stored.input_tokens + stored.output_tokens,
            ),
        )
        for msg in stored.messages:
            session.messages.append(ChatMessage(role="user", content=msg))
        self._sessions[session.session_id] = session
        return session

    def list_persisted_sessions(self) -> List[str]:
        """List all saved session IDs on disk."""
        return _list_stored_sessions()

    def search_persisted_sessions(self, query: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """Cross-session search — mirrors claw-code session_search."""
        results = search_sessions(query, max_results=max_results)
        return [
            {
                "session_id": r.session_id,
                "agent_id": r.agent_id,
                "turn_count": r.turn_count,
                "input_tokens": r.input_tokens,
                "output_tokens": r.output_tokens,
                "message_count": len(r.messages),
            }
            for r in results
        ]

    # ── Port Runtime Integration ─────────────────────────────

    def get_port_runtime(
        self,
        permission_context: Optional[ToolPermissionContext] = None,
    ) -> PortRuntime:
        """Get a PortRuntime instance for prompt routing and session bootstrap."""
        return PortRuntime(permission_context=permission_context)

    async def route_and_chat(
        self,
        prompt: str,
        *,
        agent_id: str = "",
        session_id: str = "",
        system_prompt: str = "",
        permission_context: Optional[ToolPermissionContext] = None,
        route_limit: int = 5,
    ) -> TurnResult:
        """Route prompt through PortRuntime, then chat with context.

        This combines claw-code-parity's routing with our LLM chat:
        1. Route the prompt to find relevant tools/commands
        2. Build context from routed matches
        3. Chat with the LLM using the enriched context
        """
        runtime = self.get_port_runtime(permission_context)
        matches = runtime.route_prompt(prompt, limit=route_limit)

        # Build routing context for the LLM
        if matches:
            match_ctx = "\\n".join(
                f"- [{m.kind}] {m.name} (relevance={m.score})"
                for m in matches
            )
            enriched_prompt = (
                f"用户问题: {prompt}\\n\\n"
                f"系统已匹配以下相关工具/命令:\\n{match_ctx}\\n\\n"
                f"请根据匹配结果和用户问题给出专业回答。"
            )
        else:
            enriched_prompt = prompt

        result = await self.chat(
            enriched_prompt,
            agent_id=agent_id,
            session_id=session_id,
            system_prompt=system_prompt,
        )

        # Record routing in session history
        session = self._sessions.get(result.prompt[:12]) or self._sessions.get(session_id)
        if session:
            session.history.add("routing", f"matches={len(matches)}")

        return result

    # ── Chat (Non-Streaming) ─────────────────────────────────

    async def chat(
        self,
        prompt: str,
        *,
        agent_id: str = "",
        session_id: str = "",
        system_prompt: str = "",
        tools: Optional[List[Dict[str, Any]]] = None,
        model_override: str = "",
    ) -> TurnResult:
        """Execute a single chat turn. This is the main entry point."""
        self._total_calls += 1
        config = self.get_provider_config(agent_id)
        client = LLMClient(config)

        session = self.get_or_create_session(session_id, agent_id, system_prompt)
        session.add_user_message(prompt)
        session.compact_if_needed()

        messages = session.build_openai_messages()
        model = model_override or config.model

        t0 = time.monotonic()
        raw = await client.chat_completion(
            messages, model=model, tools=tools,
        )
        latency = (time.monotonic() - t0) * 1000
