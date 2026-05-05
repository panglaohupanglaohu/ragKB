# -*- coding: utf-8 -*-
"""
Agent Team API Routes - 双团队管理 REST API

提供构建团队 & 执行团队的状态查询、KPI 考核、
任务分配、报告查询等端点。挂载至 FastAPI 的 router。
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Any, Dict, List, Optional

router = APIRouter(prefix="/api/v1/agent-teams", tags=["Agent Teams"])


# ---------------------------------------------------------------------------
# 全局引用（在 main.py startup 时注入）
# ---------------------------------------------------------------------------
_build_team = None
_execution_team = None
_scheduler = None
_evolution_engine = None


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

class FeedbackSubmission(BaseModel):
    category: str = "optimization"
    severity: str = "medium"
    title: str
    detail: str


# ---------------------------------------------------------------------------
# Scheduler
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
async def build_reports(limit: int = 10):
    if not _build_team:
        raise HTTPException(503, "Build team not initialized")
    reports = _build_team.hourly_reports[-limit:]
    return [r.to_dict() for r in reports]


@router.get("/build/issues")
async def build_issues():
    if not _build_team:
        raise HTTPException(503, "Build team not initialized")
    return _build_team.issue_backlog


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
async def execution_reports(limit: int = 10):
    if not _execution_team:
        raise HTTPException(503, "Execution team not initialized")
    reports = _execution_team.execution_reports[-limit:]
    return [r.to_dict() for r in reports]


@router.get("/execution/feedback")
async def execution_feedback():
    if not _execution_team:
        raise HTTPException(503, "Execution team not initialized")
    return [item.to_dict() for item in _execution_team.feedback_queue]


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
async def teams_overview():
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
        result["evolution"] = _evolution_engine.get_status()
    return result


# ---------------------------------------------------------------------------
# System Evolution (自我演进引擎)
# ---------------------------------------------------------------------------

@router.get("/evolution/status")
async def evolution_status():
    """获取自我演进引擎状态。"""
    if not _evolution_engine:
        raise HTTPException(404, "Evolution engine not registered")
    return _evolution_engine.get_status()


@router.get("/evolution/summary")
async def evolution_summary():
    """获取演进项汇总。"""
    if not _evolution_engine:
        raise HTTPException(404, "Evolution engine not registered")
    return _evolution_engine.get_evolution_summary()


@router.get("/evolution/items")
async def evolution_items(status: Optional[str] = None):
    """获取演进项列表，可按状态过滤。"""
    if not _evolution_engine:
        raise HTTPException(404, "Evolution engine not registered")
    return _evolution_engine.get_evolution_items(status=status)


@router.get("/evolution/rules")
async def evolution_rules():
    """获取审查规则列表。"""
    if not _evolution_engine:
        raise HTTPException(404, "Evolution engine not registered")
    return [r.to_dict() for r in _evolution_engine.audit_rules]


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
    return item.to_dict()


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
async def evolution_mark_complete(item_id: str):
    """标记演进项构建完成，进入待验证。"""
    if not _evolution_engine:
        raise HTTPException(404, "Evolution engine not registered")
    ok = _evolution_engine.mark_build_complete(item_id)
    if not ok:
        raise HTTPException(404, f"Item '{item_id}' not found")
    return {"status": "ok", "item_id": item_id, "new_status": "verify_pending"}


@router.post("/evolution/close-verified")
async def evolution_close_verified():
    """关闭所有已验证通过的演进项。"""
    if not _evolution_engine:
        raise HTTPException(404, "Evolution engine not registered")
    closed = _evolution_engine.close_verified()
    return {"closed": closed, "count": len(closed)}


@router.get("/evolution/history")
async def evolution_audit_history():
    """获取审查历史记录。"""
    if not _evolution_engine:
        raise HTTPException(404, "Evolution engine not registered")
    return _evolution_engine.get_audit_history()


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
    return _evolution_engine.get_compliance_rating()


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
    return {
        "active_zones": _evolution_engine.get_active_zones(),
        "activated_rules": _evolution_engine.get_zone_activated_rules(),
        "vessel_position": _evolution_engine._vessel_position,
    }


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
    return _evolution_engine.get_trend_analysis()


@router.get("/evolution/monitoring")
async def evolution_monitoring():
    """获取连续监控状态。"""
    if not _evolution_engine:
        raise HTTPException(404, "Evolution engine not registered")
    return _evolution_engine.get_monitoring_status()


@router.get("/evolution/audit-trail")
async def evolution_audit_trail(event_type: Optional[str] = None, limit: int = 50):
    """获取审计轨迹日志。"""
    if not _evolution_engine:
        raise HTTPException(404, "Evolution engine not registered")
    return _evolution_engine.get_audit_trail(event_type=event_type, limit=limit)


__all__ = ["router", "set_teams"]
