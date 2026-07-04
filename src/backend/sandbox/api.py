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

from fastapi import APIRouter, HTTPException, Query, Request
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


def _sync_team_agents_to_orchestrator(orch: SECSOrchestrator, team_id: str) -> None:
    """DT 无数据时的 fallback：直接从 TeamManager 获取 team agents（含 skills/tools）同步到世界状态."""
    try:
        from agents.api import _tm
        team = _tm().get_team(team_id)
        if not team:
            logger.warning(f"Team {team_id} not found for agent sync fallback")
            return
        agents_list = team.agents
        if isinstance(agents_list, dict):
            agents_list = list(agents_list.values())
        agents = []
        for a in agents_list:
            agents.append({
                "id": getattr(a, "agent_id", ""),
                "name": getattr(a, "name", "") or getattr(a, "agent_id", ""),
                "role": getattr(a, "role", "general"),
                "state": "idle",
                "room": "",
                "skills": getattr(a, "skills", []) or [],
                "tools": getattr(a, "tools", []) or [],
            })
        if agents:
            orch.sync_world(team_id=team_id, agents=agents)
            logger.info(f"🔄 DT fallback: 从 TeamManager 同步 {len(agents)} agents (team={team_id})")
    except Exception as e:
        logger.warning(f"Team agent sync fallback failed: {e}")


def _inject_external_skill_to_session(session, skill_id: str, team_id: str) -> Dict[str, Any]:
    """从 skill-router 的 skill 库取出 skill 文档，注入到 sandbox session 作为初始 SOP / 经验。

    返回注入摘要（skill_id / name / 注入到哪一层），不抛异常。
    """
    try:
        from agents.skill_router import get_skill_router
        sr = get_skill_router()
        if not sr or not sr._skill_library:
            return {"skill_id": skill_id, "injected": False, "reason": "skill_library_unavailable"}
        skills = sr._skill_library.browse(team_id=team_id or "")
        skill = next((s for s in skills if (s.get("skill_id") == skill_id or s.get("id") == skill_id)), None)
        if not skill:
            return {"skill_id": skill_id, "injected": False, "reason": "skill_not_found"}
        # Inject into the underlying TwinLoop session
        from .models import CollaborationSOP, StrategyStatus
        sop = CollaborationSOP(
            sop_id=f"ext_{skill_id}",
            name=f"[演化自 {skill.get('name', skill_id)}] {skill.get('summary','')[:80]}",
            description=(
                f"[source_skill_id={skill_id} · team_id={team_id}]\n"
                + (skill.get("summary") or skill.get("description") or "")
            ),
            avg_reward=0.0,
            steps=skill.get("steps", []) or [],
            status=StrategyStatus.CANDIDATE,
        )
        # Place at the head of the SOP library so evolutionary mode sees it as seed
        orch = get_orchestrator()
        orch.zero_exp._sop_library.insert(0, sop)
        # Also drop a memory entry so the twin loop has a starting point
        try:
            from .models import ExperienceEntry, ExperienceOutcome
            entry = ExperienceEntry(
                agent_id=f"skill:{skill_id}",
                context={"source": "skill_injection", "team_id": team_id},
                action="inject_skill",
                reward=0.0,
                outcome=ExperienceOutcome.NEUTRAL,
                notes=f"Injected from skill library: {skill.get('name', skill_id)}",
            )
            orch.memory_pool.add_experience(entry)
        except Exception as _e:
            logger.debug("memory seed skipped: %s", _e)
        return {
            "skill_id": skill_id,
            "skill_name": skill.get("name", skill_id),
            "injected": True,
            "sop_id": sop.sop_id,
            "summary": sop.description,
        }
    except Exception as e:
        logger.warning(f"外部 skill 注入失败: {e}")
        return {"skill_id": skill_id, "injected": False, "reason": str(e)}


# ── Request/Response Models ─────────────────────────────────


