# -*- coding: utf-8 -*-
"""审核路由 — SSE 推送审核队列变化 + 状态更新 API.

接口:
  GET  /api/v1/review/sse           — SSE 实时推送审核队列变化
  GET  /api/v1/review/queue         — 获取审核队列
  GET  /api/v1/review/{entry_id}    — 获取单条审核条目
  POST /api/v1/review/{entry_id}/status  — 更新审核状态 (approve/reject/...)
  POST /api/v1/review/evaluate      — 执行门禁评估并提交审核队列
  GET  /api/v1/review/entries       — 列表查询 (支持过滤)
"""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from .gate_evaluator import evaluate, evaluate_from_dict, quick_evaluate
from .review_models import (
    GateEvaluationContext,
    GateEvaluationResult,
    GateLevel,
    ReviewAction,
    ReviewEntry,
    ReviewStatus,
)
from .review_service import ReviewService, get_review_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/review", tags=["review"])

# ── SSE 事件管理 ──────────────────────────────────────────

# 活跃的 SSE 客户端连接
_active_sse_clients: Dict[str, asyncio.Queue] = {}
_sse_lock = asyncio.Lock()


async def _broadcast_event(event_type: str, data: dict) -> None:
    """广播事件到所有 SSE 客户端."""
    async with _sse_lock:
        stale = []
        for client_id, queue in _active_sse_clients.items():
            try:
                queue.put_nowait({"type": event_type, "data": data})
            except asyncio.QueueFull:
                stale.append(client_id)
        for cid in stale:
            del _active_sse_clients[cid]


# ── 请求/响应模型 ────────────────────────────────────────


class StatusUpdateRequest(BaseModel):
    """审核状态更新请求."""
    action: ReviewAction = Field(..., description="审核操作类型")
    reviewer: str = Field(default="system", description="审核人")
    comment: str = Field(default="", description="审核评论")
    idempotency_key: Optional[str] = Field(default=None, description="幂等键")


class EvaluateAndSubmitRequest(BaseModel):
    """门禁评估并提交请求."""
    entity_id: str = Field(..., description="被评估实体ID")
    entity_type: str = Field(default="evolution_item")
    entity_name: str = Field(default="")
    context: Dict[str, Any] = Field(default_factory=dict, description="评估上下文 (所有维度)")
    domain: str = Field(default="general")
    severity: str = Field(default="medium")
    idempotency_key: Optional[str] = Field(default=None)


class EvaluateResponse(BaseModel):
    """门禁评估响应."""
    entity_id: str
    score: float
    level: str
    passed: bool
    reasons: List[str]
    warnings: List[str]
    blocked_by: List[str]
    entry_id: Optional[str] = None


class QueueResponse(BaseModel):
    """审核队列响应."""
    entries: List[Dict[str, Any]]
    total_pending: int
    total_approved: int
    total_rejected: int
    last_updated: str


# ── SSE 端点 ─────────────────────────────────────────────


@router.get("/sse")
async def review_sse():
    """SSE 实时推送审核队列变化.

    事件类型:
      - queue_updated: 审核队列变化 (新增/状态更新)
      - entry_status_changed: 单条审核条目状态变化
      - heartbeat: 心跳 (每30s)
    """
    client_id = f"sse-{id(asyncio.current_task())}"

    async def event_stream():
        queue: asyncio.Queue = asyncio.Queue(maxsize=100)

        async with _sse_lock:
            _active_sse_clients[client_id] = queue

        try:
            # 初始推送: 当前队列全量
            svc = await get_review_service()
            review_queue = await svc.get_queue()
            queue_data = {
                "entries": [e.to_dict() for e in review_queue.entries],
                "total_pending": review_queue.total_pending,
                "total_approved": review_queue.total_approved,
                "total_rejected": review_queue.total_rejected,
                "last_updated": review_queue.last_updated,
            }
            yield f"data: {json.dumps({'type': 'queue_snapshot', 'data': queue_data}, ensure_ascii=False)}\n\n"

            # 持续推送
            while True:
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=30.0)
                    yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
                except asyncio.TimeoutError:
                    # 心跳
                    yield f"data: {json.dumps({'type': 'heartbeat', 'data': {'ts': __import__('datetime').datetime.now().isoformat()}}, ensure_ascii=False)}\n\n"

        except asyncio.CancelledError:
            pass
        finally:
            async with _sse_lock:
                _active_sse_clients.pop(client_id, None)

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


# ── 审核队列端点 ─────────────────────────────────────────


