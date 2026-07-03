"""Token Gate API Routes — Token 预算门控端点。

替代 Terraform Cost Gate 的 Token 语义版。
"""
from __future__ import annotations

import logging
import threading
from collections import deque
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from .token_ledger import LEDGER
from .token_policy import ENGINE, TokenBudget

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/cost-gate", tags=["token-gate"])

# ── 进程内统计与历史 ───────────────────────────────────────
_stats_lock = threading.Lock()
_stats = {"pass": 0, "warn": 0, "block": 0, "total": 0}
_history: deque = deque(maxlen=200)


def _bump_stats(decision: str) -> None:
    with _stats_lock:
        _stats["total"] += 1
        if decision in _stats:
            _stats[decision] += 1


def _append_history(report: dict, run_id: str = "") -> None:
    with _stats_lock:
        _history.append({**report, "run_id": run_id})


# ── 请求模型 ───────────────────────────────────────────────

class TokenEvaluateRequest(BaseModel):
    run_id: Optional[str] = Field(default=None, description="Run ID to evaluate (reads from Ledger)")
    inline: Optional[Dict[str, Any]] = Field(default=None, description="Inline run data (alternative to run_id)")
    budget: Optional[Dict[str, Any]] = Field(default=None, description="Token budget config")


# ── 路由 ───────────────────────────────────────────────────

@router.post("/token/evaluate")
async def evaluate_token_run(req: TokenEvaluateRequest):
    """评估一次 run 的 Token 消耗是否合规。

    优先用 run_id 从 Ledger 读取；无 run_id 时用 inline 数据。
    """
    run = {}
    run_id = req.run_id or ""
    if run_id:
        run = LEDGER.run(run_id)
    elif req.inline:
        run = req.inline

    if not run and not req.inline:
        raise HTTPException(status_code=422, detail="Either 'run_id' or 'inline' is required")

    budget = TokenBudget(**(req.budget or {}))
    report = ENGINE.evaluate(run, budget)
    _bump_stats(report["decision"])
    _append_history(report, run_id)
    return report


@router.get("/token/stats")
async def token_gate_stats():
    """Token Gate 统计。"""
    with _stats_lock:
        return dict(_stats)


@router.get("/token/history")
async def token_gate_history(limit: int = 50):
    """Token Gate 评估历史。"""
    with _stats_lock:
        items = list(_history)[-limit:]
    items.reverse()
    return {"items": items, "count": len(items)}


@router.get("/token/health")
async def token_gate_health():
    """Token Gate 健康检查。"""
    return {"status": "healthy", "engine": "token_budget", "stats": dict(_stats)}
