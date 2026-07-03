# -*- coding: utf-8 -*-
"""萃取管线 REST API — State Transitions + Todo-driven API.

端点:
  CRUD:
    POST   /api/v1/extraction/pipelines            — 创建管线
    GET    /api/v1/extraction/pipelines            — 列出管线
    GET    /api/v1/extraction/pipelines/{id}       — 获取管线详情
    PATCH  /api/v1/extraction/pipelines/{id}       — 更新管线元数据
    DELETE /api/v1/extraction/pipelines/{id}       — 删除管线

  State Transitions:
    POST   /api/v1/extraction/pipelines/{id}/advance   — 推进到下一阶段
    POST   /api/v1/extraction/pipelines/{id}/reject    — 打回到上一阶段
    POST   /api/v1/extraction/pipelines/{id}/reset     — 重置到草稿
    POST   /api/v1/extraction/pipelines/{id}/check-gate — 仅检查门禁（不迁移）

  Reviewers:
    POST   /api/v1/extraction/pipelines/{id}/reviewers  — 提交复核
    GET    /api/v1/extraction/pipelines/{id}/reviewers  — 获取复核记录

  Todos:
    GET    /api/v1/extraction/todos                    — 获取所有待办
    POST   /api/v1/extraction/pipelines/{id}/todos     — 创建待办
    PATCH  /api/v1/extraction/pipelines/{id}/todos/{tid} — 更新待办
    POST   /api/v1/extraction/pipelines/{id}/todos/{tid}/resolve — 解决待办

  Events:
    GET    /api/v1/extraction/pipelines/{id}/events     — 获取事件流

  Stats:
    GET    /api/v1/extraction/stats                     — 统计概览
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, status, Query
from pydantic import BaseModel, Field

from .extraction_models import (
    PipelineStage,
    TransitionType,
    ReviewerIdentity,
    TodoStatus,
    TodoItem,
    ReviewerRecord,
    GateRequirement,
    default_gate_requirements,
)
from .extraction_pipeline import (
    ExtractionPipelineEngine,
    GateValidationError,
    get_extraction_engine,
)
from .extraction_store import get_extraction_store

router = APIRouter(prefix="/api/v1/extraction", tags=["Extraction Pipeline"])

_engine: Optional[ExtractionPipelineEngine] = None


def _get_engine() -> ExtractionPipelineEngine:
    global _engine
    if _engine is None:
        _engine = get_extraction_engine()
    return _engine


# ── Request Models ──────────────────────────────────────

class CreatePipelineRequest(BaseModel):
    name: str = Field(default="Untitled Pipeline", min_length=1, max_length=256)
    description: str = Field(default="")
    team_id: str = Field(default="")
    created_by: str = Field(default="")
    tags: Optional[List[str]] = None
    gate_requirements: Optional[Dict[str, Dict[str, Any]]] = None


class UpdatePipelineRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    team_id: Optional[str] = None
    tags: Optional[List[str]] = None
    payload: Optional[Dict[str, Any]] = None
    gate_requirements: Optional[Dict[str, Dict[str, Any]]] = None


class TransitionRequest(BaseModel):
    triggered_by: str = Field(default="system")
    force: bool = Field(default=False)


class RejectRequest(BaseModel):
    triggered_by: str = Field(default="system")
    reason: str = Field(default="")


class ReviewSubmission(BaseModel):
    reviewer_id: str = Field(..., min_length=1)
    reviewer_name: str = Field(default="")
    action: str = Field(default="approve", description="approve | reject | request_changes")
    identity: str = Field(default="peer")
    team_id: str = Field(default="")
    comment: str = Field(default="")


class TodoCreateRequest(BaseModel):
    title: str = Field(..., min_length=1)
    description: str = Field(default="")
    assignee_id: str = Field(default="")
    assignee_name: str = Field(default="")
    required_identity: Optional[str] = None
    stage: Optional[str] = None


class TodoUpdateRequest(BaseModel):
    status: Optional[str] = None
    assignee_id: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None


# ── Pipeline CRUD ───────────────────────────────────────

@router.post("/pipelines", status_code=status.HTTP_201_CREATED, summary="创建萃取管线")
async def create_pipeline(req: CreatePipelineRequest):
    """创建一条新的萃取管线."""
    store = get_extraction_store()

    gate_reqs = None
    if req.gate_requirements:
        gate_reqs = {}
        for stage_key, gr_data in req.gate_requirements.items():
            try:
                stage = PipelineStage(stage_key)
                gate_reqs[stage] = GateRequirement(**gr_data)
            except ValueError as e:
                raise HTTPException(400, f"Invalid stage '{stage_key}': {e}")

    pipeline = await store.create_pipeline(
        name=req.name,
        description=req.description,
        team_id=req.team_id,
        created_by=req.created_by,
        tags=req.tags,
        gate_requirements=gate_reqs,
    )
    return pipeline.to_dict()


@router.get("/pipelines", summary="列出萃取管线")
async def list_pipelines(
    stage: Optional[str] = Query(None, description="按阶段过滤"),
    team_id: Optional[str] = Query(None),
):
    """列出所有管线，支持按阶段/团队过滤."""
    store = get_extraction_store()
    stage_enum = PipelineStage(stage) if stage else None
    pipelines = await store.list_pipelines(stage=stage_enum, team_id=team_id)
    return {
        "total": len(pipelines),
        "pipelines": [p.to_dict() for p in pipelines],
    }


@router.get("/pipelines/{pipeline_id}", summary="获取管线详情")
async def get_pipeline(pipeline_id: str):
    """获取单条管线完整信息."""
    store = get_extraction_store()
    pipeline = await store.get_pipeline(pipeline_id)
    if pipeline is None:
        raise HTTPException(404, f"Pipeline '{pipeline_id}' not found")
    return pipeline.to_dict()


@router.patch("/pipelines/{pipeline_id}", summary="更新管线元数据")
async def update_pipeline(pipeline_id: str, req: UpdatePipelineRequest):
    """更新管线基本信息（不触发阶段迁移）."""
    store = get_extraction_store()
    updates = {k: v for k, v in req.model_dump().items() if v is not None}
    if not updates:
        raise HTTPException(400, "No updates provided")

    pipeline = await store.update_pipeline(pipeline_id, updates)
    if pipeline is None:
        raise HTTPException(404, f"Pipeline '{pipeline_id}' not found")
    return pipeline.to_dict()


@router.delete("/pipelines/{pipeline_id}", summary="删除管线")
async def delete_pipeline(pipeline_id: str):
    """删除管线及其关联事件流."""
    store = get_extraction_store()
    deleted = await store.delete_pipeline(pipeline_id)
    if not deleted:
        raise HTTPException(404, f"Pipeline '{pipeline_id}' not found")
    return {"deleted": pipeline_id}


# ── State Transitions ───────────────────────────────────

@router.post("/pipelines/{pipeline_id}/advance", summary="推进到下一阶段")
async def advance_pipeline(pipeline_id: str, req: TransitionRequest = TransitionRequest()):
    """推进管线到下一阶段（需要门禁通过或 force=true）."""
    engine = _get_engine()
    try:
        transition, gate_result = await engine.advance(
            pipeline_id,
            triggered_by=req.triggered_by,
            force=req.force,
        )
    except GateValidationError as e:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "error": "gate_failed",
                "reason": e.result.reason,
                "gate_result": e.result.to_dict(),
            },
        )
    except ValueError as e:
        raise HTTPException(404, str(e))

    if transition is None:
        raise HTTPException(400, gate_result.reason if gate_result else "Cannot advance")

    return {
        "status": "advanced",
        "pipeline_id": pipeline_id,
        "transition": transition.to_dict(),
        "gate_result": gate_result.to_dict() if gate_result else None,
    }


@router.post("/pipelines/{pipeline_id}/reject", summary="打回上一阶段")
async def reject_pipeline(pipeline_id: str, req: RejectRequest = RejectRequest()):
    """将管线打回到上一阶段."""
    engine = _get_engine()
    try:
        transition = await engine.reject(
            pipeline_id,
            triggered_by=req.triggered_by,
            reason=req.reason,
        )
    except ValueError as e:
        raise HTTPException(404, str(e))

    if transition is None:
        raise HTTPException(400, "Cannot reject from current stage")

    return {
        "status": "rejected",
        "pipeline_id": pipeline_id,
        "transition": transition.to_dict(),
    }


@router.post("/pipelines/{pipeline_id}/reset", summary="重置到草稿")
async def reset_pipeline(pipeline_id: str, req: TransitionRequest = TransitionRequest()):
    """重置管线到草稿阶段."""
    engine = _get_engine()
    try:
        transition = await engine.reset(pipeline_id, triggered_by=req.triggered_by)
    except ValueError as e:
        raise HTTPException(404, str(e))

    if transition is None:
        raise HTTPException(400, "Already in draft stage")

    return {
        "status": "reset",
        "pipeline_id": pipeline_id,
        "transition": transition.to_dict(),
    }


@router.post("/pipelines/{pipeline_id}/check-gate", summary="检查门禁条件")
async def check_gate(pipeline_id: str):
    """仅检查门禁条件，不执行迁移."""
    store = get_extraction_store()
    engine = _get_engine()

    pipeline = await store.get_pipeline(pipeline_id)
    if pipeline is None:
        raise HTTPException(404, f"Pipeline '{pipeline_id}' not found")

    gate_result = engine.check_gate(pipeline)
    return gate_result.to_dict()


# ── Reviewers ───────────────────────────────────────────

@router.post("/pipelines/{pipeline_id}/reviewers", summary="提交复核")
async def submit_review(pipeline_id: str, req: ReviewSubmission):
    """提交一条复核记录."""
    engine = _get_engine()
    try:
        pipeline = await engine.submit_review(
            pipeline_id=pipeline_id,
            reviewer_id=req.reviewer_id,
            reviewer_name=req.reviewer_name,
            action=req.action,
            identity=req.identity,
            team_id=req.team_id,
            comment=req.comment,
        )
    except ValueError as e:
        raise HTTPException(400, str(e))

    if pipeline is None:
        raise HTTPException(404, f"Pipeline '{pipeline_id}' not found")

    return {
        "status": "review_submitted",
        "pipeline_id": pipeline_id,
        "stage": pipeline.current_stage.value,
        "reviewers": [r.to_dict() for r in pipeline.reviewers],
    }


@router.get("/pipelines/{pipeline_id}/reviewers", summary="获取复核记录")
async def get_reviewers(pipeline_id: str):
    """获取管线的所有复核记录."""
    store = get_extraction_store()
    pipeline = await store.get_pipeline(pipeline_id)
    if pipeline is None:
        raise HTTPException(404, f"Pipeline '{pipeline_id}' not found")
    return [r.to_dict() for r in pipeline.reviewers]


# ── Todos ───────────────────────────────────────────────

@router.get("/todos", summary="获取所有待办")
async def get_todos(
    assignee_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    pipeline_id: Optional[str] = Query(None),
):
    """获取待办列表，支持按分配人/状态/管线过滤."""
    engine = _get_engine()
    todos = await engine.get_all_todos(assignee_id=assignee_id, status=status)

    if pipeline_id:
        todos = [t for t in todos if t.pipeline_id == pipeline_id]

    return {
        "total": len(todos),
        "todos": [t.to_dict() for t in todos],
    }


@router.post("/pipelines/{pipeline_id}/todos", status_code=status.HTTP_201_CREATED, summary="创建待办")
async def create_todo(pipeline_id: str, req: TodoCreateRequest):
    """手动创建一条待办事项."""
    store = get_extraction_store()
    pipeline = await store.get_pipeline(pipeline_id)
    if pipeline is None:
        raise HTTPException(404, f"Pipeline '{pipeline_id}' not found")

    from .extraction_models import ReviewerIdentity

    todo = TodoItem(
        pipeline_id=pipeline_id,
        stage=PipelineStage(req.stage) if req.stage else pipeline.current_stage,
        title=req.title,
        description=req.description,
        assignee_id=req.assignee_id,
        assignee_name=req.assignee_name,
        required_identity=ReviewerIdentity(req.required_identity) if req.required_identity else None,
    )

    updated = await store.add_todo(pipeline_id, todo)
    return todo.to_dict()


@router.patch("/pipelines/{pipeline_id}/todos/{todo_id}", summary="更新待办")
async def update_todo(pipeline_id: str, todo_id: str, req: TodoUpdateRequest):
    """更新待办事项."""
    store = get_extraction_store()
    updates = {k: v for k, v in req.model_dump().items() if v is not None}
    if not updates:
        raise HTTPException(400, "No updates provided")

    updated = await store.update_todo(pipeline_id, todo_id, updates)
    if updated is None:
        raise HTTPException(404, f"Todo '{todo_id}' not found in pipeline '{pipeline_id}'")
    return updated.to_dict()


@router.post("/pipelines/{pipeline_id}/todos/{todo_id}/resolve", summary="解决待办")
async def resolve_todo(pipeline_id: str, todo_id: str):
    """解决待办并尝试自动推进管线."""
    engine = _get_engine()
    updated = await engine.resolve_todo(pipeline_id, todo_id)
    if updated is None:
        raise HTTPException(404, f"Todo '{todo_id}' not found in pipeline '{pipeline_id}'")

    pipeline = await get_extraction_store().get_pipeline(pipeline_id)
    return {
        "status": "resolved",
        "todo": updated.to_dict(),
        "pipeline_stage": pipeline.current_stage.value if pipeline else "unknown",
    }


# ── Events ──────────────────────────────────────────────

@router.get("/pipelines/{pipeline_id}/events", summary="获取事件流")
async def get_events(pipeline_id: str):
    """获取管线的完整事件流（事件溯源回放）."""
    store = get_extraction_store()
    events = await store.replay_events(pipeline_id)
    pipeline = await store.get_pipeline(pipeline_id)
    return {
        "pipeline_id": pipeline_id,
        "current_stage": pipeline.current_stage.value if pipeline else "unknown",
        "event_count": len(events),
        "events": [e.to_dict() for e in events],
    }


# ── Stats ───────────────────────────────────────────────

@router.get("/stats", summary="统计概览")
async def get_stats():
    """获取所有管线的统计概览."""
    engine = _get_engine()
    return await engine.get_stats()


# ── Enums (for frontend dropdowns) ──────────────────────

@router.get("/enums", summary="获取枚举值")
async def get_enums():
    """返回所有枚举值供前端使用."""
    return {
        "stages": [s.value for s in PipelineStage],
        "identities": [i.value for i in ReviewerIdentity],
        "transition_types": [t.value for t in TransitionType],
        "todo_statuses": [s.value for s in TodoStatus],
    }
