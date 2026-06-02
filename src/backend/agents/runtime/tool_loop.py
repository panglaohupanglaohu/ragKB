"""Shared multi-turn tool loop runtime used by coding agents."""

from __future__ import annotations

import asyncio
import json
import logging
import time
import threading
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

from ..agent_toolbox import dispatch_tool_call, get_tools_for_role
from ..budget import UsageRecord, get_budget_guard
from ..chat_harness import ChatHarness, LLMClient, ProviderConfig, UsageSummary
from ..execution_registry import ToolPermissionContext
from .events import make_runtime_event_emitter

logger = logging.getLogger(__name__)

_ITERATION_NUDGE_RATIO = 0.80
_CONTEXT_BUDGET_CHARS = 100_000
_TOOL_RESULT_TRUNC = 500


@dataclass
class ToolLoopResult:
    ok: bool = False
    summary: str = ""
    files_changed: List[str] = field(default_factory=list)
    iterations: int = 0
    log: List[Dict[str, Any]] = field(default_factory=list)
    runtime_id: str = ""
    final_message: str = ""
    error: str = ""
    usage: UsageSummary = field(default_factory=UsageSummary)

    def to_dict(self) -> Dict[str, Any]:
        payload = {
            "ok": self.ok,
            "summary": self.summary,
            "files_changed": list(self.files_changed),
            "iterations": self.iterations,
            "log": list(self.log),
        }
        if self.runtime_id:
            payload["runtime_id"] = self.runtime_id
        if self.final_message:
            payload["final_message"] = self.final_message
        if self.error:
            payload["error"] = self.error
        usage = self.usage.to_dict()
        if usage["total_tokens"]:
            payload["usage"] = usage
        return payload


def _filtered_tools(
    role: str,
    permission_context: Optional[ToolPermissionContext],
) -> List[Dict[str, Any]]:
    tools = get_tools_for_role(role)
    if not permission_context:
        return tools
    filtered: List[Dict[str, Any]] = []
    for tool in tools:
        name = ((tool.get("function") or {}).get("name") or "").strip()
        if name and permission_context.blocks(name):
            continue
        filtered.append(tool)
    return filtered


def _messages_char_count(messages: List[Dict[str, Any]]) -> int:
    total = 0
    for message in messages:
        total += len(message.get("content") or "")
    return total


def _compact_old_tool_results(
    messages: List[Dict[str, Any]],
    emit_event: Optional[Callable[[str, Dict[str, Any]], Dict[str, Any]]] = None,
) -> None:
    total = _messages_char_count(messages)
    if total <= _CONTEXT_BUDGET_CHARS:
        return
    preserve_tail = 6
    cutoff = max(0, len(messages) - preserve_tail)
    freed = 0
    for idx in range(cutoff):
        message = messages[idx]
        if message.get("role") != "tool":
            continue
        content = message.get("content", "")
        if len(content) <= _TOOL_RESULT_TRUNC:
            continue
        freed += len(content) - _TOOL_RESULT_TRUNC
        message["content"] = content[:_TOOL_RESULT_TRUNC] + "\n…(context compacted)"
    if freed > 0:
        logger.info(
            "[ToolLoopRuntime] compacted %d chars from tool results (was %d)",
            freed,
            total,
        )
        if emit_event:
            emit_event("context_compact", {"freed_chars": freed, "was": total})


def _maybe_inject_nudge(
    messages: List[Dict[str, Any]],
    iteration: int,
    max_iterations: int,
    emit_event: Optional[Callable[[str, Dict[str, Any]], Dict[str, Any]]] = None,
) -> None:
    threshold = int(max_iterations * _ITERATION_NUDGE_RATIO)
    if iteration != threshold:
        return
    nudge = (
        f"⚠️ 你已消耗 {iteration}/{max_iterations} 轮迭代，剩余 "
        f"{max_iterations - iteration} 轮。请立刻完成剩余工作并调用 finish() "
        "工具提交成果；优先完成最关键的修改，不要继续大范围探索。"
    )
    messages.append({"role": "system", "content": nudge})
    if emit_event:
        emit_event("nudge", {"iteration": iteration, "max": max_iterations})


def _summarize_result(name: str, result: Dict[str, Any]) -> str:
    if not result.get("ok"):
        return f"FAIL: {str(result.get('error', ''))[:120]}"
    if name in {"read_file", "grep", "list_files"}:
        return str(result.get("path") or result.get("total_lines") or "ok")
    if name in {"write_file", "patch_file"}:
        return str(result.get("path") or "updated")
    if name in {"run_python", "run_pytest"}:
        return f"exit={result.get('exit_code', 0)}"
    return "ok"


