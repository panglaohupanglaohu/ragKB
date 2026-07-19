# -*- coding: utf-8 -*-
"""任务 Token 治理 API — 计量 / 缓存 / 路由 / 预算 / 验证.

挂载于 cost 前缀旁：由 cost_routes 或 main 引入。
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Query
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/cost/token-governance", tags=["token-governance"])


class CompressPreviewRequest(BaseModel):
    messages: List[Dict[str, Any]] = Field(default_factory=list)
    system_max_chars: int = 6000
    msg_max_chars: int = 4000


class BudgetUpdateRequest(BaseModel):
    per_session_max: Optional[int] = None
    per_agent_daily_max: Optional[int] = None
    per_team_daily_max: Optional[int] = None
    on_exceed: Optional[str] = None  # halt | warn
    alert_threshold: Optional[float] = None


class VerifyRequest(BaseModel):
    window: str = "24h"
    team_id: str = ""
    task_key: str = ""
    run_id: str = ""
    max_tokens: int = 0
    min_efficiency: float = 0.0
    messages: Optional[List[Dict[str, Any]]] = None


class LeversUpdateRequest(BaseModel):
    compress: Optional[bool] = None
    simplify_prompt: Optional[bool] = None
    cache_mode: Optional[str] = None  # observe|serve|off
    model_route: Optional[bool] = None
    skill_route_hint: Optional[bool] = None
    budget_enforce_submit: Optional[bool] = None
    budget_enforce_turn: Optional[bool] = None
    # R9 research-inspired
    rtk_tool_compress: Optional[bool] = None
    progressive_memory: Optional[bool] = None
    codegraph_context: Optional[bool] = None
    ponytail_level: Optional[str] = None  # off|lite|full|ultra
    caveman_level: Optional[str] = None
    cost_tier_route: Optional[bool] = None
    # R10: tunable knobs (also budget keys → dual-write budget settings)
    params: Optional[Dict[str, Any]] = None


class SimulateRequest(BaseModel):
    messages: List[Dict[str, Any]] = Field(default_factory=list)
    task_id: str = ""
    team_id: str = ""
    agent_id: str = ""
    query_for_skill: str = ""
    # fixture=前端硬编码样例；task=从 task_id 拉最近一轮（默认优先 task）
    source: str = "auto"  # auto | task | fixture


@router.get("/dashboard")
def governance_dashboard(
    window: str = Query(default="24h"),
    team_id: str = Query(default=""),
) -> Dict[str, Any]:
    """工作台一页聚合：任务账单 + 杠杆统计 + 预算 + 路由."""
    from .token_governance import get_token_governance

    return get_token_governance().dashboard(window=window, team_id=team_id or "")


@router.get("/levers")
def get_levers() -> Dict[str, Any]:
    """开关 + 可调参数当前值 + 运行时指标（UI 权威数据源；长文见 README）."""
    from .token_governance import get_token_governance
    from .token_governance.lever_catalog import catalog_with_runtime, get_lever_catalog
    from .token_governance.lever_params import PARAM_SPECS
    from .token_governance.settings import load_budget_knobs
    from .prompt_cache import get_prompt_cache

    svc = get_token_governance()
    settings = svc.settings()
    stats = svc.counters()
    counters = (stats.get("counters") or {})
    cache = get_prompt_cache().stats()
    budget = load_budget_knobs()
    model_state = {}
    try:
        from .runtime.model_router import get_model_router
        model_state = get_model_router().get_state_dict()
    except Exception:
        pass
    catalog = catalog_with_runtime(settings, counters, cache, model_state, budget)
    return {
        "ok": True,
        "levers": settings,  # 兼容旧字段（含 params）
        "params": settings.get("params") or {},
        "budget": budget,
        "param_specs": PARAM_SPECS,
        "catalog": catalog,
        "pipeline": [c["id"] for c in get_lever_catalog()],
        "docs": "/README.md#任务-token-治理",
        "architecture": {
            "entry": "TokenGovernanceService.prepare_request",
            "order": (
                "simplify → ponytail/caveman → rtk_tool → compress → progressive_mem → "
                "codegraph → cache → skill → cost_tier+model → budget"
            ),
            "wired_into": ["chat_harness.chat", "tool_loop (per turn)", "POST .../simulate"],
            "settings_file": "config/settings.json → token_governance + budget",
            "savings_log": "storage/token_governance/savings_events.jsonl",
            "ui": "one-line pipeline + knobs; long docs in README",
        },
        "stats": stats,
        "cache": cache,
        "model_router": model_state,
    }


@router.post("/levers")
def set_levers(req: LeversUpdateRequest) -> Dict[str, Any]:
    from .token_governance import get_token_governance
    from .token_governance.settings import load_budget_knobs

    updates = req.model_dump(exclude_none=True)
    svc = get_token_governance()
    levers = svc.update_settings(updates)
    return {
        "ok": True,
        "levers": levers,
        "params": levers.get("params") or {},
        "budget": load_budget_knobs(),
        "stats": svc.counters(),
    }


@router.get("/task-messages")
def get_task_messages(
    task_id: str = Query(...),
) -> Dict[str, Any]:
    """从真实 task 取最近一轮 messages（snapshot 优先，否则产物重构）."""
    from .token_governance.task_messages import load_task_messages

    data = load_task_messages(task_id)
    # 列表接口不回传全文，只回元信息 + 每条 content_len
    msgs = data.get("messages") or []
    data_out = dict(data)
    data_out["messages_preview"] = [
        {
            "role": m.get("role"),
            "content_len": len(str(m.get("content") or "")),
            "content_head": str(m.get("content") or "")[:120],
        }
        for m in msgs
    ]
    # 默认不带全文（体积大）；需要全文时用 include_body=1
    data_out.pop("messages", None)
    return data_out


@router.get("/recent-tasks")
def recent_tasks_for_sim(
    limit: int = Query(default=20, ge=1, le=50),
    team_id: str = Query(default=""),
) -> Dict[str, Any]:
    from .token_governance.task_messages import list_recent_tasks

    items = list_recent_tasks(limit=limit, team_id=team_id or "")
    return {"ok": True, "tasks": items, "count": len(items)}


@router.post("/simulate")
def simulate_prepare(req: SimulateRequest) -> Dict[str, Any]:
    """对 messages 跑 prepare（调试；不短路生产 LLM）.

    source:
      - task / auto+task_id: 从 task 拉最近一轮真实 messages
      - fixture / 显式 messages: 用请求体 messages（前端样例或自定义）
    """
    from .token_governance import get_token_governance
    from .token_governance.task_messages import load_task_messages

    src = (req.source or "auto").lower()
    messages = list(req.messages or [])
    task_id = (req.task_id or "").strip()
    team_id = req.team_id or ""
    agent_id = req.agent_id or ""
    msg_meta: Dict[str, Any] = {"source": "request_body"}

    use_task = src in ("task", "auto") and bool(task_id) and (
        src == "task" or not messages
    )
    if use_task:
        loaded = load_task_messages(task_id)
        if not loaded.get("ok") or not loaded.get("messages"):
            return {
                "ok": False,
                "error": loaded.get("error") or "no_messages_for_task",
                "task_id": task_id,
                "hint": "无 snapshot 且无法重构：先跑一轮任务，或改用 fixture 样例",
                "loaded": {k: loaded.get(k) for k in (
                    "source", "message_count", "chars", "hints",
                )},
            }
        messages = loaded["messages"]
        task_id = str(loaded.get("task_id") or task_id)
        team_id = team_id or str(loaded.get("team_id") or "")
        agent_id = agent_id or str(loaded.get("agent_id") or "")
        msg_meta = {
            "source": loaded.get("source") or "task",
            "snapshot_source": loaded.get("snapshot_source"),
            "message_count": loaded.get("message_count"),
            "chars": loaded.get("chars"),
            "saved_at": loaded.get("saved_at"),
            "title": loaded.get("title"),
            "hints": loaded.get("hints"),
        }
    elif not messages:
        return {
            "ok": False,
            "error": "messages_or_task_id_required",
            "hint": "传 task_id（source=task）或 messages（fixture）",
        }

    query = req.query_for_skill or ""
    if not query:
        for m in reversed(messages):
            if isinstance(m, dict) and m.get("role") == "user":
                query = str(m.get("content") or "")[:2000]
                break

    prep = get_token_governance().prepare_request(
        messages,
        task_id=task_id,
        team_id=team_id,
        agent_id=agent_id,
        query_for_skill=query,
    )
    # 不返回完整 messages 正文过长时截断
    msgs = prep.get("messages") or []
    prep_out = dict(prep)
    prep_out["messages"] = [
        {"role": m.get("role"), "content_len": len(str(m.get("content") or ""))}
        for m in msgs
    ]
    return {
        "ok": True,
        "prepare": prep_out,
        "input": msg_meta,
        "task_id": task_id,
        "team_id": team_id,
        "agent_id": agent_id,
    }


@router.get("/cache-stats")
def cache_stats() -> Dict[str, Any]:
    from .prompt_cache import get_prompt_cache
    from .token_governance import get_token_governance

    return {
        "ok": True,
        "cache": get_prompt_cache().stats(),
        "stats": get_token_governance().counters(),
    }


@router.get("/savings")
def list_savings(
    task_id: str = Query(default=""),
    team_id: str = Query(default=""),
    limit: int = Query(default=40, ge=1, le=200),
) -> Dict[str, Any]:
    """按 task/team 查询 prepare 节省事件（JSONL）."""
    from .token_governance.savings_store import aggregate_by_task, recent_events

    return {
        "ok": True,
        "events": recent_events(limit=limit, task_id=task_id or "", team_id=team_id or ""),
        "by_task": aggregate_by_task(limit_tasks=30, team_id=team_id or ""),
        "filter": {"task_id": task_id, "team_id": team_id, "limit": limit},
    }


@router.post("/compress-preview")
def compress_preview(req: CompressPreviewRequest) -> Dict[str, Any]:
    from .prompt_cache import compress_messages, fingerprint_messages, get_prompt_cache

    result = compress_messages(
        req.messages,
        system_max_chars=req.system_max_chars,
        msg_max_chars=req.msg_max_chars,
    )
    key = fingerprint_messages(result["messages"])
    cache = get_prompt_cache()
    lookup = cache.lookup_messages(req.messages, compress=True)
    return {
        "ok": True,
        "fingerprint": key,
        "compress": result,
        "cache_hit": lookup.get("hit"),
        "cache_key": lookup.get("key"),
    }


@router.post("/cache-warm")
def cache_warm(req: CompressPreviewRequest) -> Dict[str, Any]:
    """将压缩后的消息指纹写入缓存（模拟重复上下文命中）."""
    from .prompt_cache import get_prompt_cache

    cache = get_prompt_cache()
    key = cache.store_messages(req.messages, compress=True)
    return {"ok": True, "key": key, "cache": cache.stats()}


@router.get("/router-status")
def router_status() -> Dict[str, Any]:
    """ModelRouter 档位说明 + 若进程内有默认实例则返回状态."""
    try:
        from .runtime.model_router import ModelRouter, ModelTier
    except Exception as e:
        return {"ok": False, "error": str(e)}

    tiers = []
    for t in ModelTier:
        cfg = ModelRouter._default_tiers().get(t)
        tiers.append({
            "tier": t.value,
            "model": cfg.model if cfg else "",
            "provider": cfg.provider if cfg else "",
            "max_tokens": cfg.max_tokens if cfg else 0,
        })
    # 轻量默认路由器（无全局单例时展示策略默认值）
    demo = ModelRouter(total_budget=100_000)
    demo.state.used_budget = 0
    decision = demo.route(tokens_estimated=0)
    return {
        "ok": True,
        "tiers": tiers,
        "policy": {
            "budget_threshold_down": demo.state.budget_threshold_down,
            "failure_threshold_up": demo.state.failure_threshold_up,
            "sticky_count": demo.state.sticky_count,
        },
        "current": {
            "tier": decision.tier.value,
            "model": decision.model,
            "reason": decision.reason or "default",
        },
        "note": "按需模型路由：预算紧→economy；连续失败→升档；粘滞防抖",
    }


@router.get("/budget")
def get_budget() -> Dict[str, Any]:
    from .budget import get_budget_guard

    guard = get_budget_guard()
    alerts = guard.alerts()
    return {
        "ok": True,
        "budget": guard.budget.to_dict(),
        "recent_events": (alerts.get("events") or [])[:20],
    }


@router.post("/budget")
def set_budget(req: BudgetUpdateRequest) -> Dict[str, Any]:
    from .budget import get_budget_guard, save_budget_settings
    from .budget.models import TokenBudget

    guard = get_budget_guard()
    cur = guard.budget
    new_b = TokenBudget(
        per_session_max=int(req.per_session_max if req.per_session_max is not None else cur.per_session_max),
        per_agent_daily_max=int(
            req.per_agent_daily_max if req.per_agent_daily_max is not None else cur.per_agent_daily_max
        ),
        per_team_daily_max=int(
            req.per_team_daily_max if req.per_team_daily_max is not None else cur.per_team_daily_max
        ),
        on_exceed=str(req.on_exceed or cur.on_exceed or "halt"),
        alert_threshold=float(
            req.alert_threshold if req.alert_threshold is not None else cur.alert_threshold
        ),
    )
    if new_b.on_exceed not in ("halt", "warn"):
        new_b.on_exceed = "halt"
    save_budget_settings(new_b)
    guard.update_budget(new_b)
    return {"ok": True, "budget": new_b.to_dict()}


@router.post("/verify")
def verify_governance(req: VerifyRequest) -> Dict[str, Any]:
    """效果验证：ledger 摘要 + 可选 run gate + 缓存统计 + 压缩预览."""
    from .prompt_cache import compress_messages, get_prompt_cache
    from .token_ledger import LEDGER
    from .token_policy import ENGINE, TokenBudget as PolicyBudget

    summary = LEDGER.summary(req.window)
    by_task = LEDGER.by_task(window=req.window, team_id=req.team_id or "", limit=30)
    task_row = None
    unscoped = None
    attributed_total = 0
    for row in by_task:
        if row.get("task_key") == "(unscoped)":
            unscoped = row
        else:
            attributed_total += int(row.get("total") or 0)
        if req.task_key and row.get("task_key") == req.task_key:
            task_row = row

    gate = None
    run_data = {}
    if req.run_id:
        run_data = LEDGER.run(req.run_id)
        gate = ENGINE.evaluate(
            {
                "total": run_data.get("total", 0),
                "score": 0,
                "calls": run_data.get("calls", 0),
                "dup_intent_calls": 0,
            },
            PolicyBudget(max_tokens=req.max_tokens, min_efficiency=req.min_efficiency),
        )

    compress = None
    if req.messages:
        compress = compress_messages(req.messages)

    cache = get_prompt_cache().stats()
    attribution = {
        "attributed_total": attributed_total,
        "unscoped_total": int((unscoped or {}).get("total") or 0),
        "unscoped_calls": int((unscoped or {}).get("calls") or 0),
        "attributed_tasks": sum(1 for r in by_task if r.get("task_key") != "(unscoped)"),
    }
    grand = attributed_total + attribution["unscoped_total"]
    attribution["attributed_share"] = (
        round(attributed_total / grand, 4) if grand else 0.0
    )
    return {
        "ok": True,
        "window": req.window,
        "summary": summary,
        "by_task_top": [r for r in by_task if r.get("task_key") != "(unscoped)"][:10],
        "task_focus": task_row,
        "attribution": attribution,
        "gate": gate,
        "run": run_data if req.run_id else None,
        "compress": compress,
        "cache": cache,
        "verdict": _verdict(summary, gate, cache, compress, attribution),
    }


def _verdict(summary, gate, cache, compress, attribution=None) -> Dict[str, Any]:
    notes = []
    score = 100
    total = int((summary or {}).get("total") or 0)
    if total <= 0:
        notes.append("窗口内尚无 token 记账 — 先跑任务再验证")
        score -= 20
    attr = attribution or {}
    uns = int(attr.get("unscoped_total") or 0)
    share = float(attr.get("attributed_share") or 0)
    if uns > 0 and share < 0.5:
        notes.append(
            f"归因不足：unscoped={uns} tokens，已归因占比 {share:.0%} "
            "— 新任务执行须带 task_id（已接 tool_loop/直连 API）"
        )
        score -= 25
    elif uns > 0:
        notes.append(f"仍有 unscoped={uns}（历史遗留可忽略；新跑任务应带 task_key）")
        score -= 5
    else:
        notes.append("任务归因良好（无 unscoped）")
        score += 5
    if gate:
        if gate.get("decision") == "block":
            notes.append("Token Gate: block")
            score -= 40
        elif gate.get("decision") == "warn":
            notes.append("Token Gate: warn")
            score -= 15
        else:
            notes.append("Token Gate: pass")
    if cache and cache.get("hits", 0) > 0:
        notes.append(f"缓存命中 {cache.get('hits')} 次，估计省 {cache.get('tokens_saved_est', 0)} tokens")
        score += 5
    if compress and compress.get("saved_tokens_est", 0) > 0:
        notes.append(f"压缩可省约 {compress['saved_tokens_est']} tokens（估计）")
        score += 5
    score = max(0, min(100, score))
    return {"score": score, "notes": notes}
