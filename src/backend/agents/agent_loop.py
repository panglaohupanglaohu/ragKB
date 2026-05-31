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
from .chat_harness import ProviderConfig
from .runtime import run_tool_loop_sync

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
    """Thin shim over ``agents.runtime.tool_loop.run_tool_loop_sync``.
    .. deprecated:: Use the runtime module directly. This class will be removed.
    """

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
        config = ProviderConfig(
            api_key=self.api_key,
            api_base_url=self.api_base_url,
            model=self.model,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            thinking={"type": "enabled"},
            reasoning_effort="high",
        )
        return run_tool_loop_sync(
            prompt=user_prompt,
            config=config,
            role=self.role,
            system_prompt=self.messages[0]["content"],
            max_iterations=self.max_iterations,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            on_event=self.on_event,
        )

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
        cutoff = max(0, len(self.messages) - preserve_tail)
        freed = 0
        for i in range(cutoff):
            m = self.messages[i]
            if m.get("role") == "tool":
                old_content = m.get("content", "")
                if len(old_content) > _TOOL_RESULT_TRUNC:
                    freed += len(old_content) - _TOOL_RESULT_TRUNC
                    m["content"] = old_content[:_TOOL_RESULT_TRUNC] + "\n…(context compacted)"
        if freed > 0:
            logger.info(
                "[AgentLoop] Context budget: compacted %d chars from old tool results "
                "(total was %d, budget %d)", freed, total, _CONTEXT_BUDGET_CHARS,
            )
            self._emit("context_compact", {"freed_chars": freed, "was": total})

    def _maybe_inject_nudge(self, iteration: int):
        """Safeguard 1: when approaching iteration cap, inject a system nudge
        telling the agent to wrap up and call finish().
        """
        threshold = int(self.max_iterations * _ITERATION_NUDGE_RATIO)
        if iteration != threshold:
            return
        nudge = (
            f"⚠️ 你已消耗 {iteration}/{self.max_iterations} 轮迭代，剩余 "
            f"{self.max_iterations - iteration} 轮。请立刻完成剩余工作并调用 "
            "finish() 工具提交你的成果。如果还有未完成的修改，优先完成最关键的部分，"
            "其余可在 summary 中说明。不要再做大量阅读探索。"
        )
        self.messages.append({"role": "system", "content": nudge})
        logger.info("[AgentLoop] Injected iteration nudge at turn %d/%d", iteration, self.max_iterations)
        self._emit("nudge", {"iteration": iteration, "max": self.max_iterations})