def _record_usage(
    raw_usage: Dict[str, Any],
    *,
    model: str,
    session_id: str,
    agent_id: str,
    team_id: str,
) -> UsageSummary:
    usage = UsageSummary(
        input_tokens=raw_usage.get("prompt_tokens", 0),
        output_tokens=raw_usage.get("completion_tokens", 0),
        total_tokens=raw_usage.get("total_tokens", 0),
    )
    if usage.total_tokens:
        get_budget_guard().record_usage(
            UsageRecord(
                session_id=session_id,
                agent_id=agent_id,
                team_id=team_id,
                model=model,
                input_tokens=usage.input_tokens,
                output_tokens=usage.output_tokens,
                total_tokens=usage.total_tokens,
                cost_usd=ChatHarness._estimate_cost_usd(model, usage.total_tokens),
            )
        )
    return usage


async def run_tool_loop(
    *,
    prompt: str,
    config: ProviderConfig,
    role: str,
    system_prompt: str,
    agent_id: str = "",
    team_id: str = "",
    session_id: str = "",
    max_iterations: int = 25,
    max_tokens: int = 65536,
    temperature: float = 0.2,
    on_event: Optional[Callable[[str, Dict[str, Any]], None]] = None,
    permission_context: Optional[ToolPermissionContext] = None,
) -> ToolLoopResult:
    runtime_id, emit_event = make_runtime_event_emitter(
        loop_kind="tool_loop",
        session_id=session_id,
        on_event=on_event,
    )
    tools = _filtered_tools(role, permission_context)
    tool_names = [t["function"]["name"] for t in tools]
    tool_name_set = set(tool_names)
    messages: List[Dict[str, Any]] = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": prompt},
    ]
    client = LLMClient(config)
    budget_guard = get_budget_guard()
    usage_total = UsageSummary()
    files_changed: List[str] = []
    tool_log: List[Dict[str, Any]] = []
    summary = ""

    emit_event("loop_start", {"role": role, "tools": tool_names})

    for iteration in range(max_iterations):
        _maybe_inject_nudge(messages, iteration, max_iterations, emit_event)
        _compact_old_tool_results(messages, emit_event)

        estimated_tokens = ChatHarness._estimate_tokens_from_messages(
            messages,
            max_tokens=max_tokens,
        )
        budget_check = budget_guard.check(
            session_id=session_id,
            agent_id=agent_id,
            team_id=team_id,
            estimated_tokens=estimated_tokens,
        )
        if not budget_check.allowed:
            error_msg = budget_check.events[0].message if budget_check.events else "Token budget exceeded"
            emit_event("error", {"iteration": iteration, "error": error_msg})
            emit_event("loop_end", {"reason": "budget_exceeded", "iteration": iteration})
            return ToolLoopResult(
                ok=bool(files_changed or summary),
                summary=summary,
                files_changed=files_changed,
                iterations=iteration,
                log=tool_log,
                error=error_msg,
                usage=usage_total,
                runtime_id=runtime_id,
            )

        started_at = time.monotonic()
        raw = await client.chat_completion(
            messages,
            model=config.model,
            max_tokens=max_tokens,
            temperature=temperature,
            tools=tools,
        )
        if raw.get("error"):
            error_msg = raw.get("message", "LLM call failed")
            emit_event("error", {"iteration": iteration, "error": error_msg})
            emit_event(
                "loop_end",
                {
                    "reason": "network_error_partial" if files_changed or summary else "network_error",
                    "iteration": iteration,
                },
            )
            return ToolLoopResult(
                ok=bool(files_changed or summary),
                summary=summary or f"(network error after {iteration} turns)",
                files_changed=files_changed,
                iterations=iteration,
                log=tool_log,
                error=error_msg,
                usage=usage_total,
                runtime_id=runtime_id,
            )

        turn_usage = _record_usage(
            raw.get("usage", {}),
            model=config.model,
            session_id=session_id,
            agent_id=agent_id,
            team_id=team_id,
        )
        usage_total = usage_total.add(
            turn_usage.input_tokens,
            turn_usage.output_tokens,
        )

        choice = (raw.get("choices") or [{}])[0]
        message = choice.get("message", {}) or {}
        content = message.get("content") or message.get("reasoning") or ""
        tool_calls = message.get("tool_calls") or []
        finish_reason = choice.get("finish_reason", "")
        emit_event(
            "model_turn",
            {
                "iteration": iteration,
                "elapsed": round(time.monotonic() - started_at, 2),
                "content_chars": len(content),
                "tool_call_count": len(tool_calls),
                "finish_reason": finish_reason,
            },
        )

        assistant_message: Dict[str, Any] = {"role": "assistant", "content": content}
        if tool_calls:
            assistant_message["tool_calls"] = tool_calls
        messages.append(assistant_message)

        if not tool_calls:
            if not summary and content:
                summary = content[:1000]
            emit_event("loop_end", {"reason": "no_tool_call", "iteration": iteration})
            return ToolLoopResult(
                ok=True,
                summary=summary,
                files_changed=files_changed,
                iterations=iteration + 1,
                log=tool_log,
                final_message=content,
                usage=usage_total,
                runtime_id=runtime_id,
            )

        finished = False
        for tool_call in tool_calls:
            tool_call_id = tool_call.get("id", "")
            function = tool_call.get("function", {}) or {}
            name = function.get("name", "")
            args_raw = function.get("arguments", "") or "{}"
            emit_event("tool_call", {"name": name, "args": args_raw[:500]})

            if name == "finish":
                try:
                    payload = json.loads(args_raw or "{}")
                except json.JSONDecodeError:
                    payload = {"summary": args_raw[:500]}
                summary = payload.get("summary", summary)
                for changed in payload.get("files_changed") or []:
                    if changed and changed not in files_changed:
                        files_changed.append(changed)
                tool_log.append({"name": name, "args": args_raw, "ok": True})
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call_id,
                        "name": name,
                        "content": json.dumps({"ok": True, "ack": "finished"}, ensure_ascii=False),
                    }
                )
                finished = True
                continue

            if name not in tool_name_set or (permission_context and permission_context.blocks(name)):
                tool_result = {
                    "ok": False,
                    "error": f"tool blocked by runtime permissions: {name}",
                }
            else:
                tool_result = dispatch_tool_call(name, args_raw)

            if name in {"write_file", "patch_file"} and tool_result.get("ok"):
                try:
                    payload = json.loads(args_raw or "{}")
                except json.JSONDecodeError:
                    payload = {}
                path = payload.get("path", "")
                if path and path not in files_changed:
                    files_changed.append(path)

            tool_log.append(
                {
                    "name": name,
                    "args": args_raw[:1000],
                    "ok": bool(tool_result.get("ok")),
                    "summary": _summarize_result(name, tool_result),
                }
            )
            emit_event(
                "tool_result",
                {
                    "name": name,
                    "ok": bool(tool_result.get("ok")),
                    "summary": tool_log[-1]["summary"],
                },
            )
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call_id,
                    "name": name,
                    "content": json.dumps(tool_result, ensure_ascii=False)[:32000],
                }
            )

        if finished:
            emit_event("loop_end", {"reason": "finish_called", "iteration": iteration})
            return ToolLoopResult(
                ok=True,
                summary=summary,
                files_changed=files_changed,
                iterations=iteration + 1,
                log=tool_log,
                usage=usage_total,
                runtime_id=runtime_id,
            )

    emit_event(
        "loop_end",
        {
            "reason": "iteration_cap_partial" if files_changed or summary else "iteration_cap",
            "iteration": max_iterations,
        },
    )
    return ToolLoopResult(
        ok=bool(files_changed or summary),
        summary=summary or (
            f"(completed {len(files_changed)} file changes before cap)"
            if files_changed
            else ""
        ),
        files_changed=files_changed,
        iterations=max_iterations,
        log=tool_log,
        error="" if files_changed or summary else f"iteration cap hit ({max_iterations})",
        usage=usage_total,
        runtime_id=runtime_id,
    )


