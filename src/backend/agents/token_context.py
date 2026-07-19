"""Token 归因上下文 — 进程内 contextvar 注入。

用法:
    from .token_context import token_scope, new_run_id, get_token_ctx

    run_id = new_run_id("skill_verify")
    with token_scope(run_id=run_id, phase="skill_verify", skill_id=skill_id, team_id=team_id):
        # 内部所有 chat_harness.chat() 调用自动归因到该 run_id
        result = await harness.chat(...)

    # 读取当前上下文（chat_harness 记账时调用）
    ctx = get_token_ctx()  # -> {phase, run_id, skill_id, ...}
"""
from __future__ import annotations

import contextvars
import uuid
from contextlib import contextmanager
from typing import Any, Dict, Iterator

TokenContext = Dict[str, Any]

_ctx: contextvars.ContextVar[TokenContext] = contextvars.ContextVar("token_ctx", default={})


def new_run_id(prefix: str = "run") -> str:
    """生成带前缀的 run_id。"""
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


def get_token_ctx() -> TokenContext:
    """获取当前归因上下文副本。"""
    return dict(_ctx.get())


@contextmanager
def token_scope(**kw: Any) -> Iterator[TokenContext]:
    """合并入栈当前归因上下文。

    支持的键: phase, run_id, team_id, agent_id, skill_id, scenario_id, task_id。
    task_id 若提供且未显式传 scenario_id，则写入 scenario_id（任务维计量兼容）。
    值为 None 的键会被跳过，保留父级上下文中的值。
    """
    updates = dict(kw)
    task_id = updates.pop("task_id", None)
    if task_id and not updates.get("scenario_id"):
        updates["scenario_id"] = str(task_id)
    if task_id:
        updates["task_id"] = str(task_id)
    merged = _merge_token_context(_ctx.get(), updates)
    token = _ctx.set(merged)
    try:
        yield merged
    finally:
        _ctx.reset(token)


def _merge_token_context(parent: TokenContext, updates: TokenContext) -> TokenContext:
    return {**parent, **_without_none_values(updates)}


def _without_none_values(values: TokenContext) -> TokenContext:
    return {key: value for key, value in values.items() if value is not None}
