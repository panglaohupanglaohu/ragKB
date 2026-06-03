# -*- coding: utf-8 -*-
"""Sandbox API — FastAPI 路由 + SSE 实时流.

提供 SECS 系统的 HTTP API 接口:
- 沙箱会话 CRUD
- 仿真执行控制
- 实时仿真流 (SSE)
- 策略注入
- 全局统计
"""

from __future__ import annotations

import asyncio
import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from .models import SimulationMode, SandboxStatus
from .orchestrator import SECSOrchestrator
from .python_runner import describe_sandbox_runtime, get_sandbox, record_sandbox_self_check

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/sandbox", tags=["sandbox"])

# 全局编排器实例（在 main.py 中初始化注入）
_orchestrator: Optional[SECSOrchestrator] = None


def set_orchestrator(orch: SECSOrchestrator) -> None:
    """设置全局编排器实例."""
    global _orchestrator
    _orchestrator = orch


def get_orchestrator() -> SECSOrchestrator:
    """获取编排器实例."""
    if _orchestrator is None:
        raise HTTPException(status_code=503, detail="SECS orchestrator not initialized")
    return _orchestrator


# ── Helper: DT→SECS bridge ──────────────────────────────────


def _sync_dt_to_orchestrator(orch: SECSOrchestrator) -> Dict[str, Any]:
    """从数字孪生 _dt_state 同步到 SECS."""
    try:
        from agents.api import _dt_state
        return orch.sync_from_digital_twin(_dt_state)
    except Exception as e:
        logger.warning(f"DT 同步失败: {e}")
        return {"synced_agents": 0, "synced_rooms": 0, "synced_edges": 0, "error": str(e)}


# ── Request/Response Models ─────────────────────────────────


class CreateSessionRequest(BaseModel):
    team_id: str = "default"
    mode: str = Field(default="what_if", description="what_if | parallel | evolutionary")
    max_steps: int = Field(default=50, ge=10, le=500)
    speed_factor: float = Field(default=10.0, ge=1.0, le=100.0)
    parallel_branches: int = Field(default=3, ge=1, le=10)
    trigger_description: str = ""
    use_llm: bool = Field(default=False, description="启用 LLM 驱动的智能体决策")
    sync_dt: bool = Field(default=True, description="创建时自动从数字孪生同步场景")


class InjectRequest(BaseModel):
    confirm: bool = True


class SyncWorldRequest(BaseModel):
    team_id: str = "default"
    agents: list = Field(default_factory=list)
    resources: list = Field(default_factory=list)
    tasks: list = Field(default_factory=list)
    constraints: list = Field(default_factory=list)
    workflow_edges: list = Field(default_factory=list)


# ── API Endpoints ───────────────────────────────────────────


@router.post("/sessions")
async def create_session(req: CreateSessionRequest) -> Dict[str, Any]:
    """创建新的沙箱仿真会话."""
    orch = get_orchestrator()

    try:
        mode = SimulationMode(req.mode)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid mode: {req.mode}")

    # 自动从数字孪生同步当前场景
    dt_sync = None
    if req.sync_dt:
        dt_sync = _sync_dt_to_orchestrator(orch)

    session = orch.create_session(
        team_id=req.team_id,
        mode=mode,
        max_steps=req.max_steps,
        speed_factor=req.speed_factor,
        parallel_branches=req.parallel_branches,
        trigger_description=req.trigger_description,
        use_llm=req.use_llm,
    )

    return {
        "session_id": session.session_id,
        "status": session.status.value,
        "mode": session.mode.value,
        "created_at": session.created_at,
        "use_llm": req.use_llm,
        "dt_sync": dt_sync,
    }


@router.post("/sync-from-dt")
async def sync_from_digital_twin() -> Dict[str, Any]:
    """从数字孪生同步当前场景到 SECS 世界状态."""
    orch = get_orchestrator()
    result = _sync_dt_to_orchestrator(orch)
    return {"status": "synced", **result}


@router.post("/llm-mode")
async def set_llm_mode(enabled: bool = True) -> Dict[str, Any]:
    """全局切换 LLM 决策模式."""
    orch = get_orchestrator()
    orch.set_llm_mode(enabled)
    return {"llm_mode": enabled}


@router.get("/runtime-status")
async def get_runtime_status() -> Dict[str, Any]:
    """Return python/pytest sandbox runtime readiness."""
    return describe_sandbox_runtime()


@router.post("/runtime-self-check")
async def run_runtime_self_check() -> Dict[str, Any]:
    """Run a minimal end-to-end self-check through the configured sandbox runtime."""
    runtime = describe_sandbox_runtime()
    if runtime.get("mode") == "docker" and not runtime.get("ready"):
        blocked_reason = runtime.get("ready_reason") or "docker sandbox is not ready"
        payload = {
            "ok": False,
            "blocked": True,
            "blocked_reason": blocked_reason,
            "runtime": runtime,
            "checks": {
                "python": {
                    "ok": False,
                    "skipped": True,
                    "error": blocked_reason,
                },
                "pytest_collect": {
                    "ok": False,
                    "skipped": True,
                    "error": blocked_reason,
                },
            },
        }
        record_sandbox_self_check(payload)
        return payload

    sandbox = get_sandbox()
    repo_root = Path(__file__).resolve().parents[3]
    python_result = sandbox.run_python("print('sandbox-ok')", cwd=repo_root, timeout=5)
    pytest_result = sandbox.run_pytest("src/backend/tests/test_sandbox_smoke.py", cwd=repo_root, timeout=20)
    checks = {
        "python": python_result.to_dict(),
        "pytest_collect": pytest_result.to_dict(),
    }
    ok = bool(python_result.ok and pytest_result.ok and pytest_result.exit_code == 0)
    payload = {
        "ok": ok,
        "runtime": runtime,
        "checks": checks,
    }
    record_sandbox_self_check(payload)
    return payload


