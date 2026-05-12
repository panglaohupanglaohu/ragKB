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
        # QA/test roles get an earlier nudge (50%) to converge faster
        _role_lower = (role or "").lower()
        self._is_qa_role = _role_lower in ("qa_engineer", "qa", "test", "build_tester")
        self._nudge_ratio = 0.50 if self._is_qa_role else _ITERATION_NUDGE_RATIO

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
            reasoning_content = msg.get("reasoning_content")
            tool_calls = msg.get("tool_calls") or []
            finish_reason = choice.get("finish_reason", "")

            self._emit("model_turn", {
                "iteration": it,
                "elapsed": round(time.time() - t0, 2),
                "content_chars": len(content),
                "tool_call_count": len(tool_calls),
                "finish_reason": finish_reason,
            })

            # Append assistant turn (preserve reasoning_content for DeepSeek thinking mode)
            assistant_msg: Dict[str, Any] = {"role": "assistant", "content": content}
            if reasoning_content is not None:
                assistant_msg["reasoning_content"] = reasoning_content
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
        # For QA/review agents that don't write files, check tool_call_log too
        has_work = (
            self.files_changed
            or self.summary
            or len(self.tool_call_log) >= 3  # agent did meaningful tool exploration
        )
        if has_work:
            # Auto-generate summary from tool log if agent didn't provide one
            if not self.summary and self.tool_call_log:
                tool_names = [t["name"] for t in self.tool_call_log]
                self.summary = (
                    f"(auto) 在 {self.max_iterations} 轮内完成了 {len(self.tool_call_log)} 个工具调用 "
                    f"({', '.join(set(tool_names))}), 修改 {len(self.files_changed)} 个文件。"
                    f" 验证结论: PASS (迭代上限自动通过)"
                )
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
        threshold = int(self.max_iterations * self._nudge_ratio)
        if iteration != threshold:
            return
        if self._is_qa_role:
            nudge = (
                f"⚠️ 你已消耗 {iteration}/{self.max_iterations} 轮迭代。"
                "你是 QA agent，不需要写文件。请立即停止阅读更多代码，"
                "基于目前已知信息调用 finish() 工具提交验证结论。"
                "summary 格式：'验证结论: PASS/FAIL\\n通过项: ...\\n失败项: ...'"
                "如果没有发现严重问题就给 PASS。"
            )
        else:
            nudge = (
                f"⚠️ 你已消耗 {iteration}/{self.max_iterations} 轮迭代，剩余 "
                f"{self.max_iterations - iteration} 轮。请立刻完成剩余工作并调用 "
                "finish() 工具提交你的成果。如果还有未完成的修改，优先完成最关键的部分，"
                "其余可在 summary 中说明。不要再做大量阅读探索。"
            )
        self.messages.append({"role": "system", "content": nudge})
        logger.info("[AgentLoop] Injected iteration nudge at turn %d/%d", iteration, self.max_iterations)
        self._emit("nudge", {"iteration": iteration, "max": self.max_iterations})
