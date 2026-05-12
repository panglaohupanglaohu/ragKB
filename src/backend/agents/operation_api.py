# -*- coding: utf-8 -*-
"""操作事件 & 情境切片 API — 查询/追溯/统计 REST 端点.

提供:
  - GET  /api/v1/operations           — 查询操作事件列表
  - GET  /api/v1/operations/{id}      — 获取单个操作事件
  - GET  /api/v1/operations/{id}/trace — 获取操作追溯 (操作+关联切片)
  - GET  /api/v1/operations/{id}/chain — 获取操作因果链
  - GET  /api/v1/context-slices        — 查询情境切片列表
  - GET  /api/v1/context-slices/{id}   — 获取单个情境切片
  - GET  /api/v1/operations/stats      — 存储统计
  - GET  /api/v1/operations/verify     — 完整性验证
  - POST /api/v1/operations/record     — 记录操作事件 (内部调用)

设计原则:
  - 只读端点 (GET) 公开给前端审计面板
  - 写入端点 (POST /record) 供后端 Agent 内部调用
  - 所有响应包含完整性状态
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from .operation_models import (
    OperationEvent,
    OperationType,
    OperationQuery,
    OperationTrace,
    ContextQuery,
    ContextSlice,
    ContextType,
)
from .operation_store import get_operation_store

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/operations", tags=["Operations"])

# 额外的情境切片子路由
slices_router = APIRouter(prefix="/api/v1/context-slices", tags=["Context Slices"])


# ═══════════════════════════════════════════════════════════════
# Pydantic Schemas
# ═══════════════════════════════════════════════════════════════


class RecordOperationRequest(BaseModel):
    """记录操作事件的请求体."""
    operation_type: str = Field(..., description="操作类型: tool_call / task_started / ...")
    agent_id: str = Field(default="system")
    team_id: str = Field(default="default")
    summary: str = Field(default="")
    detail: Optional[Dict[str, Any]] = Field(default_factory=dict)
    parent_operation_id: Optional[str] = None
    session_id: Optional[str] = None
    task_id: Optional[str] = None
    idempotency_key: Optional[str] = None
    # 可选的情境切片
    context_slices: Optional[List[Dict[str, Any]]] = None


class OperationResponse(BaseModel):
    """操作事件响应."""
    ok: bool = True
    operation: Dict[str, Any]


class OperationListResponse(BaseModel):
    """操作事件列表响应."""
    ok: bool = True
    operations: List[Dict[str, Any]]
    total: int
    limit: int
    offset: int


class TraceResponse(BaseModel):
    """操作追溯响应."""
    ok: bool = True
    trace: Dict[str, Any]


class ChainResponse(BaseModel):
    """因果链响应."""
    ok: bool = True
    chain: List[Dict[str, Any]]
    depth: int


class SliceResponse(BaseModel):
    """情境切片响应."""
    ok: bool = True
    slice: Dict[str, Any]


class SliceListResponse(BaseModel):
    """情境切片列表响应."""
    ok: bool = True
    slices: List[Dict[str, Any]]
    total: int
    limit: int
    offset: int


class StatsResponse(BaseModel):
    """统计响应."""
    ok: bool = True
    stats: Dict[str, Any]


class VerifyResponse(BaseModel):
    """完整性验证响应."""
    ok: bool = True
    verification: Dict[str, Any]
    healthy: bool


# ═══════════════════════════════════════════════════════════════
# Operation Endpoints
# ═══════════════════════════════════════════════════════════════


@router.post("/record", response_model=OperationResponse)
async def record_operation(req: RecordOperationRequest):
    """记录一条操作事件 (内部调用).

    支持可选的情境切片列表，原子写入。
    幂等键去重: 相同 idempotency_key 不重复写入。
    """
    store = get_operation_store()

    # 解析 operation_type
    try:
        op_type = OperationType(req.operation_type)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"未知操作类型: {req.operation_type}")

    event = OperationEvent.create(
        operation_type=op_type,
        agent_id=req.agent_id,
        team_id=req.team_id,
        summary=req.summary,
        detail=req.detail or {},
        parent_operation_id=req.parent_operation_id,
        session_id=req.session_id,
        task_id=req.task_id,
        idempotency_key=req.idempotency_key,
    )

    # 构建情境切片
    slices: List[ContextSlice] = []
    if req.context_slices:
        for cs_data in req.context_slices:
            ctx_type_str = cs_data.get("context_type", "custom")
            try:
                ctx_type = ContextType(ctx_type_str)
            except ValueError:
                ctx_type = ContextType.CUSTOM
            cs = ContextSlice.create(
                operation_id=event.operation_id,
                context_type=ctx_type,
                payload=cs_data.get("payload", {}),
                summary=cs_data.get("summary", ""),
                entity_id=cs_data.get("entity_id"),
                entity_type=cs_data.get("entity_type"),
            )
            slices.append(cs)

    if slices:
        ok = await store.record_operation_with_context(event, slices)
    else:
        ok = await store.append_operation(event)

    if not ok:
        return OperationResponse(
            ok=True,
            operation={
                "operation_id": event.operation_id,
                "status": "duplicate (idempotent)",
            }
        )

    return OperationResponse(ok=True, operation=event.to_dict())


@router.get("", response_model=OperationListResponse)
async def list_operations(
    operation_type: Optional[str] = Query(None, description="按操作类型过滤"),
    agent_id: Optional[str] = Query(None, description="按 Agent ID 过滤"),
    team_id: Optional[str] = Query(None, description="按团队 ID 过滤"),
    session_id: Optional[str] = Query(None, description="按会话 ID 过滤"),
    task_id: Optional[str] = Query(None, description="按任务 ID 过滤"),
    parent_operation_id: Optional[str] = Query(None, description="按父操作 ID 过滤"),
    start_time: Optional[str] = Query(None, description="起始时间 (ISO 8601)"),
    end_time: Optional[str] = Query(None, description="结束时间 (ISO 8601)"),
    limit: int = Query(100, ge=1, le=1000, description="返回条数"),
    offset: int = Query(0, ge=0, description="偏移量"),
):
    """查询操作事件列表."""
    store = get_operation_store()

    op_type_enum = None
    if operation_type:
        try:
            op_type_enum = OperationType(operation_type)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"未知操作类型: {operation_type}")

    q = OperationQuery(
        operation_type=op_type_enum,
        agent_id=agent_id,
        team_id=team_id,
        session_id=session_id,
        task_id=task_id,
        parent_operation_id=parent_operation_id,
        start_time=start_time,
        end_time=end_time,
        limit=limit,
        offset=offset,
    )

    results = await store.query_operations(q)
    return OperationListResponse(
        operations=[op.to_dict() for op in results],
        total=len(results),
        limit=limit,
        offset=offset,
    )


@router.get("/stats", response_model=StatsResponse)
async def get_stats():
    """获取操作存储统计."""
    store = get_operation_store()
    stats = await store.get_stats()
    return StatsResponse(ok=True, stats=stats)


@router.get("/verify", response_model=VerifyResponse)
async def verify_integrity():
    """验证存储数据完整性."""
    store = get_operation_store()
    v = await store.verify_all()
    healthy = v["corrupt_ops"] == 0 and v["corrupt_slices"] == 0
    return VerifyResponse(ok=True, verification=v, healthy=healthy)


@router.get("/{operation_id}", response_model=OperationResponse)
async def get_operation(operation_id: str):
    """获取单个操作事件."""
    store = get_operation_store()
    op = await store.get_operation(operation_id)
    if not op:
        raise HTTPException(status_code=404, detail=f"操作 {operation_id} 不存在")
    return OperationResponse(ok=True, operation=op.to_dict())


@router.get("/{operation_id}/trace", response_model=TraceResponse)
async def get_operation_trace(operation_id: str):
    """获取操作追溯 — 操作事件 + 关联情境切片."""
    store = get_operation_store()
    trace = await store.get_trace(operation_id)
    if not trace:
        raise HTTPException(status_code=404, detail=f"操作 {operation_id} 不存在")
    return TraceResponse(ok=True, trace=trace.to_dict())


@router.get("/{operation_id}/chain", response_model=ChainResponse)
async def get_causal_chain(
    operation_id: str,
    max_depth: int = Query(20, ge=1, le=100, description="最大追溯深度"),
):
    """获取操作因果链 — 沿 parent_operation_id 回溯."""
    store = get_operation_store()
    chain = await store.get_causal_chain(operation_id, max_depth=max_depth)
    return ChainResponse(
        ok=True,
        chain=[op.to_dict() for op in chain],
        depth=len(chain),
    )


# ═══════════════════════════════════════════════════════════════
# Context Slice Endpoints (via slices_router)
# ═══════════════════════════════════════════════════════════════


@slices_router.get("", response_model=SliceListResponse)
async def list_slices(
    operation_id: Optional[str] = Query(None, description="按操作 ID 过滤"),
    context_type: Optional[str] = Query(None, description="按情境类型过滤"),
    entity_id: Optional[str] = Query(None, description="按实体 ID 过滤"),
    entity_type: Optional[str] = Query(None, description="按实体类型过滤"),
    start_time: Optional[str] = Query(None, description="起始时间"),
    end_time: Optional[str] = Query(None, description="结束时间"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
):
    """查询情境切片列表."""
    store = get_operation_store()

    ctx_type_enum = None
    if context_type:
        try:
            ctx_type_enum = ContextType(context_type)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"未知情境类型: {context_type}")

    q = ContextQuery(
        operation_id=operation_id,
        context_type=ctx_type_enum,
        entity_id=entity_id,
        entity_type=entity_type,
        start_time=start_time,
        end_time=end_time,
        limit=limit,
        offset=offset,
    )

    results = await store.query_slices(q)
    return SliceListResponse(
        slices=[cs.to_dict() for cs in results],
        total=len(results),
        limit=limit,
        offset=offset,
    )


@slices_router.get("/{slice_id}", response_model=SliceResponse)
async def get_slice(slice_id: str):
    """获取单个情境切片."""
    store = get_operation_store()
    cs = await store.get_slice(slice_id)
    if not cs:
        raise HTTPException(status_code=404, detail=f"切片 {slice_id} 不存在")
    return SliceResponse(ok=True, slice=cs.to_dict())
