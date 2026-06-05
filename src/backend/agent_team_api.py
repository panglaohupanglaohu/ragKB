# -*- coding: utf-8 -*-
"""
Agent Team API Routes - 双团队管理 REST API

提供构建团队 & 执行团队的状态查询、KPI 考核、
任务分配、报告查询等端点。挂载至 FastAPI 的 router。
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional

router = APIRouter(prefix="/api/v1/agent-teams", tags=["Agent Teams"])

try:
    from config import DEFAULT_PAGE_SIZE as _DEFAULT_PAGE_SIZE
    from config import MAX_PAGE_SIZE as _MAX_PAGE_SIZE
except Exception:
    _DEFAULT_PAGE_SIZE = 50
    _MAX_PAGE_SIZE = 200


# ---------------------------------------------------------------------------
# 全局引用（在 main.py startup 时注入）
# ---------------------------------------------------------------------------
_build_team = None
_execution_team = None
_scheduler = None
_evolution_engine = None


def _paginate_optional(items: List[Dict[str, Any]], *, limit: int, offset: int) -> Any:
    """Preserve old array responses by default while enabling optional pagination."""
    limit = getattr(limit, "default", limit)
    offset = getattr(offset, "default", offset)
    limit = int(limit or 0)
    offset = max(int(offset or 0), 0)
    if limit <= 0 and offset <= 0:
        return items
    if limit <= 0:
        limit = _DEFAULT_PAGE_SIZE
    limit = min(limit, _MAX_PAGE_SIZE)
    total = len(items)
    return {
        "items": items[offset:offset + limit],
        "total": total,
        "limit": limit,
        "offset": offset,
        "has_more": offset + limit < total,
    }


def set_teams(build_team, execution_team, scheduler, evolution_engine=None):
    """在应用启动时由 main.py 调用，注入团队实例."""
    global _build_team, _execution_team, _scheduler, _evolution_engine
    _build_team = build_team
    _execution_team = execution_team
    _scheduler = scheduler
    _evolution_engine = evolution_engine


# ---------------------------------------------------------------------------
# Request / Response Models
# ---------------------------------------------------------------------------

class TaskAssignment(BaseModel):
    agent_id: str
    task: str


class EvolutionCloseRequest(BaseModel):
    reason: str = Field(default="", description="关闭理由")
    verify_conclusion: str = Field(default="", description="验证结论")


class EvolutionCompleteRequest(BaseModel):
    code_changes: List[str] = Field(default_factory=list, description="构建阶段产生的代码或配置变更")
    artifact_dir: str = Field(default="", description="构建阶段产物目录")


class FeedbackSubmission(BaseModel):
    category: str = "optimization"
    severity: str = "medium"
    title: str
    detail: str

# ── 演化优化请求模型 ──────────────────────────────────────────

class OptimizeRequest(BaseModel):
    target_type: str = "skill"
    target_id: str = ""
    team_id: str = "build_system"
    iterations: int = Field(default=5, ge=1, le=10)
    content: str = ""

class AutoTriageRequest(BaseModel):
    team_id: str = "build_system"
    top_n: int = Field(default=5, ge=1, le=10)

class DatasetGenerateRequest(BaseModel):
    skill_id: str = ""
    team_id: str = "build_system"
    count: int = Field(default=15, ge=1, le=30)

class ExampleItem(BaseModel):
    task_input: str
    rubric: str

class DatasetManualRequest(BaseModel):
    dataset_id: str = ""
    skill_id: str = ""
    examples: List[ExampleItem] = Field(default_factory=list)
    skill_name: str = ""

class DatasetImportKBRequest(BaseModel):
    skill_id: str = ""
    skill_name: str = ""
    dataset_id: str = ""
    max_examples: int = Field(default=20, ge=1, le=50)

class UpdateExamplesRequest(BaseModel):
    action: str = "replace_all"
    examples: List[ExampleItem] = Field(default_factory=list)
    indices: List[int] = Field(default_factory=list)
    index: int = -1
    example: Optional[ExampleItem] = None

class StepBaselineRequest(BaseModel):
    skill_id: str = ""
    team_id: str = "build_system"
    dataset_id: str = ""

class FailureItem(BaseModel):
    task_input: str = ""
    rubric: str = ""
    composite: float = 0.0
    reasoning: str = ""

class StepReflectRequest(BaseModel):
    skill_id: str = ""
    team_id: str = "build_system"
    failures: List[FailureItem] = Field(default_factory=list)
    user_hints: str = ""

class StepMutateRequest(BaseModel):
    skill_id: str = ""
    team_id: str = "build_system"
    reflection: Dict[str, Any] = Field(default_factory=dict)

class StepEvaluateCandidateRequest(BaseModel):
    skill_id: str = ""
    team_id: str = "build_system"
    dataset_id: str = ""
    instructions: str = ""

class StepApplyRequest(BaseModel):
    skill_id: str = ""
    team_id: str = "build_system"
    instructions: str = ""
    baseline_score: float = 0.0
    new_score: float = 0.0


# ---------------------------------------------------------------------------
# Minimal AgentScheduler — provides basic scheduling status & tick
# ---------------------------------------------------------------------------

import time as _time


class AgentScheduler:
    """轻量级调度器，提供运行状态、tick 计数、报告生成等基本能力。

    在 main.py startup 时自动创建并注入，确保前端团队概览的
    「调度器」卡片显示「运行中」而非「已停止」。
    """

    def __init__(self) -> None:
        self._started_at = _time.time()
        self._tick_count: int = 0
        self._last_tick_at: float = 0.0

    def get_status(self) -> Dict[str, Any]:
        return {
            "running": True,
            "tick_count": self._tick_count,
            "uptime_seconds": _time.time() - self._started_at,
            "last_tick_at": self._last_tick_at if self._last_tick_at else None,
        }

    def tick_once(self) -> Dict[str, Any]:
        """手动触发一次 tick（供调试/手动推进）."""
        self._tick_count += 1
        self._last_tick_at = _time.time()
        # 每次 tick 尝试驱动 evolution engine 的审查周期（如果存在）
        try:
            global _evolution_engine
            if _evolution_engine is not None:
                _evolution_engine.audit()
        except Exception:
            pass
        return {"tick": self._tick_count, "ok": True}

    def generate_report_now(self) -> Dict[str, Any]:
        return {
            "status": self.get_status(),
            "summary": (f"调度器已运行 {self.get_status()['uptime_seconds']:.0f} 秒，"
                        f"累计 {self._tick_count} 次 tick"),
        }


# ---------------------------------------------------------------------------
# Scheduler API
# ---------------------------------------------------------------------------

@router.get("/scheduler/status")
async def scheduler_status():
    if not _scheduler:
        raise HTTPException(503, "Scheduler not initialized")
    return _scheduler.get_status()


@router.post("/scheduler/report")
async def scheduler_generate_report():
    if not _scheduler:
        raise HTTPException(503, "Scheduler not initialized")
    return _scheduler.generate_report_now()


@router.post("/scheduler/tick")
async def scheduler_tick_once():
    """手动触发一次调度 tick (调试用)."""
    if not _scheduler:
        raise HTTPException(503, "Scheduler not initialized")
    return _scheduler.tick_once()


# ---------------------------------------------------------------------------
# Build Team
# ---------------------------------------------------------------------------

@router.get("/build/status")
async def build_team_status():
    if not _build_team:
        raise HTTPException(503, "Build team not initialized")
    return _build_team.get_status()


@router.get("/build/kpis")
async def build_team_kpis():
    if not _build_team:
        raise HTTPException(503, "Build team not initialized")
    return _build_team.get_agent_kpis()


@router.get("/build/agents/{agent_id}")
async def build_agent_detail(agent_id: str):
    if not _build_team:
        raise HTTPException(503, "Build team not initialized")
    agent = _build_team.agents.get(agent_id)
    if not agent:
        raise HTTPException(404, f"Agent '{agent_id}' not found")
    return agent.to_dict()


@router.post("/build/assign")
async def build_assign_task(body: TaskAssignment):
    if not _build_team:
        raise HTTPException(503, "Build team not initialized")
    ok = _build_team.assign_task(body.agent_id, body.task)
    if not ok:
        raise HTTPException(404, f"Agent '{body.agent_id}' not found")
    return {"status": "assigned", "agent_id": body.agent_id, "task": body.task}


@router.get("/build/reports")
async def build_reports(
    limit: int = Query(default=10, ge=0, le=_MAX_PAGE_SIZE),
    offset: int = Query(default=0, ge=0),
):
    if not _build_team:
        raise HTTPException(503, "Build team not initialized")
    items = [r.to_dict() for r in _build_team.hourly_reports]
    if limit > 0 and offset == 0:
        items = items[-limit:]
        return items
    return _paginate_optional(items, limit=limit, offset=offset)


@router.get("/build/issues")
async def build_issues(
    limit: int = Query(default=0, ge=0, le=_MAX_PAGE_SIZE),
    offset: int = Query(default=0, ge=0),
):
    if not _build_team:
        raise HTTPException(503, "Build team not initialized")
    items = list(_build_team.issue_backlog)
    return _paginate_optional(items, limit=limit, offset=offset)


# ---------------------------------------------------------------------------
# Execution Team
# ---------------------------------------------------------------------------

@router.get("/execution/status")
async def execution_team_status():
    if not _execution_team:
        raise HTTPException(503, "Execution team not initialized")
    return _execution_team.get_status()


@router.get("/execution/agents/{agent_id}")
async def execution_agent_detail(agent_id: str):
    if not _execution_team:
        raise HTTPException(503, "Execution team not initialized")
    agent = _execution_team.agents.get(agent_id)
    if not agent:
        raise HTTPException(404, f"Agent '{agent_id}' not found")
    return agent.to_dict()


@router.get("/execution/reports")
async def execution_reports(
    limit: int = Query(default=10, ge=0, le=_MAX_PAGE_SIZE),
    offset: int = Query(default=0, ge=0),
):
    if not _execution_team:
        raise HTTPException(503, "Execution team not initialized")
    items = [r.to_dict() for r in _execution_team.execution_reports]
    if limit > 0 and offset == 0:
        items = items[-limit:]
        return items
    return _paginate_optional(items, limit=limit, offset=offset)


@router.get("/execution/feedback")
async def execution_feedback(
    limit: int = Query(default=0, ge=0, le=_MAX_PAGE_SIZE),
    offset: int = Query(default=0, ge=0),
):
    if not _execution_team:
        raise HTTPException(503, "Execution team not initialized")
    items = [item.to_dict() for item in _execution_team.feedback_queue]
    return _paginate_optional(items, limit=limit, offset=offset)


@router.post("/execution/feedback")
async def submit_feedback(body: FeedbackSubmission):
    if not _execution_team:
        raise HTTPException(503, "Execution team not initialized")
    item = _execution_team.submit_feedback(
        category=body.category,
        severity=body.severity,
        title=body.title,
        detail=body.detail,
    )
    return item.to_dict()


# ---------------------------------------------------------------------------
# Combined
# ---------------------------------------------------------------------------

@router.get("/overview")
async def teams_overview(team_id: Optional[str] = None):
    """一站式获取双团队全局概览."""
    result: Dict[str, Any] = {}
    if _build_team:
        bs = _build_team.get_status()
        result["build_team"] = {
            "health": bs["health"],
            "agent_count": bs["agent_count"],
            "metrics": bs["metrics"],
        }
    if _execution_team:
        es = _execution_team.get_status()
        result["execution_team"] = {
            "health": es["health"],
            "agent_count": es["agent_count"],
            "metrics": es["metrics"],
        }
    if _scheduler:
        result["scheduler"] = _scheduler.get_status()
    if _evolution_engine:
        result["evolution"] = {
            **_evolution_engine.get_status(),
            "compliance_rating": _serialize_compliance_rating(),
        }
    if team_id:
        result["current_team"] = _serialize_current_team(team_id)
    return result


def _serialize_current_team(team_id: str) -> Optional[Dict[str, Any]]:
    try:
        from .agents.api import _summarize_team_tasks, _team_manager
    except ImportError:
        from agents.api import _summarize_team_tasks, _team_manager

    if _team_manager is None:
        return None

    team = _team_manager.get_team(team_id)
    if team is None:
        return None

    return {
        **team.to_dict(),
        "tasks": _summarize_team_tasks(team_id),
    }


# ---------------------------------------------------------------------------
# System Evolution (自我演进引擎)
# ---------------------------------------------------------------------------

@router.get("/evolution/status")
async def evolution_status():
    """获取自我演进引擎状态。"""
    if not _evolution_engine:
        raise HTTPException(404, "Evolution engine not registered")
    status = _evolution_engine.get_status()
    return {
        "status": "initialized" if status.get("initialized") else "not_initialized",
        **status,
    }


@router.get("/evolution/summary")
async def evolution_summary():
    """获取演进项汇总。"""
    if not _evolution_engine:
        raise HTTPException(404, "Evolution engine not registered")
    return _evolution_engine.get_evolution_summary()


@router.get("/evolution/items")
async def evolution_items(status: Optional[str] = None, limit: int = Query(default=50, ge=1, le=200), offset: int = Query(default=0, ge=0)):
    """获取演进项列表，可按状态过滤、分页。"""
    if not _evolution_engine:
        raise HTTPException(404, "Evolution engine not registered")
    items = _evolution_engine.get_evolution_items(status=status)
    total = len(items)
    sliced = items[offset:offset + limit]
    return {
        "items": sliced,
        "total": total,
        "limit": limit,
        "offset": offset,
        "has_more": offset + limit < total,
    }


@router.get("/evolution/rules")
async def evolution_rules(limit: int = Query(default=50, ge=1, le=200), offset: int = Query(default=0, ge=0)):
    """获取审查规则列表（分页）。"""
    if not _evolution_engine:
        raise HTTPException(404, "Evolution engine not registered")
    items = [r.to_dict() for r in _evolution_engine.audit_rules]
    total = len(items)
    sliced = items[offset:offset + limit]
    return {
        "items": sliced,
        "total": total,
        "limit": limit,
        "offset": offset,
        "has_more": offset + limit < total,
    }


@router.post("/evolution/audit")
async def evolution_run_audit():
    """手动触发一次审查。"""
    if not _evolution_engine:
        raise HTTPException(404, "Evolution engine not registered")
    return _evolution_engine.run_full_audit()


@router.post("/evolution/cycle")
async def evolution_run_cycle():
    """运行完整演进周期（审查→派发→验证→关闭）。"""
    if not _evolution_engine:
        raise HTTPException(404, "Evolution engine not registered")
    return _evolution_engine.run_evolution_cycle()


@router.post("/evolution/dispatch")
async def evolution_dispatch():
    """派发所有待处理演进项给 Build 团队。"""
    if not _evolution_engine:
        raise HTTPException(404, "Evolution engine not registered")
    return _evolution_engine.dispatch_all_pending()


@router.post("/evolution/verify")
async def evolution_verify():
    """验证所有待验证项。"""
    if not _evolution_engine:
        raise HTTPException(404, "Evolution engine not registered")
    return _evolution_engine.verify_all_pending()


@router.get("/evolution/items/{item_id}")
async def evolution_item_detail(item_id: str):
    """获取单个演进项详情。"""
    if not _evolution_engine:
        raise HTTPException(404, "Evolution engine not registered")
    item = _evolution_engine.evolution_items.get(item_id)
    if not item:
        raise HTTPException(404, f"Item '{item_id}' not found")
    detail = item.to_dict()
    try:
        from agents.evidence_store import get_evidence_store
        store = get_evidence_store()
        evidence_runs = await store.query_for_object("evolution", item_id, limit=50)
        related_runs = list(evidence_runs)
        if item.build_task_id:
            related_runs.extend(await store.query_for_object("task", item.build_task_id, limit=20))
        seen = set()
        deduped = []
        for run in related_runs:
            if run.evidence_id in seen:
                continue
            seen.add(run.evidence_id)
            deduped.append(run)
        detail["evidence_runs"] = [run.to_dict() for run in deduped]
    except Exception:
        detail["evidence_runs"] = []
    return detail


@router.post("/evolution/items/{item_id}/verify")
async def evolution_verify_item(item_id: str):
    """验证单个待验证演进项。"""
    if not _evolution_engine:
        raise HTTPException(404, "Evolution engine not registered")
    item = _evolution_engine.evolution_items.get(item_id)
    if not item:
        raise HTTPException(404, f"Item '{item_id}' not found")
    return _evolution_engine.verify_pending_items(item_ids=[item_id])


@router.post("/evolution/items/{item_id}/close")
async def evolution_close_item(item_id: str, req: EvolutionCloseRequest):
    """关闭单个已验证演进项，要求记录关闭理由和验证结论。"""
    if not _evolution_engine:
        raise HTTPException(404, "Evolution engine not registered")
    item = _evolution_engine.evolution_items.get(item_id)
    if not item:
        raise HTTPException(404, f"Item '{item_id}' not found")
    if item.status != "verified":
        raise HTTPException(400, "Only verified evolution items can be closed")
    closed = _evolution_engine.close_verified_items(
        item_ids=[item_id],
        close_reason=req.reason,
        verify_conclusion=req.verify_conclusion,
    )
    return {"closed": closed, "count": len(closed), "item_id": item_id}


@router.post("/evolution/items/{item_id}/progress")
async def evolution_mark_progress(item_id: str):
    """标记演进项为进行中。"""
    if not _evolution_engine:
        raise HTTPException(404, "Evolution engine not registered")
    ok = _evolution_engine.mark_in_progress(item_id)
    if not ok:
        raise HTTPException(404, f"Item '{item_id}' not found")
    return {"status": "ok", "item_id": item_id, "new_status": "in_progress"}


@router.post("/evolution/items/{item_id}/complete")
async def evolution_mark_complete(item_id: str, req: Optional[EvolutionCompleteRequest] = None):
    """标记演进项构建完成，进入待验证。"""
    if not _evolution_engine:
        raise HTTPException(404, "Evolution engine not registered")
    item = _evolution_engine.evolution_items.get(item_id)
    if not item:
        raise HTTPException(404, f"Item '{item_id}' not found")
    req = req or EvolutionCompleteRequest()
    ok = _evolution_engine.mark_build_complete(
        item_id,
        code_changes=req.code_changes,
        artifact_dir=req.artifact_dir,
    )
    if not ok:
        raise HTTPException(400, "Build completion requires code_changes or artifact_dir")
    return {"status": "ok", "item_id": item_id, "new_status": "verify_pending"}


@router.post("/evolution/close-verified")
async def evolution_close_verified():
    """关闭所有已验证通过的演进项。"""
    if not _evolution_engine:
        raise HTTPException(404, "Evolution engine not registered")
    closed = _evolution_engine.close_verified()
    return {"closed": closed, "count": len(closed)}


@router.post("/evolution/close")
async def evolution_close():
    """关闭所有已验证通过的演进项 (close-verified 别名)。"""
    if not _evolution_engine:
        raise HTTPException(404, "Evolution engine not registered")
    closed = _evolution_engine.close_verified()
    return {"closed": closed, "count": len(closed)}


@router.get("/evolution/history")
async def evolution_audit_history(limit: int = Query(default=50, ge=1, le=200), offset: int = Query(default=0, ge=0)):
    """获取审查历史记录（分页）。"""
    if not _evolution_engine:
        raise HTTPException(404, "Evolution engine not registered")
    raw = _evolution_engine.get_audit_history()
    # Normalize field names for frontend (expects timestamp, total)
    result = []
    for h in raw:
        entry = dict(h)
        entry.setdefault("timestamp", entry.pop("time", None))
        entry.setdefault("total", (entry.get("passed") or 0) + (entry.get("failed") or 0) + (entry.get("skipped") or 0))
        result.append(entry)
    total = len(result)
    sliced = result[offset:offset + limit]
    return {
        "items": sliced,
        "total": total,
        "limit": limit,
        "offset": offset,
        "has_more": offset + limit < total,
    }


@router.get("/evolution/analytics")
async def evolution_analytics():
    """获取演进分析数据 (域覆盖、严重度分布、趋势)。"""
    if not _evolution_engine:
        raise HTTPException(404, "Evolution engine not registered")
    summary = _evolution_engine.get_evolution_summary()
    history = _evolution_engine.get_audit_history()
    status = _evolution_engine.get_status()

    return {
        "summary": summary,
        "history": history,
        "stats": status.get("stats", {}),
        "items_by_status": status.get("items_by_status", {}),
        "rules_count": status.get("audit_rules_count", 0),
    }


# ---------------------------------------------------------------------------
# Phase 3: 业界标准化改进 API
# ---------------------------------------------------------------------------

@router.get("/evolution/compliance-rating")
async def evolution_compliance_rating():
    """获取 DNV CII 风格 A~E 合规评级。"""
    if not _evolution_engine:
        raise HTTPException(404, "Evolution engine not registered")
    return _serialize_compliance_rating()


def _serialize_compliance_rating() -> Dict[str, Any]:
    data = _evolution_engine.get_compliance_rating()
    data["grade"] = data.get("rating", "?")
    data["description"] = data.get("rating_label", "")
    escalation = _evolution_engine.get_escalation_status()
    data["escalation_tier"] = "corrective" if escalation.get("escalated_count", 0) > 0 else "normal"
    return data


@router.post("/evolution/compliance-rating/calculate")
async def evolution_calculate_rating():
    """重新计算合规评级 (运行快速审查)。"""
    if not _evolution_engine:
        raise HTTPException(404, "Evolution engine not registered")
    return _evolution_engine.calculate_compliance_rating()


@router.get("/evolution/checklist")
async def evolution_checklist(level: Optional[str] = None):
    """获取 ClassNK 双层自查清单 (company/ship)。"""
    if not _evolution_engine:
        raise HTTPException(404, "Evolution engine not registered")
    return _evolution_engine.get_checklist(level=level)


@router.get("/evolution/zones")
async def evolution_zones():
    """获取所有合规区域。"""
    if not _evolution_engine:
        raise HTTPException(404, "Evolution engine not registered")
    return _evolution_engine.get_all_zones()


@router.get("/evolution/zones/active")
async def evolution_active_zones():
    """获取当前激活的合规区域。"""
    if not _evolution_engine:
        raise HTTPException(404, "Evolution engine not registered")
    return _evolution_engine.get_active_zones()


@router.post("/evolution/zones/update-position")
async def evolution_update_position(lat: float = 0.0, lon: float = 0.0):
    """更新船舶位置，自动检测合规区域进入/离开。"""
    if not _evolution_engine:
        raise HTTPException(404, "Evolution engine not registered")
    return _evolution_engine.update_vessel_position(lat, lon)


@router.get("/evolution/escalation")
async def evolution_escalation():
    """获取失败升级状态 (DNV SEEMP Part III 风格)。"""
    if not _evolution_engine:
        raise HTTPException(404, "Evolution engine not registered")
    return _evolution_engine.get_escalation_status()


@router.get("/evolution/trend")
async def evolution_trend():
    """获取合规评级趋势分析。"""
    if not _evolution_engine:
        raise HTTPException(404, "Evolution engine not registered")
    data = _evolution_engine.get_trend_analysis()
    # Frontend expects improvement_rate
    delta = data.get("trend_delta", 0.0)
    data["improvement_rate"] = round(delta, 1)
    return data


@router.get("/evolution/monitoring")
async def evolution_monitoring():
    """获取连续监控状态。"""
    if not _evolution_engine:
        raise HTTPException(404, "Evolution engine not registered")
    data = _evolution_engine.get_monitoring_status()
    # Frontend expects 'active' bool and 'last_check' timestamp
    data["active"] = True
    if _evolution_engine._last_monitoring_time:
        from datetime import datetime as _dt
        data["last_check"] = _dt.fromtimestamp(_evolution_engine._last_monitoring_time).isoformat()
    else:
        data["last_check"] = None
    return data


@router.get("/evolution/audit-trail")
async def evolution_audit_trail(event_type: Optional[str] = None, limit: int = Query(default=50, ge=1, le=200), offset: int = Query(default=0, ge=0)):
    """获取审计轨迹日志（分页）。"""
    if not _evolution_engine:
        raise HTTPException(404, "Evolution engine not registered")
    items = _evolution_engine.get_audit_trail(event_type=event_type)
    total = len(items)
    sliced = items[offset:offset + limit]
    return {
        "items": sliced,
        "total": total,
        "limit": limit,
        "offset": offset,
        "has_more": offset + limit < total,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# 演化优化 API (Phase 1-5: Qwen 反思式演化)
# ═══════════════════════════════════════════════════════════════════════════════

@router.post("/evolution/optimize")
async def evolution_optimize(body: OptimizeRequest):
    """启动技能/规则/提示词优化 (Phase 1-3).

    Body: {target_type: "skill"|"rule"|"prompt", target_id, team_id, iterations?}
    """
    from agents.evolution.optimizer import optimize_skill, optimize_rule_description, optimize_prompt_section
    from agents.skill_library import get_skill_library

    target_type = body.target_type
    target_id = body.target_id
    team_id = body.team_id
    iterations = body.iterations

    if not target_id:
        raise HTTPException(400, "target_id required")

    if target_type == "skill":
        lib = get_skill_library()
        if not lib:
            raise HTTPException(500, "Skill library not initialized")
        skill = lib._find_skill(team_id, target_id)
        if not skill:
            raise HTTPException(404, f"Skill {target_id} not found")

        import asyncio
        run = await optimize_skill(
            team_id=team_id,
            skill_id=target_id,
            skill_name=skill.name,
            instructions=skill.instructions,
            tags=skill.tags if hasattr(skill, 'tags') else [],
            iterations=iterations,
        )
        return run.to_dict()

    elif target_type == "rule":
        if not _evolution_engine:
            raise HTTPException(404, "Evolution engine not registered")
        rules = _evolution_engine.get_rules()
        rule = next((r for r in rules if r.get("id") == target_id), None)
        if not rule:
            raise HTTPException(404, f"Rule {target_id} not found")

        run = await optimize_rule_description(
            rule_id=target_id,
            current_title=rule.get("title", ""),
            current_description=rule.get("description", ""),
            iterations=iterations,
        )
        return run.to_dict()

    elif target_type == "prompt":
        content = body.content
        if not content:
            raise HTTPException(400, "content required for prompt optimization")
        run = await optimize_prompt_section(
            section_name=target_id,
            current_content=content,
            team_id=team_id,
            iterations=iterations,
        )
        return run.to_dict()

    raise HTTPException(400, f"Unknown target_type: {target_type}")


@router.get("/evolution/optimize/runs")
async def evolution_optimize_runs(target_type: Optional[str] = None, limit: int = Query(default=20, ge=1, le=200), offset: int = Query(default=0, ge=0)):
    """列出优化运行记录（分页）。"""
    from agents.evolution.optimizer import list_runs
    items = list_runs(target_type=target_type, limit=limit + offset)
    sliced = items[offset:offset + limit]
    return {
        "items": sliced,
        "total": len(items),
        "limit": limit,
        "offset": offset,
        "has_more": offset + limit < len(items),
    }


@router.get("/evolution/optimize/{run_id}")
async def evolution_optimize_result(run_id: str):
    """获取单次优化运行的详细结果."""
    from agents.evolution.optimizer import OptimizationRun
    run = OptimizationRun.load(run_id)
    if not run:
        raise HTTPException(404, f"Run {run_id} not found")
    return run.to_dict()


@router.get("/evolution/optimize/{run_id}/compare")
async def evolution_optimize_compare(run_id: str):
    """获取 baseline vs evolved 对比视图."""
    from agents.evolution.optimizer import OptimizationRun
    from agents.evolution.comparator import compare_results
    run = OptimizationRun.load(run_id)
    if not run:
        raise HTTPException(404, f"Run {run_id} not found")
    return compare_results(
        original_instructions=run.original_instructions,
        evolved_instructions=run.best_instructions,
        baseline_score=run.baseline_score,
        evolved_score=run.best_score,
        iteration_log=run.iteration_log,
    )


@router.post("/evolution/optimize/{run_id}/approve")
async def evolution_optimize_approve(run_id: str):
    """批准演化结果 — 应用到技能并走棘轮锁定.

    照搬 Hermes: Deploy via PR (ratchet lock).
    """
    from agents.evolution.optimizer import OptimizationRun
    from agents.skill_evolver import get_skill_evolver

    run = OptimizationRun.load(run_id)
    if not run:
        raise HTTPException(404, f"Run {run_id} not found")
    if not run.improved:
        raise HTTPException(400, "Run did not produce improvement (delta < 5%)")
    if run.target_type != "skill":
        raise HTTPException(400, "Only skill approval implemented")

    evolver = get_skill_evolver()
    result = evolver.apply_evolution(
        team_id=run.team_id,
        skill_id=run.target_id,
        new_instructions=run.best_instructions,
    )
    if result.get("error"):
        raise HTTPException(500, result["error"])

    return {
        "status": "approved_and_applied",
        "skill_id": run.target_id,
        "new_version": result.get("version"),
        "score_improvement": f"+{run.score_delta * 100:.1f}%",
    }


@router.post("/evolution/fitness/skill/{skill_id}")
async def evolution_skill_fitness(skill_id: str, team_id: str = "build_system"):
    """评估单个技能的 fitness 分数 (Phase 1 核心)."""
    from agents.evolution.dataset_builder import build_full_dataset
    from agents.evolution.fitness import evaluate_skill
    from agents.skill_library import get_skill_library

    lib = get_skill_library()
    if not lib:
        raise HTTPException(500, "Skill library not initialized")
    skill = lib._find_skill(team_id, skill_id)
    if not skill:
        raise HTTPException(404, f"Skill {skill_id} not found")

    dataset = await build_full_dataset(
        skill_name=skill.name,
        skill_id=skill_id,
        instructions=skill.instructions,
        tags=skill.tags if hasattr(skill, 'tags') else [],
        synthetic_count=8,
    )

    if len(dataset.val) < 2:
        raise HTTPException(500, "Failed to generate sufficient eval examples")

    report = await evaluate_skill(
        skill_id=skill_id,
        skill_name=skill.name,
        instructions=skill.instructions,
        eval_examples=dataset.val,
    )
    return report.to_dict()


@router.post("/evolution/auto-triage")
async def evolution_auto_triage(body: Optional[AutoTriageRequest] = None):
    """自动诊断 — 识别最需要优化的技能 (Phase 5)."""
    from agents.evolution.auto_triage import run_auto_triage
    body = body or AutoTriageRequest()
    return await run_auto_triage(team_id=body.team_id, top_n=body.top_n)


@router.post("/evolution/dataset/generate")
async def evolution_generate_dataset(body: DatasetGenerateRequest):
    """为指定技能生成评估数据集."""
    from agents.evolution.dataset_builder import build_full_dataset
    from agents.skill_library import get_skill_library

    skill_id = body.skill_id
    team_id = body.team_id
    count = body.count

    if not skill_id:
        raise HTTPException(400, "skill_id required")

    lib = get_skill_library()
    if not lib:
        raise HTTPException(500, "Skill library not initialized")
    skill = lib._find_skill(team_id, skill_id)
    if not skill:
        raise HTTPException(404, f"Skill {skill_id} not found")

    dataset = await build_full_dataset(
        skill_name=skill.name,
        skill_id=skill_id,
        instructions=skill.instructions,
        tags=skill.tags if hasattr(skill, 'tags') else [],
        synthetic_count=count,
    )
    dataset.save("skills")
    return dataset.to_dict()


# ═══════════════════════════════════════════════════════════════════════════════
# 交互式演化步骤 API (Step-by-Step)
# ═══════════════════════════════════════════════════════════════════════════════

def _get_ds_dir():
    """Get the evolution datasets directory path."""
    from pathlib import Path
    ds_dir = Path(__file__).resolve().parent / "agents" / ".." / ".." / "storage" / "evolution_datasets" / "skills"
    ds_dir = ds_dir.resolve()
    ds_dir.mkdir(parents=True, exist_ok=True)
    return ds_dir


def _load_dataset(dataset_id: str):
    """Load an EvalDataset by its ID."""
    from agents.evolution.dataset_builder import EvalDataset
    ds_dir = _get_ds_dir()
    found = list(ds_dir.glob(f"*_{dataset_id}.json"))
    if not found:
        raise HTTPException(404, f"Dataset {dataset_id} not found")
    return EvalDataset.load(str(found[0]))

@router.post("/evolution/dataset/manual")
async def evolution_dataset_manual(body: DatasetManualRequest):
    """手动添加评估用例到数据集."""
    from agents.evolution.dataset_builder import EvalDataset

    dataset_id = body.dataset_id
    skill_id = body.skill_id
    examples = body.examples

    if not examples:
        raise HTTPException(400, "examples required")

    # Load existing or create new
    if dataset_id:
        ds = _load_dataset(dataset_id)
    else:
        if not skill_id:
            raise HTTPException(400, "skill_id required when creating new dataset")
        ds = EvalDataset(skill_id=skill_id, skill_name=body.skill_name)

    # Add examples
    for ex in examples:
        ds.examples.append({"task_input": ex.task_input, "rubric": ex.rubric})

    ds.split()
    ds.save("skills")
    return ds.to_dict()


@router.post("/evolution/dataset/import-kb")
async def evolution_dataset_import_kb(body: DatasetImportKBRequest):
    """从知识库抽取评估用例."""
    from agents.evolution.dataset_builder import EvalDataset, mine_knowledge_base

    skill_id = body.skill_id
    skill_name = body.skill_name or skill_id
    dataset_id = body.dataset_id
    max_examples = body.max_examples

    if not skill_id:
        raise HTTPException(400, "skill_id required")

    mined = mine_knowledge_base(skill_id, skill_name, max_examples=max_examples)

    if dataset_id:
        try:
            ds = _load_dataset(dataset_id)
        except HTTPException:
            ds = EvalDataset(skill_id=skill_id, skill_name=skill_name)
    else:
        ds = EvalDataset(skill_id=skill_id, skill_name=skill_name)

    for ex in mined:
        ds.examples.append({"task_input": ex["task_input"], "rubric": ex["rubric"]})

    ds.split()
    ds.save("skills")
    return {"dataset": ds.to_dict(), "imported_count": len(mined)}


@router.get("/evolution/dataset/{dataset_id}")
async def evolution_get_dataset(dataset_id: str):
    """获取数据集详情."""
    ds = _load_dataset(dataset_id)
    return ds.to_dict()


@router.put("/evolution/dataset/{dataset_id}/examples")
async def evolution_update_dataset_examples(dataset_id: str, body: UpdateExamplesRequest):
    """编辑数据集中的用例."""
    from agents.evolution.dataset_builder import EvalDataset

    ds = _load_dataset(dataset_id)
    action = body.action

    if action == "replace_all":
        ds.examples = [{"task_input": ex.task_input, "rubric": ex.rubric} for ex in body.examples]
    elif action == "delete":
        indices = sorted(body.indices, reverse=True)
        for idx in indices:
            if 0 <= idx < len(ds.examples):
                ds.examples.pop(idx)
    elif action == "update":
        idx = body.index
        example = body.example
        if 0 <= idx < len(ds.examples) and example and example.task_input and example.rubric:
            ds.examples[idx] = {"task_input": example.task_input, "rubric": example.rubric}

    ds.split()
    ds.save("skills")
    return ds.to_dict()


@router.post("/evolution/step/baseline")
async def evolution_step_baseline(body: StepBaselineRequest):
    """步骤2: 在已有数据集上评估 baseline."""
    from agents.evolution.fitness import evaluate_skill
    from agents.skill_library import get_skill_library

    skill_id = body.skill_id
    team_id = body.team_id
    dataset_id = body.dataset_id

    if not skill_id or not dataset_id:
        raise HTTPException(400, "skill_id and dataset_id required")

    lib = get_skill_library()
    if not lib:
        raise HTTPException(500, "Skill library not initialized")
    skill = lib._find_skill(team_id, skill_id)
    if not skill:
        raise HTTPException(404, f"Skill {skill_id} not found")

    ds = _load_dataset(dataset_id)

    eval_set = ds.val if ds.val else ds.examples[:5]
    if len(eval_set) < 1:
        raise HTTPException(400, "Dataset too small for evaluation")

    report = await evaluate_skill(
        skill_id=skill_id,
        skill_name=skill.name,
        instructions=skill.instructions,
        eval_examples=eval_set,
    )
    return {**report.to_dict(), "dataset_id": dataset_id, "eval_count": len(eval_set)}


@router.post("/evolution/step/reflect")
async def evolution_step_reflect(body: StepReflectRequest):
    """步骤3: 反思分析 — 可传入用户补充的 hints."""
    from agents.evolution.mutator import reflect_on_failures
    from agents.skill_library import get_skill_library

    skill_id = body.skill_id
    team_id = body.team_id
    failures = [{"task_input": f.task_input, "rubric": f.rubric, "composite": f.composite, "reasoning": f.reasoning} for f in body.failures]
    user_hints = body.user_hints

    if not skill_id:
        raise HTTPException(400, "skill_id required")

    lib = get_skill_library()
    if not lib:
        raise HTTPException(500, "Skill library not initialized")
    skill = lib._find_skill(team_id, skill_id)
    if not skill:
        raise HTTPException(404, f"Skill {skill_id} not found")

    instructions = skill.instructions
    if user_hints:
        # Inject user hints into the failures context
        failures = failures or []
        failures.append({
            "task_input": f"[用户反馈] {user_hints}",
            "rubric": "用户指出的问题方向",
            "composite": 0.0,
            "reasoning": user_hints,
        })

    if not failures:
        raise HTTPException(400, "failures required (from baseline evaluation)")

    reflection = await reflect_on_failures(instructions, failures)
    return {
        "root_causes": reflection.root_causes,
        "specific_defects": reflection.specific_defects,
        "improvement_directions": reflection.improvement_directions,
    }


@router.post("/evolution/step/mutate")
async def evolution_step_mutate(body: StepMutateRequest):
    """步骤4: 生成变异候选."""
    from agents.evolution.mutator import ReflectionResult, generate_candidates
    from agents.skill_library import get_skill_library

    skill_id = body.skill_id
    team_id = body.team_id
    reflection_data = body.reflection

    if not skill_id or not reflection_data:
        raise HTTPException(400, "skill_id and reflection required")

    lib = get_skill_library()
    if not lib:
        raise HTTPException(500, "Skill library not initialized")
    skill = lib._find_skill(team_id, skill_id)
    if not skill:
        raise HTTPException(404, f"Skill {skill_id} not found")

    # Build ReflectionResult from data
    reflection = ReflectionResult()
    reflection.root_causes = reflection_data.get("root_causes", [])
    reflection.specific_defects = reflection_data.get("specific_defects", [])
    reflection.improvement_directions = reflection_data.get("improvement_directions", [])

    candidates = await generate_candidates(skill.instructions, reflection)
    return {
        "candidates": [
            {"strategy": c.strategy, "instructions": c.instructions, "summary": c.summary if hasattr(c, 'summary') else ""}
            for c in candidates
        ]
    }


@router.post("/evolution/step/evaluate-candidate")
async def evolution_step_evaluate_candidate(body: StepEvaluateCandidateRequest):
    """步骤4b: 评估单个候选."""
    from agents.evolution.constraints import validate_all
    from agents.evolution.fitness import apply_length_penalty, evaluate_skill
    from agents.skill_library import get_skill_library

    skill_id = body.skill_id
    team_id = body.team_id
    dataset_id = body.dataset_id
    candidate_instructions = body.instructions

    if not skill_id or not candidate_instructions:
        raise HTTPException(400, "skill_id and instructions required")

    lib = get_skill_library()
    if not lib:
        raise HTTPException(500, "Skill library not initialized")
    skill = lib._find_skill(team_id, skill_id)
    if not skill:
        raise HTTPException(404, f"Skill {skill_id} not found")

    # Constraint check first
    cv = validate_all(skill.instructions, candidate_instructions, "skill")
    if not cv["passed"]:
        return {"passed_constraints": False, "violations": cv["violations"], "score": 0}

    # Load dataset for evaluation
    eval_set = []
    if dataset_id:
        try:
            ds = _load_dataset(dataset_id)
            eval_set = ds.val if ds.val else ds.examples[:5]
        except HTTPException:
            pass

    if not eval_set:
        raise HTTPException(400, "dataset_id required or dataset too small")

    report = await evaluate_skill(
        skill_id=skill_id,
        skill_name=skill.name,
        instructions=candidate_instructions,
        eval_examples=eval_set,
    )

    score = apply_length_penalty(
        report.mean_composite,
        len(skill.instructions),
        len(candidate_instructions),
    )

    return {
        "passed_constraints": True,
        "score": round(score, 3),
        "raw_score": round(report.mean_composite, 3),
        "details": report.to_dict(),
        "length_original": len(skill.instructions),
        "length_candidate": len(candidate_instructions),
    }


@router.post("/evolution/step/apply")
async def evolution_step_apply(body: StepApplyRequest):
    """步骤5: 应用选中的变异到技能 (棘轮锁定)."""
    from agents.skill_evolver import get_skill_evolver

    skill_id = body.skill_id
    team_id = body.team_id
    new_instructions = body.instructions
    baseline_score = body.baseline_score
    new_score = body.new_score

    if not skill_id or not new_instructions:
        raise HTTPException(400, "skill_id and instructions required")

    if new_score <= baseline_score:
        raise HTTPException(400, "New score must be higher than baseline")

    evolver = get_skill_evolver()
    result = evolver.apply_evolution(
        team_id=team_id,
        skill_id=skill_id,
        new_instructions=new_instructions,
    )
    if result.get("error"):
        raise HTTPException(500, result["error"])

    return {
        "status": "applied",
        "skill_id": skill_id,
        "new_version": result.get("version"),
        "score_improvement": f"+{(new_score - baseline_score) * 100:.1f}%",
    }


__all__ = ["router", "set_teams"]