class CreateSessionRequest(BaseModel):
    team_id: str = "default"
    mode: str = Field(default="what_if", description="what_if | parallel | evolutionary")
    max_steps: int = Field(default=150, ge=10, le=500)
    speed_factor: float = Field(default=10.0, ge=1.0, le=100.0)
    parallel_branches: int = Field(default=3, ge=1, le=10)
    trigger_description: str = ""
    use_llm: bool = Field(default=False, description="启用 LLM 驱动的智能体决策")
    sync_dt: bool = Field(default=True, description="创建时自动从数字孪生同步场景")
    initial_skill_id: Optional[str] = Field(
        default=None,
        description="从技能库注入的初始 skill（用于演化训练场景）",
    )


class InjectRequest(BaseModel):
    confirm: bool = True
    type: Optional[str] = None          # chaos事件类型: agent_failure / task_mutation / agent_leave / agent_join / skill_inject
    target_agent: Optional[str] = None  # 目标agent_id (可选, 不指定则随机)
    skill_id: Optional[str] = None      # 技能注入时的 skill_id
    timestamp: Optional[int] = None     # 前端时间戳


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
        # DT 无数据时，从 TeamManager 直接同步 agents（含 skills/tools）
        if not dt_sync.get("synced_agents") and not dt_sync.get("error"):
            _sync_team_agents_to_orchestrator(orch, req.team_id)

    session = orch.create_session(
        team_id=req.team_id,
        mode=mode,
        max_steps=req.max_steps,
        speed_factor=req.speed_factor,
        parallel_branches=req.parallel_branches,
        trigger_description=req.trigger_description,
        use_llm=req.use_llm,
    )

    # 注入外部 skill 作为初始策略来源（用于演化训练）
    injected_skill = None
    if req.initial_skill_id:
        try:
            injected_skill = _inject_external_skill_to_session(
                session, req.initial_skill_id, req.team_id
            )
        except Exception as e:
            logger.warning(f"注入外部 skill 失败: {e}")

    return {
        "session_id": session.session_id,
        "status": session.status.value,
        "mode": session.mode.value,
        "created_at": session.created_at,
        "use_llm": req.use_llm,
        "dt_sync": dt_sync,
        "initial_skill": injected_skill,
    }