@router.get("/queue", response_model=QueueResponse)
async def get_review_queue():
    """获取当前审核队列."""
    svc = await get_review_service()
    queue = await svc.get_queue()
    return QueueResponse(
        entries=[e.to_dict() for e in queue.entries],
        total_pending=queue.total_pending,
        total_approved=queue.total_approved,
        total_rejected=queue.total_rejected,
        last_updated=queue.last_updated,
    )


@router.get("/entries")
async def list_entries(
    status_filter: Optional[str] = Query(default=None, alias="status"),
    entity_id: Optional[str] = Query(default=None),
    domain: Optional[str] = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
):
    """列表查询审核条目 (支持过滤)."""
    svc = await get_review_service()
    rev_status = ReviewStatus(status_filter) if status_filter else None
    entries = await svc.list_entries(
        status=rev_status,
        entity_id=entity_id,
        domain=domain,
        limit=limit,
        offset=offset,
    )
    return {"entries": [e.to_dict() for e in entries], "count": len(entries)}


@router.get("/{entry_id}")
async def get_review_entry(entry_id: str):
    """获取单条审核条目."""
    svc = await get_review_service()
    entry = await svc.get_entry(entry_id)
    if entry is None:
        raise HTTPException(status_code=404, detail=f"审核条目不存在: {entry_id}")
    return entry.to_dict()


@router.post("/{entry_id}/status")
async def update_review_status(entry_id: str, req: StatusUpdateRequest):
    """更新审核状态 — approve / reject / request_changes / close.

    幂等: 相同 idempotency_key 的重复调用返回已处理结果。
    """
    svc = await get_review_service()

    try:
        updated = await svc.perform_action(
            entry_id=entry_id,
            action=req.action,
            reviewer=req.reviewer,
            comment=req.comment,
            idempotency_key=req.idempotency_key,
        )
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))

    # 广播事件到 SSE 客户端
    await _broadcast_event("entry_status_changed", {
        "entry_id": updated.id,
        "entity_id": updated.entity_id,
        "old_status": "",  # 前端可从旧数据推断
        "new_status": updated.status.value,
        "action": req.action.value,
        "reviewer": req.reviewer,
        "version": updated.version,
        "entity_version": updated.entity_version,
        "updated_at": updated.updated_at,
    })

    # 同时广播队列更新
    queue = await svc.get_queue()
    await _broadcast_event("queue_updated", {
        "total_pending": queue.total_pending,
        "total_approved": queue.total_approved,
        "total_rejected": queue.total_rejected,
        "last_updated": queue.last_updated,
    })

    return updated.to_dict()


# ── 门禁评估端点 ─────────────────────────────────────────


@router.post("/evaluate", response_model=EvaluateResponse)
async def evaluate_and_submit(req: EvaluateAndSubmitRequest):
    """执行门禁评估并提交审核队列.

    纯函数 evaluate() + ReviewService.submit() 的组合。
    """
    # Step 1: 纯函数评估
    ctx = GateEvaluationContext(
        entity_id=req.entity_id,
        entity_type=req.entity_type,
        entity_name=req.entity_name,
        **req.context,
    )
    result = evaluate(ctx)

    # Step 2: 提交审核队列
    svc = await get_review_service()
    entry = await svc.submit(
        entity_id=req.entity_id,
        result=result,
        context=ctx.model_dump(),
        idempotency_key=req.idempotency_key,
        entity_type=req.entity_type,
        entity_name=req.entity_name,
        domain=req.domain,
        severity=req.severity,
    )

    # 广播新增条目
    await _broadcast_event("entry_created", {
        "entry_id": entry.id,
        "entity_id": entry.entity_id,
        "score": entry.evaluation_score,
        "level": entry.evaluation_level.value,
        "passed": entry.evaluation_passed,
        "created_at": entry.created_at,
    })

    return EvaluateResponse(
        entity_id=req.entity_id,
        score=result.score,
        level=result.level.value,
        passed=result.passed,
        reasons=result.reasons,
        warnings=result.warnings,
        blocked_by=result.blocked_by,
        entry_id=entry.id,
    )


@router.post("/evaluate/quick")
async def quick_evaluate_endpoint(req: EvaluateAndSubmitRequest):
    """快速评估并提交 (便捷端点)."""
    return await evaluate_and_submit(req)


@router.get("/health")
async def review_health():
    """审核服务健康检查."""
    svc = await get_review_service()
    pending = await svc.get_pending_count()
    return {
        "status": "ok",
        "pending_count": pending,
        "sse_clients": len(_active_sse_clients),
    }