@router.get("/sessions")
async def list_sessions() -> Dict[str, Any]:
    """列出所有沙箱会话."""
    orch = get_orchestrator()
    return {"sessions": orch.list_sessions()}


@router.get("/sessions/{session_id}")
async def get_session(session_id: str) -> Dict[str, Any]:
    """获取沙箱会话详情."""
    orch = get_orchestrator()
    session = orch.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    return {
        "session_id": session.session_id,
        "status": session.status.value,
        "mode": session.mode.value,
        "team_id": session.team_id,
        "max_steps": session.max_steps,
        "total_steps_executed": session.total_steps_executed,
        "twins_count": len(session.twins),
        "created_at": session.created_at,
        "updated_at": session.updated_at,
        "evaluation": {
            "global_score": session.evaluation.global_score,
            "task_completion": session.evaluation.task_completion,
            "communication_efficiency": session.evaluation.communication_efficiency,
            "resource_utilization": session.evaluation.resource_utilization,
            "conflict_avoidance": session.evaluation.conflict_avoidance,
            "convergence_speed": session.evaluation.convergence_speed,
            "recommendations": session.evaluation.recommendations,
        } if session.evaluation else None,
        "best_sop": {
            "sop_id": session.best_sop.sop_id,
            "name": session.best_sop.name,
            "avg_reward": session.best_sop.avg_reward,
            "status": session.best_sop.status.value,
        } if session.best_sop else None,
        "injected": session.injected,
    }


@router.post("/sessions/{session_id}/run")
async def run_simulation(session_id: str) -> Dict[str, Any]:
    """启动仿真执行."""
    orch = get_orchestrator()
    session = orch.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.status not in (SandboxStatus.CREATED, SandboxStatus.PAUSED):
        raise HTTPException(
            status_code=400,
            detail=f"Cannot run session in status: {session.status.value}"
        )

    # 异步执行仿真
    result = await orch.run_full_pipeline(session_id)
    return result


@router.get("/sessions/{session_id}/stream")
async def stream_simulation(session_id: str, request: Request) -> StreamingResponse:
    """SSE 实时仿真流."""
    orch = get_orchestrator()
    session = orch.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    async def event_generator():
        """生成 SSE 事件流."""
        # 发送当前状态
        yield f"data: {json.dumps({'type': 'status', 'status': session.status.value})}\n\n"

        # 发送已有步骤
        for step in session.steps:
            event_data = {
                "type": "step",
                "step_id": step.step_id,
                "global_reward": step.global_reward,
                "agent_actions": {k: v.get("action", "unknown") for k, v in step.agent_actions.items()},
                "messages_count": len(step.messages),
            }
            yield f"data: {json.dumps(event_data)}\n\n"

        # 如果仿真进行中，持续流式输出
        last_step_count = len(session.steps)
        while session.status == SandboxStatus.RUNNING:
            if await request.is_disconnected():
                break
            # 检查新步骤
            current_count = len(session.steps)
            if current_count > last_step_count:
                for step in session.steps[last_step_count:]:
                    event_data = {
                        "type": "step",
                        "step_id": step.step_id,
                        "global_reward": step.global_reward,
                        "agent_actions": {k: v.get("action", "unknown") for k, v in step.agent_actions.items()},
                        "messages_count": len(step.messages),
                    }
                    yield f"data: {json.dumps(event_data)}\n\n"
                last_step_count = current_count
            await asyncio.sleep(0.1)

        # 发送完成事件
        final_data = {
            "type": "complete",
            "status": session.status.value,
            "total_steps": session.total_steps_executed,
            "evaluation": session.evaluation.global_score if session.evaluation else None,
        }
        yield f"data: {json.dumps(final_data)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/sessions/{session_id}/inject")
async def inject_strategy(session_id: str, req: InjectRequest) -> Dict[str, Any]:
    """将最优策略注入真实环境."""
    if not req.confirm:
        raise HTTPException(status_code=400, detail="Injection requires confirmation")

    orch = get_orchestrator()
    result = await orch.inject_strategy(session_id)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.post("/world/sync")
async def sync_world_state(req: SyncWorldRequest) -> Dict[str, Any]:
    """同步世界状态到沙箱引擎."""
    orch = get_orchestrator()
    orch.sync_world(
        team_id=req.team_id,
        agents=req.agents,
        resources=req.resources,
        tasks=req.tasks,
        constraints=req.constraints,
        workflow_edges=req.workflow_edges,
    )
    return {"synced": True, "world_state": orch.get_world_summary()}


@router.get("/stats")
async def get_stats() -> Dict[str, Any]:
    """获取 SECS 系统全局统计."""
    orch = get_orchestrator()
    return orch.get_global_stats()


@router.get("/drift/history")
async def get_drift_history() -> Dict[str, Any]:
    """获取环境偏移历史."""
    orch = get_orchestrator()
    return {"drifts": orch.get_drift_history()}


@router.get("/sops")
async def get_sop_library() -> Dict[str, Any]:
    """获取 SOP 库."""
    orch = get_orchestrator()
    return {"sops": orch.get_sop_library()}


@router.get("/memory/{agent_id}")
async def get_agent_memory(agent_id: str) -> Dict[str, Any]:
    """获取智能体记忆统计."""
    orch = get_orchestrator()
    return orch.get_agent_memory_stats(agent_id)