@router.post("/sync-from-dt")
async def sync_from_digital_twin(
    scenario_id: str = Query(default=""),
) -> Dict[str, Any]:
    """从数字孪生同步当前场景到 SECS 世界状态。
    
    C-4.2: 可选 scenario_id — 当传入时携带场景房间配置，
    世界状态同步时以场景房间为准。
    """
    orch = get_orchestrator()
    result = _sync_dt_to_orchestrator(orch)
    if scenario_id:
        try:
            from .scenario_store import get_scenario_store
            store = get_scenario_store()
            spec = store.get(scenario_id)
            if spec and spec.get("world") and spec["world"].get("rooms"):
                result["scenario_id"] = scenario_id
                result["scenario_rooms"] = len(spec["world"]["rooms"])
                # 场景房间覆写 world_state 的房间列表
                orch.world_state.set_room_stages([
                    {"room_id": r.get("room_id", r.get("id")), "stage": r.get("stage", 0)}
                    for r in spec["world"]["rooms"]
                ])
                logger.info(f"sync-from-dt: scenario={scenario_id} rooms={len(spec['world']['rooms'])}")
        except Exception as e:
            logger.warning(f"sync-from-dt scenario load failed: {e}")
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
    """获取沙箱会话详情.

    容错设计: 即使评分/SOP 尚未生成或数据不完整，
    也返回可渲染的 session 基础数据，绝不返回 500。
    """
    orch = get_orchestrator()
    session = orch.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # ── 外层容错: 整个序列化过程不被任何内部异常中断 ──
    try:
        # 构建步骤摘要（含 skill 使用信息，供前端报告用）
        steps_summary = []
        for step in session.steps:
            skills_used = {}
            for twin_id, action in step.agent_actions.items():
                # [P0-fix] 防御: action 可能是 None 或非 dict
                if not isinstance(action, dict):
                    continue
                sk = action.get("skill_used")
                tk = action.get("tool_used")
                if sk:
                    skills_used[twin_id] = {"skill": sk, "tool": tk, "action": action.get("action", "")}
            steps_summary.append({
                "step_id": step.step_id,
                "global_reward": round(step.global_reward, 4),
                "skills_used": skills_used,
                "messages_count": len(step.messages),
            })

        evaluation_data = None
        if session.evaluation:
            evaluation_data = {
                "global_score": session.evaluation.global_score,
                "task_completion": session.evaluation.task_completion,
                "communication_efficiency": session.evaluation.communication_efficiency,
                "resource_utilization": session.evaluation.resource_utilization,
                "conflict_avoidance": session.evaluation.conflict_avoidance,
                "convergence_speed": session.evaluation.convergence_speed,
                "recommendations": session.evaluation.recommendations,
            }

        sop_data = None
        if session.best_sop:
            sop_data = {
                "sop_id": session.best_sop.sop_id,
                "name": session.best_sop.name,
                "avg_reward": session.best_sop.avg_reward,
                "status": session.best_sop.status.value,
            }

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
            "twins": [
                {"twin_id": t.twin_id, "source_agent_id": t.source_agent_id,
                 "role": t.role, "skills": t.skills, "tools": t.tools,
                 "actions_taken": t.actions_taken, "rewards_collected": round(t.rewards_collected, 4)}
                for t in session.twins
            ],
            "steps_summary": steps_summary,
            "evaluation": evaluation_data,
            "best_sop": sop_data,
            "injected": session.injected,
        }
    except Exception as e:
        # [P5-fix] 兜底: 任何序列化异常都返回基础数据，而非 500
        logger.warning(f"get_session 序列化异常 (降级返回): {e}", exc_info=True)
        return {
            "session_id": session.session_id,
            "status": session.status.value,
            "mode": getattr(session.mode, 'value', 'unknown'),
            "total_steps_executed": session.total_steps_executed,
            "twins_count": len(getattr(session, 'twins', []) or []),
            "steps_summary": [],
            "evaluation": None,
            "best_sop": None,
            "_degraded": True,
            "_error": str(e),
        }


@router.post("/sessions/{session_id}/run")
async def run_simulation(session_id: str) -> Dict[str, Any]:
    """启动仿真执行."""
    orch = get_orchestrator()
    session = orch.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.status not in (SandboxStatus.CREATED, SandboxStatus.PAUSED, SandboxStatus.COMPLETED):
        raise HTTPException(
            status_code=400,
            detail=f"Cannot run session in status: {session.status.value}"
        )

    # 异步执行仿真
    result = await orch.run_full_pipeline(session_id)
    return result


@router.post("/sessions/{session_id}/stop")
async def stop_simulation(session_id: str) -> Dict[str, Any]:
    """停止正在运行的仿真."""
    orch = get_orchestrator()
    session = orch.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    result = orch.stop_simulation(session_id)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.post("/sessions/{session_id}/step")
async def step_simulation(session_id: str) -> Dict[str, Any]:
    """单步执行仿真（PAUSED 状态下可用）."""
    orch = get_orchestrator()
    session = orch.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    result = await orch.step_once(session_id)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.post("/sessions/{session_id}/pause")
async def pause_session(session_id: str) -> Dict[str, Any]:
    """暂停仿真（等同于停止，保留状态供单步续跑）.
    
    支持 CREATED/RUNNING 状态：CREATED 时仅标记为 PAUSED（就绪→可单步）。
    """
    orch = get_orchestrator()
    session = orch.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    # 就绪态(CREATED)：直接标记为PAUSED即可
    if session.status in (SandboxStatus.CREATED,):
        session.status = SandboxStatus.PAUSED
        return {"paused": True, "status": "paused", "session_id": session_id}
    result = orch.stop_simulation(session_id)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.post("/sessions/force-reset", summary="强制清理所有会话资源")
