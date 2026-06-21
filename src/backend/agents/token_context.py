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
from typing import Dict, Optional

_ctx: contextvars.ContextVar[Dict] = contextvars.ContextVar("token_ctx", default={})


def new_run_id(prefix: str = "run") -> str:
    """生成带前缀的 run_id。"""
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


def get_token_ctx() -> Dict:
    """获取当前归因上下文副本。"""
    return dict(_ctx.get())


@contextmanager
def token_scope(**kw):
    """合并入栈当前归因上下文。

    支持的键: phase, run_id, team_id, agent_id, skill_id, scenario_id。
    值为 None 的键会被跳过，保留父级上下文中的值。
    """
    merged = {**_ctx.get(), **{k: v for k, v in kw.items() if v is not None}}
    tok = _ctx.set(merged)
    try:
        yield merged
    finally:
        _ctx.reset(tok)
