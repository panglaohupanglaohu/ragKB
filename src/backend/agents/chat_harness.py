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
from .budget import UsageRecord, get_budget_guard
from .secret_store import load_default_llm_api_key, resolve_api_key
from .token_context import get_token_ctx

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
    CODEBUDDY = "codebuddy"  # CodeBuddy IDE built-in AI


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
        LLMProvider.CODEBUDDY: "https://api.deepseek.com",
    }, repr=False)

    def resolve_base_url(self) -> str:
        if self.api_base_url:
            return self.api_base_url.strip().rstrip("/")
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
            api_key=resolve_api_key(provider.value),
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

        api_key = resolve_api_key(
            provider.value,
            default_secret=load_default_llm_api_key(),
            plaintext_fallback=llm.get("api_key", ""),
        )

        return cls(
            provider=provider,
            api_key=api_key,
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
            api_key=resolve_api_key(
                provider.value,
                explicit=getattr(model_config, "api_key", ""),
            ),
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

        def _is_codebuddy_param_error(txt: str) -> bool:
            t = (txt or "").lower()
            return "11133" in t or "invalid request parameters" in t

        async def _post_once(session, payload: Dict[str, Any], headers: Dict[str, str], url: str) -> Dict[str, Any]:
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
                if payload.get("stream"):
                    full_content = ""
                    full_json = None
                    async for line in resp.content:
                        text = line.decode(errors='replace')
                        if text.startswith("data: ") and text.strip() != "data: [DONE]":
                            try:
                                chunk = json.loads(text[6:])
                                full_json = chunk  # keep last chunk for metadata
                                delta = chunk.get("choices", [{}])[0].get("delta", {})
                                content = delta.get("content", "")
                                if content:
                                    full_content += content
                            except json.JSONDecodeError:
                                pass
                    if full_json:
                        full_json["choices"][0]["message"] = {"role": "assistant", "content": full_content}
                        return full_json
                    return {"choices": [{"message": {"role": "assistant", "content": full_content}}]}
                return await resp.json(content_type=None)

        model = model or self._config.model
        max_tokens = max_tokens or self._config.max_tokens
        temp = temperature if temperature >= 0 else self._config.temperature

        payload: Dict[str, Any] = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temp,
            "stream": self._config.provider == LLMProvider.CODEBUDDY,  # CodeBuddy requires stream
        }
        if self._config.thinking and self._config.provider != LLMProvider.CODEBUDDY:
            payload["thinking"] = self._config.thinking
        if self._config.reasoning_effort and self._config.provider != LLMProvider.CODEBUDDY:
            payload["reasoning_effort"] = self._config.reasoning_effort
        # Qwen3 models: disable thinking to get content in 'content' field
        if model and "qwen" in model.lower():
            payload["chat_template_kwargs"] = {"enable_thinking": False}
        if tools:
            payload["tools"] = tools

        headers: Dict[str, str] = {
            "Content-Type": "application/json",
        }

        api_key = resolve_api_key(
            self._config.provider.value,
            explicit=self._config.api_key,
        )

        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"

        url = f"{self._base_url}/chat/completions"

        try:
            async with aiohttp.ClientSession() as session:
                result = await _post_once(session, payload, headers, url)
                if (
                    self._config.provider == LLMProvider.CODEBUDDY
                    and result.get("error")
                    and _is_codebuddy_param_error(result.get("message", ""))
                ):
                    # Compatibility fallback for strict parameter validation on CodeBuddy
                    compact_payloads = [
                        {
                            "model": model,
                            "messages": messages,
                            "stream": False,
                        },
                        {
                            "model": model,
                            "messages": [messages[-1]] if messages else messages,
                            "stream": False,
                        },
                    ]
                    for p in compact_payloads:
                        result = await _post_once(session, p, headers, url)
                        if not result.get("error"):
                            break
                return result
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
        if self._config.reasoning_effort and self._config.provider != LLMProvider.CODEBUDDY:
            payload["reasoning_effort"] = self._config.reasoning_effort
        # Qwen3 models: disable thinking to get content in 'content' field
        if model and "qwen" in model.lower():
            payload["chat_template_kwargs"] = {"enable_thinking": False}
        headers: Dict[str, str] = {"Content-Type": "application/json"}
        api_key = resolve_api_key(
            self._config.provider.value,
            explicit=self._config.api_key,
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
        # 全局模型 override：一旦设置，压过 per-agent / per-team / default，
        # 让 plaza / skill 演进 / 棘轮 / 数字孪生等所有走本 harness 的地方统一用它。
        self._global_override: Optional[ProviderConfig] = None
        self._global_override_meta: Dict[str, str] = {}  # {team_id, model_id, name} 供前端回显
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
            with settings_path.open(encoding="utf-8") as f:
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

    def set_global_override(self, config: Optional[ProviderConfig], meta: Optional[Dict[str, str]] = None) -> None:
        """设置/清除全局模型 override。config=None 清除（回退到 per-team/default）。"""
        self._global_override = config
        self._global_override_meta = dict(meta or {}) if config else {}

    def get_global_override(self) -> Optional[ProviderConfig]:
        return self._global_override

    def get_provider_config(self, agent_id: str = "") -> ProviderConfig:
        """Get the provider config for an agent (or default).

        全局 override 优先级最高：设了就压过 per-agent / per-team / default。
        """
        if self._global_override is not None:
            return self._global_override
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

    @staticmethod
    def _estimate_tokens_from_messages(
        messages: List[Dict[str, Any]],
        *,
        max_tokens: int,
    ) -> int:
        char_count = sum(len(str(msg.get("content", ""))) for msg in messages)
        prompt_estimate = max(1, char_count // 4)
        return prompt_estimate + max_tokens

    @staticmethod
    def _estimate_tokens_from_text(text: str) -> int:
        if not text:
            return 0
        return max(1, len(text) // 4)

    @staticmethod
    def _estimate_cost_usd(model: str, total_tokens: int) -> float:
        lowered = (model or "").lower()
        if "gpt-4" in lowered:
            return round((total_tokens / 1000.0) * 0.02, 6)
        if "claude" in lowered:
            return round((total_tokens / 1000.0) * 0.018, 6)
        if "deepseek" in lowered:
            return round((total_tokens / 1000.0) * 0.002, 6)
        if "qwen" in lowered:
            return round((total_tokens / 1000.0) * 0.004, 6)
        return 0.0

    # ── Session Management ───────────────────────────────────

    def get_or_create_session(
        self,
        session_id: str = "",
        agent_id: str = "",
        system_prompt: str = "",
    ) -> ChatSession:
        """Get existing session or create a new one."""
        if session_id and session_id in self._sessions:
            session = self._sessions[session_id]
            if system_prompt and session.system_prompt != system_prompt:
                session.system_prompt = system_prompt
            if agent_id and not session.agent_id:
                session.agent_id = agent_id
            return session
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
        team_id: str = "",
        session_id: str = "",
        system_prompt: str = "",
        tools: Optional[List[Dict[str, Any]]] = None,
        model_override: str = "",
        config_override: Optional[ProviderConfig] = None,
    ) -> TurnResult:
        """Execute a single chat turn. This is the main entry point."""
        self._total_calls += 1
        # 全局 override 优先级最高（压过显式 config_override）；未设则按 config_override→per-agent→default
        config = self._global_override or config_override or self.get_provider_config(agent_id)
        client = LLMClient(config)

        session = self.get_or_create_session(session_id, agent_id, system_prompt)
        session.add_user_message(prompt)
        session.compact_if_needed()

        messages = session.build_openai_messages()
        model = model_override or config.model
        budget_guard = get_budget_guard()
        estimated_tokens = self._estimate_tokens_from_messages(
            messages,
            max_tokens=config.max_tokens,
        )
        budget_check = budget_guard.check(
            session_id=session.session_id,
            agent_id=agent_id,
            team_id=team_id,
            estimated_tokens=estimated_tokens,
        )
        if not budget_check.allowed:
            error_msg = budget_check.events[0].message if budget_check.events else "Token budget exceeded"
            fallback = (
                f"本次请求因 token 预算限制被拦截。\n\n"
                f"{error_msg}\n\n"
                f"可以缩小问题范围、减少上下文，或提高预算上限后重试。"
            )
            session.add_assistant_message(fallback)
            session.history.add("budget_exceeded", error_msg)
            return TurnResult(
                prompt=prompt,
                response=fallback,
                stop_reason="budget_exceeded",
                model=model,
                provider=config.provider.value,
                error=error_msg,
            )

        t0 = time.monotonic()
        raw = await client.chat_completion(
            messages, model=model, tools=tools,
        )
        latency = (time.monotonic() - t0) * 1000

        # Handle errors
        if raw.get("error"):
            error_msg = raw.get("message", "LLM call failed")
            # Provide a fallback response so chat doesn't break
            fallback = self._build_fallback_response(prompt, agent_id, system_prompt, error_msg)
            session.add_assistant_message(fallback)
            return TurnResult(
                prompt=prompt,
                response=fallback,
                stop_reason="error_fallback",
                model=model,
                provider=config.provider.value,
                latency_ms=latency,
                error=error_msg,
            )

        # Extract response
        choices = raw.get("choices", [])
        if not choices:
            fallback = self._build_fallback_response(prompt, agent_id, system_prompt, "No choices returned")
            session.add_assistant_message(fallback)
            return TurnResult(
                prompt=prompt, response=fallback,
                stop_reason="no_choices", model=model,
                provider=config.provider.value, latency_ms=latency,
            )

        choice = choices[0]
        message = choice.get("message", {})
        content = message.get("content") or ""
        # Qwen3 thinking mode: content is null, actual response in reasoning
        if not content and message.get("reasoning"):
            content = message["reasoning"]
        stop_reason = choice.get("finish_reason", "stop")

        # Token usage
        raw_usage = raw.get("usage", {})
        usage = UsageSummary(
            input_tokens=raw_usage.get("prompt_tokens", 0),
            output_tokens=raw_usage.get("completion_tokens", 0),
            total_tokens=raw_usage.get("total_tokens", 0),
        )
        _ctx = get_token_ctx()
        budget_guard.record_usage(
            UsageRecord(
                session_id=session.session_id,
                agent_id=agent_id or _ctx.get("agent_id", ""),
                team_id=team_id or _ctx.get("team_id", ""),
                model=model,
                input_tokens=usage.input_tokens,
                output_tokens=usage.output_tokens,
                total_tokens=usage.total_tokens,
                cost_usd=self._estimate_cost_usd(model, usage.total_tokens),
                phase=_ctx.get("phase", "task"),
                skill_id=_ctx.get("skill_id", ""),
                scenario_id=_ctx.get("scenario_id", ""),
                run_id=_ctx.get("run_id", ""),
            )
        )
        session.total_usage = session.total_usage.add(
            usage.input_tokens, usage.output_tokens
        )
        self._total_tokens += usage.total_tokens

        # Handle tool calls if present
        tool_invocations = self._extract_tool_calls(message)
        if tool_invocations:
            from .agent_toolbox import dispatch_tool_call

            for invocation in tool_invocations:
                args_json = json.dumps(invocation.arguments, ensure_ascii=False)
                tool_result = dispatch_tool_call(invocation.tool_name, args_json)
                invocation.result = json.dumps(tool_result, ensure_ascii=False)
                invocation.permitted = bool(tool_result.get("ok", False))
                if not invocation.permitted:
                    invocation.denial_reason = tool_result.get("error", "")

            tool_context = json.dumps(
                [inv.to_dict() for inv in tool_invocations],
                ensure_ascii=False,
            )
            followup_messages = messages + [
                {"role": "assistant", "content": content or "工具调用已准备执行。"},
                {
                    "role": "user",
                    "content": (
                        "工具执行结果(JSON):\n"
                        f"{tool_context[:8000]}\n\n"
                        "请基于这些结果直接回答原始问题。"
                    ),
                },
            ]
            followup_budget = budget_guard.check(
                session_id=session.session_id,
                agent_id=agent_id,
                team_id=team_id,
                estimated_tokens=self._estimate_tokens_from_messages(
                    followup_messages,
                    max_tokens=config.max_tokens,
                ),
            )
            if not followup_budget.allowed:
                tool_invocations[0].denial_reason = followup_budget.events[0].message
                content = (
                    f"{content}\n\n"
                    f"后续总结因 token 预算限制被跳过：{followup_budget.events[0].message}"
                ).strip()
                stop_reason = "budget_exceeded_after_tool"
                followup_messages = []
            second_raw = None
            if followup_messages:
                second_raw = await client.chat_completion(
                    followup_messages, model=model, tools=None,
                )
            if second_raw and not second_raw.get("error"):
                second_choices = second_raw.get("choices", [])
                if second_choices:
                    second_message = second_choices[0].get("message", {})
                    final_content = second_message.get("content") or second_message.get("reasoning") or ""
                    if final_content:
                        content = final_content
                        stop_reason = "tool_result"
                    second_usage = second_raw.get("usage", {})
                    second_total = second_usage.get("total_tokens", 0)
                    _ctx2 = get_token_ctx()
                    budget_guard.record_usage(
                        UsageRecord(
                            session_id=session.session_id,
                            agent_id=agent_id or _ctx2.get("agent_id", ""),
                            team_id=team_id or _ctx2.get("team_id", ""),
                            model=model,
                            input_tokens=second_usage.get("prompt_tokens", 0),
                            output_tokens=second_usage.get("completion_tokens", 0),
                            total_tokens=second_total,
                            cost_usd=self._estimate_cost_usd(model, second_total),
                            phase=_ctx2.get("phase", "task"),
                            skill_id=_ctx2.get("skill_id", ""),
                            scenario_id=_ctx2.get("scenario_id", ""),
                            run_id=_ctx2.get("run_id", ""),
                        )
                    )
                    usage = usage.add(
                        second_usage.get("prompt_tokens", 0),
                        second_usage.get("completion_tokens", 0),
                    )
                    session.total_usage = session.total_usage.add(
                        second_usage.get("prompt_tokens", 0),
                        second_usage.get("completion_tokens", 0),
                    )
                    self._total_tokens += second_usage.get("total_tokens", 0)

        session.add_assistant_message(content)

        return TurnResult(
            prompt=prompt,
            response=content,
            usage=usage,
            tool_invocations=tool_invocations,
            stop_reason=stop_reason,
            model=model,
            provider=config.provider.value,
            latency_ms=latency,
        )

    # ── Chat (Streaming) ─────────────────────────────────────

    async def stream_chat(
        self,
        prompt: str,
        *,
        agent_id: str = "",
        team_id: str = "",
        session_id: str = "",
        system_prompt: str = "",
        model_override: str = "",
    ) -> AsyncIterator[Dict[str, Any]]:
        """Stream a chat response chunk by chunk."""
        config = self.get_provider_config(agent_id)
        client = LLMClient(config)
        budget_guard = get_budget_guard()
        session = self.get_or_create_session(session_id, agent_id, system_prompt)
        session.add_user_message(prompt)
        session.compact_if_needed()
        messages = session.build_openai_messages()
        model = model_override or config.model
        budget_check = budget_guard.check(
            session_id=session.session_id,
            agent_id=agent_id,
            team_id=team_id,
            estimated_tokens=self._estimate_tokens_from_messages(
                messages,
                max_tokens=config.max_tokens,
            ),
        )
        if not budget_check.allowed:
            message = budget_check.events[0].message if budget_check.events else "Token budget exceeded"
            fallback = (
                f"本次请求因 token 预算限制被拦截。\n\n"
                f"{message}\n\n"
                f"可以缩小问题范围、减少上下文，或提高预算上限后重试。"
            )
            session.add_assistant_message(fallback)
            yield {"type": "message_start", "session_id": session.session_id, "model": model}
            yield {"type": "message_delta", "text": fallback}
            yield {"type": "message_stop", "stop_reason": "budget_exceeded"}
            return

        yield {"type": "message_start", "session_id": session.session_id, "model": model}

        full_content = ""
        raw_usage: Dict[str, Any] = {}
        async for chunk in client.stream_chat_completion(messages, model=model):
            if chunk.get("error"):
                yield {"type": "error", "message": chunk.get("message", "")}
                fallback = self._build_fallback_response(prompt, agent_id, system_prompt, chunk.get("message", ""))
                session.add_assistant_message(fallback)
                yield {"type": "message_delta", "text": fallback}
                yield {"type": "message_stop", "stop_reason": "error_fallback"}
                return

            if chunk.get("usage"):
                raw_usage = chunk.get("usage") or raw_usage

            choices = chunk.get("choices", [])
            if choices:
                delta = choices[0].get("delta", {})
                text = delta.get("content") or delta.get("reasoning") or ""
                if text:
                    full_content += text
                    yield {"type": "message_delta", "text": text}

        session.add_assistant_message(full_content)
        prompt_tokens = raw_usage.get(
            "prompt_tokens",
            self._estimate_tokens_from_text("\n".join(str(msg.get("content", "")) for msg in messages)),
        )
        completion_tokens = raw_usage.get(
            "completion_tokens",
            self._estimate_tokens_from_text(full_content),
        )
        total_tokens = raw_usage.get(
            "total_tokens",
            prompt_tokens + completion_tokens,
        )
        usage = UsageSummary(
            input_tokens=prompt_tokens,
            output_tokens=completion_tokens,
            total_tokens=total_tokens,
        )
        if usage.total_tokens:
            _ctx3 = get_token_ctx()
            budget_guard.record_usage(
                UsageRecord(
                    session_id=session.session_id,
                    agent_id=agent_id or _ctx3.get("agent_id", ""),
                    team_id=team_id or _ctx3.get("team_id", ""),
                    model=model,
                    input_tokens=usage.input_tokens,
                    output_tokens=usage.output_tokens,
                    total_tokens=usage.total_tokens,
                    cost_usd=self._estimate_cost_usd(model, usage.total_tokens),
                    phase=_ctx3.get("phase", "task"),
                    skill_id=_ctx3.get("skill_id", ""),
                    scenario_id=_ctx3.get("scenario_id", ""),
                    run_id=_ctx3.get("run_id", ""),
                )
            )
            session.total_usage = session.total_usage.add(
                usage.input_tokens,
                usage.output_tokens,
            )
            self._total_tokens += usage.total_tokens
        self._total_calls += 1
        yield {
            "type": "message_stop",
            "stop_reason": "completed",
            "full_content_length": len(full_content),
            "usage": usage.to_dict(),
        }

    # ── Fallback Response Builder ────────────────────────────

    def _build_fallback_response(
        self, prompt: str, agent_id: str, system_prompt: str, error: str
    ) -> str:
        """Generate a meaningful fallback when LLM is unavailable."""
        role_hint = ""
        if system_prompt:
            lines = system_prompt.split("\n")
            for line in lines[:10]:
                if any(kw in line for kw in ["角色", "Role", "职责", "核心", "你是"]):
                    role_hint = line.strip()
                    break

        prompt_lower = prompt.lower()
        system_lower = (system_prompt or "").lower()

        if (
            (" ri" in f" {prompt_lower}" or "reserved instance" in prompt_lower or "预留实例" in prompt_lower)
            and any(kw in system_lower for kw in ["reserved instance", "savings plan", "成本", "账单", "finops", "aws"])
        ):
            return (
                "在当前成本优化智能体语境下，RI 指 AWS Reserved Instance（预留实例），不是编程领域术语。\n\n"
                "建议按这条路径处理：\n"
                "1. 先拉取过去 30/60/90 天实例族、区域、规格、运行小时和利用率，确认稳定基线。\n"
                "2. 区分可承诺的稳定负载和波动负载；稳定部分评估 RI，弹性部分优先 Savings Plan 或按需/Spot。\n"
                "3. 计算覆盖率、利用率、到期时间、预付方式和现金流影响，避免为了折扣买过量。\n"
                "4. 对 OpenSearch/ElasticSearch 扩容，分别估算实例、存储、跨 AZ 流量、快照和监控成本。\n"
                "5. 设置 Cost Gate：覆盖率低、利用率低、预算超阈值或区域合规缺失时阻断采购。\n"
                "6. 输出购买建议、风险、回滚/调整策略，并把治理目标写回任务或系统演进项。\n\n"
                f"⚠️ 当前 LLM 未连接 ({error[:80]})，以上为成本治理降级答复。"
            )

        if any(kw in prompt_lower for kw in ["状态", "status", "进度", "report"]):
            return (
                f"📊 系统状态报告\n\n"
                f"AgentsGroup2026 后端: ✅ 运行中\n"
                f"LLM 状态: ⚠️ 离线 ({error[:60]})\n\n"
                f"💡 配置方式:\n"
                f"1. 设置环境变量 `DEEPSEEK_API_KEY=sk-xxx`\n"
                f"2. 或在智能体管理面板 → 模型池 → 添加模型 → 填入 API Key"
            )

        # General fallback
        return (
            f"我是 AgentsGroup2026 智能体{f' ({agent_id})' if agent_id else ''}。收到您的消息:\n"
            f"「{prompt[:100]}」\n\n"
            f"{f'我的定位: {role_hint}' if role_hint else ''}\n\n"
            f"⚠️ 当前 LLM 未连接 ({error[:80]})\n\n"
            f"当前系统功能正常，但需要 LLM 连接才能进行智能对话。\n\n"
            f"💡 快速配置 LLM:\n"
            f"```bash\n"
            f"export DEEPSEEK_API_KEY=sk-your-key-here\n"
            f"# 或 export OPENAI_API_KEY=sk-xxx\n"
            f"```\n"
            f"也可以在智能体管理面板 → 模型池中配置。"
        )

    def _extract_tool_calls(
        self, message: Dict[str, Any]
    ) -> List[ToolInvocation]:
        """Extract tool calls from the LLM response message."""
        tool_calls = message.get("tool_calls", [])
        result = []
        for tc in tool_calls:
            func = tc.get("function", {})
            args = func.get("arguments", "{}")
            try:
                parsed_args = json.loads(args) if isinstance(args, str) else args
            except json.JSONDecodeError:
                parsed_args = {"raw": args}
            result.append(ToolInvocation(
                tool_name=func.get("name", ""),
                arguments=parsed_args,
            ))
        return result

    # ── Status / Config Inspection ───────────────────────────

    def get_status(self) -> Dict[str, Any]:
        """Return harness status for monitoring."""
        cfg = self._default_config
        return {
            "provider": cfg.provider.value,
            "model": cfg.model,
            "base_url": cfg.resolve_base_url(),
            "has_api_key": bool(cfg.api_key),
            "total_calls": self._total_calls,
            "total_tokens": self._total_tokens,
            "errors": self._errors,
            "active_sessions": len(self._sessions),
            "agent_overrides": list(self._agent_configs.keys()),
        }

    def get_provider_info(self) -> Dict[str, Any]:
        """Get detailed provider configuration (safe — no key)."""
        cfg = self._default_config
        return {
            "provider": cfg.provider.value,
            "model": cfg.model,
            "base_url": cfg.resolve_base_url(),
            "max_tokens": cfg.max_tokens,
            "temperature": cfg.temperature,
            "has_api_key": bool(cfg.api_key),
            "api_key_preview": (
                cfg.api_key[:4] + "****" + cfg.api_key[-4:]
                if len(cfg.api_key) >= 8 else ("****" if cfg.api_key else "")
            ),
        }

    # ══════════════════════════════════════════════════════════
    # UltraPlan Agentic Loop — plan → act → observe → reflect
    # ══════════════════════════════════════════════════════════

    async def agent_loop(
        self,
        prompt: str,
        *,
        agent_id: str = "",
        team_id: str = "",
        session_id: str = "",
        system_prompt: str = "",
        tools: Optional[List[Dict[str, Any]]] = None,
        max_iterations: int = 10,
        plan_middleware: Optional[PlanMiddleware] = None,
        permission_context: Optional[ToolPermissionContext] = None,
        on_event: Optional[Callable[[str, Dict[str, Any]], None]] = None,
    ) -> "AgentLoopResult":
        """Execute a full agentic loop: plan → act → observe → reflect."""
        from .runtime import run_plan_loop

        return await run_plan_loop(
            self,
            prompt=prompt,
            plan_builder=build_plan_from_prompt,
            agent_id=agent_id,
            team_id=team_id,
            session_id=session_id,
            system_prompt=system_prompt,
            tools=tools,
            max_iterations=max_iterations,
            plan_middleware=plan_middleware,
            permission_context=permission_context,
            on_event=on_event,
        )

    async def agent_loop_stream(
        self,
        prompt: str,
        *,
        agent_id: str = "",
        team_id: str = "",
        session_id: str = "",
        system_prompt: str = "",
        tools: Optional[List[Dict[str, Any]]] = None,
        max_iterations: int = 10,
        plan_middleware: Optional[PlanMiddleware] = None,
        permission_context: Optional[ToolPermissionContext] = None,
        on_event: Optional[Callable[[str, Dict[str, Any]], None]] = None,
    ) -> AsyncIterator[Dict[str, Any]]:
        """Stream the agentic loop progress as SSE-compatible events."""
        from .runtime import stream_plan_loop

        async for chunk in stream_plan_loop(
            self,
            prompt=prompt,
            plan_builder=build_plan_from_prompt,
            agent_id=agent_id,
            team_id=team_id,
            session_id=session_id,
            system_prompt=system_prompt,
            tools=tools,
            max_iterations=max_iterations,
            plan_middleware=plan_middleware,
            permission_context=permission_context,
            on_event=on_event,
        ):
            yield chunk


# ═══════════════════════════════════════════════════════════════
# Singleton + init
# ═══════════════════════════════════════════════════════════════

_harness: Optional[ChatHarness] = None


@dataclass
class AgentLoopResult:
    """Result of a full agentic loop execution."""
    plan: ExecutionPlan = field(default_factory=ExecutionPlan)
    observations: List[Dict[str, Any]] = field(default_factory=list)
    final_response: str = ""
    turn_result: Optional[TurnResult] = None
    iterations: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "plan": self.plan.to_dict(),
            "observations": self.observations,
            "final_response": self.final_response[:2000],
            "iterations": self.iterations,
            "turn_result": self.turn_result.to_dict() if self.turn_result else None,
        }


def get_chat_harness() -> ChatHarness:
    """Get or create the global ChatHarness singleton."""
    global _harness
    if _harness is None:
        _harness = ChatHarness.from_settings_file()
    return _harness


def init_chat_harness(config: Optional[ProviderConfig] = None) -> ChatHarness:
    """Initialize the global ChatHarness with explicit config."""
    global _harness
    _harness = ChatHarness(default_config=config)
    return _harness


__all__ = [
    "AgentLoopResult",
    "ChatHarness",
    "ChatMessage",
    "ChatSession",
    "ExecutionPlan",
    "LLMClient",
    "LLMProvider",
    "PlanStep",
    "PlanStepStatus",
    "ProviderConfig",
    "ToolInvocation",
    "TurnResult",
    "UsageSummary",
    "build_plan_from_prompt",
    "get_chat_harness",
    "init_chat_harness",
    # Re-exports from execution_registry / session_store
    "HistoryLog",
    "ToolPermissionContext",
    "PermissionDenial",
    "RoutedMatch",
    "ToolPool",
    "PortRuntime",
    "TranscriptStore",
]