async def force_reset_sessions() -> Dict[str, Any]:
    """强制清理僵尸会话、stop_events、信号量.

    在 parallel 模式崩溃后调用，重置 Sandbox 沙箱环境到干净状态。
    """
    orch = get_orchestrator()
    return orch.twin_loop.force_reset_all()


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

        # Helper: 构建 agent 的 skill 使用信息
        def _build_agent_skill_map(agent_actions_dict):
            return {
                k: {"action": v.get("action", "unknown"), "skill": v.get("skill_used"), "tool": v.get("tool_used")}
                for k, v in agent_actions_dict.items() if isinstance(v, dict)
            }

        # 发送已有步骤
        for step in session.steps:
            event_data = {
                "type": "step",
                "step_id": step.step_id,
                "global_reward": step.global_reward,
                "agent_actions": {k: v.get("action", "unknown") for k, v in step.agent_actions.items()},
                "agent_skills": _build_agent_skill_map(step.agent_actions),
                "messages_count": len(step.messages),
                "total_steps": session.max_steps,
                "agent_roles": {t.source_agent_id: t.role for t in (session.twins or [])},
                # twin_id → 真身 agent_id 映射：前端(协作图/办公室3D)据此把孪生副本对齐回真身
                "twin_agents": {t.twin_id: t.source_agent_id for t in (session.twins or [])},
            }
            yield f"data: {json.dumps(event_data)}\n\n"

        # 等待仿真启动并持续流式输出（CREATED→RUNNING 状态转换）
        last_step_count = len(session.steps)
        # 就绪态(CREATED)：等待用户操作（自动运行/单步），不退出循环
        # 运行态(RUNNING)：轮询新步骤
        while session.status in (SandboxStatus.CREATED, SandboxStatus.RUNNING, SandboxStatus.PAUSED):
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
                        "agent_skills": _build_agent_skill_map(step.agent_actions),
                        "messages_count": len(step.messages),
                        "total_steps": session.max_steps,
                        "agent_roles": {t.source_agent_id: t.role for t in (session.twins or [])},
                        # twin_id → 真身 agent_id 映射：前端(协作图/办公室3D)据此把孪生副本对齐回真身
                        "twin_agents": {t.twin_id: t.source_agent_id for t in (session.twins or [])},
                    }
                    yield f"data: {json.dumps(event_data)}\n\n"
                last_step_count = current_count
            await asyncio.sleep(0.15)

        # 仅在有实际执行过步骤时才发送完成事件（避免就绪态误报完成）
        if session.total_steps_executed > 0 or session.status in (SandboxStatus.COMPLETED, SandboxStatus.EVALUATING):
            final_data = {
                "type": "complete",
                "session_id": session_id,
                "status": session.status.value,
                "total_steps": session.total_steps_executed,
                "total_steps_planned": session.max_steps,
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
    """将最优策略注入真实环境 或 混沌事件注入沙箱."""
    if not req.confirm:
        raise HTTPException(status_code=400, detail="Injection requires confirmation")

    orch = get_orchestrator()

    # ── 混沌事件注入（仿真运行中）──
    _chaos_types = {"agent_failure", "failure", "task_mutation", "task_change", "agent_leave", "agent_join",
                    "network_delay", "skill_degraded", "model_hallucination", "logic_deadlock"}
    if req.type and req.type in _chaos_types:
        # 类型映射：前端简称 → 后端标准名
        _type_map = {"failure": "agent_failure", "task_change": "task_mutation"}
        mapped_type = _type_map.get(req.type, req.type)
        result = await orch.inject_chaos_event(
            session_id=session_id,
            event_type=mapped_type,
            target_agent=req.target_agent,
            skill_id=req.skill_id,
        )
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        return result

    # ── 技能注入（仿真运行中）──
    if req.type == "skill_inject" or req.skill_id:
        result = await orch.inject_chaos_event(
            session_id=session_id,
            event_type="skill_inject",
            skill_id=req.skill_id,
        )
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        return result

    # ── 策略注入（仿真完成后）──
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