def run_tool_loop_sync(**kwargs: Any) -> Dict[str, Any]:
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(run_tool_loop(**kwargs)).to_dict()

    holder: Dict[str, Any] = {}

    def _runner() -> None:
        try:
            holder["result"] = asyncio.run(run_tool_loop(**kwargs)).to_dict()
        except Exception as exc:  # pragma: no cover - only used in nested loop edge cases
            holder["error"] = exc

    thread = threading.Thread(target=_runner, daemon=True)
    thread.start()
    thread.join()
    if "error" in holder:
        raise holder["error"]
    return holder["result"]


def run_tool_loop_sync_with_provider(
    *,
    prompt: str,
    api_key: str,
    api_base_url: str,
    model: str,
    role: str,
    system_prompt: str,
    max_iterations: int = 25,
    max_tokens: int = 65536,
    temperature: float = 0.2,
    agent_id: str = "",
    team_id: str = "",
    session_id: str = "",
    on_event: Optional[Callable[[str, Dict[str, Any]], None]] = None,
    permission_context: Optional[ToolPermissionContext] = None,
) -> Dict[str, Any]:
    """Synchronous compatibility entrypoint for runtime callers with raw provider fields."""
    return run_tool_loop_sync(
        prompt=prompt,
        config=ProviderConfig(
            api_key=api_key,
            api_base_url=api_base_url,
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            thinking={"type": "enabled"},
            reasoning_effort="high",
        ),
        role=role,
        system_prompt=system_prompt,
        agent_id=agent_id,
        team_id=team_id,
        session_id=session_id,
        max_iterations=max_iterations,
        max_tokens=max_tokens,
        temperature=temperature,
        on_event=on_event,
        permission_context=permission_context,
    )
