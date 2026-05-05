# -*- coding: utf-8 -*-
"""智能体广场 API 路由 + SSE 实时推送."""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from .plaza import PRESET_TOPICS, SeatTier, NicheRole
from .plaza_engine import get_plaza_engine

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/plaza", tags=["Plaza"])


# ── Request Models ────────────────────────────────────────

class CreatePlazaRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: str = Field(default="", max_length=500)


class AddParticipantRequest(BaseModel):
    agent_id: str
    agent_name: str = ""
    role: str = ""
    team_id: str = ""
    seat_tier: str = Field(default="middle")
    niche_role: str = Field(default="observer")


class CreateDiscussionRequest(BaseModel):
    topic: str = Field(..., min_length=1, max_length=200)
    description: str = Field(default="", max_length=500)
    goal: str = Field(default="", max_length=500)
    moderator_agent_id: str = ""
    max_rounds: int = Field(default=3, ge=1, le=10)


class SetVisualModeRequest(BaseModel):
    mode: str = Field(default="modern")  # modern | rome_320ad | senedd


# ── 广场 CRUD ──────────────────────────────────────────────

@router.post("", summary="创建广场", status_code=status.HTTP_201_CREATED)
async def create_plaza(req: CreatePlazaRequest) -> Dict[str, Any]:
    engine = get_plaza_engine()
    plaza = engine.create_plaza(req.name, req.description)
    return plaza.to_dict(include_details=True)


@router.get("", summary="列出所有广场")
async def list_plazas() -> List[Dict[str, Any]]:
    engine = get_plaza_engine()
    return [p.to_dict() for p in engine.list_plazas()]


@router.get("/presets", summary="获取预设话题模板")
async def get_preset_topics() -> List[Dict[str, str]]:
    return PRESET_TOPICS


@router.get("/{plaza_id}", summary="获取广场详情")
async def get_plaza(plaza_id: str) -> Dict[str, Any]:
    engine = get_plaza_engine()
    plaza = engine.get_plaza(plaza_id)
    if not plaza:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "广场不存在")
    return plaza.to_dict(include_details=True)


@router.delete("/{plaza_id}", summary="删除广场")
async def delete_plaza(plaza_id: str) -> Dict[str, str]:
    engine = get_plaza_engine()
    if not engine.delete_plaza(plaza_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "广场不存在")
    return {"status": "deleted"}


@router.put("/{plaza_id}/visual-mode", summary="切换视觉模式")
async def set_visual_mode(plaza_id: str, req: SetVisualModeRequest) -> Dict[str, Any]:
    engine = get_plaza_engine()
    plaza = engine.get_plaza(plaza_id)
    if not plaza:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "广场不存在")
    if req.mode not in ("modern", "rome_320ad", "senedd"):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "无效的视觉模式")
    plaza.visual_mode = req.mode
    return {"status": "updated", "visual_mode": plaza.visual_mode}


# ── 参与者管理 ──────────────────────────────────────────────

@router.post("/{plaza_id}/participants", summary="添加参与者", status_code=201)
async def add_participant(plaza_id: str, req: AddParticipantRequest) -> Dict[str, Any]:
    engine = get_plaza_engine()
    try:
        tier = SeatTier(req.seat_tier)
    except ValueError:
        tier = SeatTier.MIDDLE
    try:
        niche = NicheRole(req.niche_role)
    except ValueError:
        niche = NicheRole.OBSERVER
    p = engine.add_participant(
        plaza_id, req.agent_id, req.agent_name, req.role, req.team_id,
        tier, niche,
    )
    if not p:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "广场不存在")
    return p.to_dict()


@router.delete("/{plaza_id}/participants/{agent_id}", summary="移除参与者")
async def remove_participant(plaza_id: str, agent_id: str) -> Dict[str, str]:
    engine = get_plaza_engine()
    if not engine.remove_participant(plaza_id, agent_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "参与者不存在")
    return {"status": "removed"}


@router.post("/{plaza_id}/participants/batch", summary="批量添加参与者", status_code=201)
async def batch_add_participants(
    plaza_id: str, participants: List[AddParticipantRequest]
) -> List[Dict[str, Any]]:
    engine = get_plaza_engine()
    results = []
    for req in participants:
        try:
            tier = SeatTier(req.seat_tier)
        except ValueError:
            tier = SeatTier.MIDDLE
        try:
            niche = NicheRole(req.niche_role)
        except ValueError:
            niche = NicheRole.OBSERVER
        p = engine.add_participant(
            plaza_id, req.agent_id, req.agent_name, req.role, req.team_id,
            tier, niche,
        )
        if p:
            results.append(p.to_dict())
    return results


# ── 讨论管理 ──────────────────────────────────────────────

@router.post("/{plaza_id}/discussions", summary="创建讨论", status_code=201)
async def create_discussion(
    plaza_id: str, req: CreateDiscussionRequest,
) -> Dict[str, Any]:
    engine = get_plaza_engine()
    disc = engine.create_discussion(
        plaza_id, req.topic, req.description,
        req.moderator_agent_id, req.max_rounds,
    )
    if disc:
        disc.goal = req.goal
    if not disc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "广场不存在")
    return disc.to_dict()


@router.get("/{plaza_id}/discussions", summary="列出讨论")
async def list_discussions(plaza_id: str) -> List[Dict[str, Any]]:
    engine = get_plaza_engine()
    return [d.to_dict() for d in engine.list_discussions(plaza_id)]


@router.get("/{plaza_id}/discussions/{disc_id}", summary="获取讨论详情")
async def get_discussion(plaza_id: str, disc_id: str) -> Dict[str, Any]:
    engine = get_plaza_engine()
    disc = engine.get_discussion(plaza_id, disc_id)
    if not disc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "讨论不存在")
    return disc.to_dict(include_messages=True)


@router.get("/{plaza_id}/discussions/{disc_id}/summary", summary="获取讨论总结")
async def get_discussion_summary(plaza_id: str, disc_id: str) -> Dict[str, Any]:
    engine = get_plaza_engine()
    disc = engine.get_discussion(plaza_id, disc_id)
    if not disc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "讨论不存在")
    return {
        "discussion_id": disc.id,
        "topic": disc.topic,
        "status": disc.status.value,
        "summary": disc.summary,
        "key_conclusions": disc.key_conclusions,
        "message_count": len(disc.messages),
        "rounds": disc.current_round,
        "plan": disc.plan,
        "goal": disc.goal,
        "assigned_team_id": disc.assigned_team_id,
    }


@router.delete("/{plaza_id}/discussions/{disc_id}", summary="删除讨论")
async def delete_discussion(plaza_id: str, disc_id: str) -> Dict[str, str]:
    engine = get_plaza_engine()
    if not engine.delete_discussion(plaza_id, disc_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "讨论不存在")
    return {"status": "deleted", "discussion_id": disc_id}


# ── 自动入座 (所有团队智能体) ──────────────────────────────

@router.post("/{plaza_id}/auto-seat", summary="全部智能体自动入座", status_code=200)
async def auto_seat_all_agents(plaza_id: str) -> Dict[str, Any]:
    """从所有团队拉取智能体自动入座广场，按团队分区."""
    engine = get_plaza_engine()
    plaza = engine.get_plaza(plaza_id)
    if not plaza:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "广场不存在")

    # 获取 TeamManager
    try:
        from agents.api import _team_manager
    except ImportError:
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "TeamManager 不可用")

    added = []
    teams = _team_manager.list_teams() if _team_manager else []
    for team in teams:
        agents = team.agents
        if isinstance(agents, dict):
            agents = list(agents.values())
        for a in agents:
            if a.agent_id in plaza.participants:
                continue
            p = engine.add_participant(
                plaza_id, a.agent_id, a.name or a.agent_id,
                a.role or "", team.team_id,
                SeatTier.MIDDLE, NicheRole.OBSERVER,
            )
            if p:
                added.append(p.to_dict())

    return {"added": len(added), "total": len(plaza.participants), "participants": added}


# ── 计划指派给团队 ──────────────────────────────────────────

class AssignPlanRequest(BaseModel):
    team_id: str
    task_name: str = ""
    task_description: str = ""


@router.post("/{plaza_id}/discussions/{disc_id}/assign", summary="将讨论计划指派给团队")
async def assign_plan_to_team(
    plaza_id: str, disc_id: str, req: AssignPlanRequest,
) -> Dict[str, Any]:
    engine = get_plaza_engine()
    disc = engine.get_discussion(plaza_id, disc_id)
    if not disc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "讨论不存在")

    disc.assigned_team_id = req.team_id

    # 尝试创建任务
    try:
        from agents.task_engine import get_task_engine, AgentTask
        te = get_task_engine()
        task_name = req.task_name or f"[广场计划] {disc.topic[:50]}"
        task_desc = req.task_description or disc.summary or disc.topic
        task = AgentTask(
            team_id=req.team_id,
            title=task_name,
            description=task_desc,
            metadata={"source": "plaza", "discussion_id": disc.id, "plaza_id": plaza_id},
        )
        import asyncio
        submitted = await te.submit_task(task)
        return {"status": "assigned", "team_id": req.team_id, "task_id": submitted.task_id}
    except Exception as e:
        logger.warning(f"创建任务失败: {e}")
        return {"status": "assigned_no_task", "team_id": req.team_id, "error": str(e)}


# ── 讨论→任务批量派发 ──────────────────────────────────────

class DispatchTasksRequest(BaseModel):
    team_id: str = Field(..., min_length=1)


@router.post("/{plaza_id}/discussions/{disc_id}/dispatch", summary="从讨论结论自动拆解并派发任务")
async def dispatch_tasks_from_discussion(
    plaza_id: str, disc_id: str, req: DispatchTasksRequest,
) -> Dict[str, Any]:
    """解析讨论总结中的行动计划，为每个步骤创建独立任务并提交到 TaskEngine."""
    engine = get_plaza_engine()
    disc = engine.get_discussion(plaza_id, disc_id)
    if not disc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "讨论不存在")
    if not disc.summary:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "讨论尚无总结，请先完成讨论")

    # 用 LLM 解析总结 → 任务列表
    from .chat_harness import get_chat_harness
    harness = get_chat_harness()
    parse_prompt = (
        "你是任务拆解助手。请分析以下讨论总结，提取可执行的任务列表。\n"
        "严格按照 JSON 数组格式输出，每项包含: title, description, priority (1-3, 1最高)\n"
        "只输出 JSON 数组，不要任何其他文字。\n\n"
        f"讨论话题: {disc.topic}\n\n"
        f"讨论总结:\n{disc.summary}\n"
    )
    try:
        llm_reply = await harness.chat(parse_prompt, system="你是一个任务拆解专家，只输出JSON。")
        # 提取 JSON 数组
        import re
        json_match = re.search(r'\[.*\]', llm_reply, re.DOTALL)
        if not json_match:
            raise ValueError("LLM 未返回有效 JSON 数组")
        tasks_data = json.loads(json_match.group())
    except Exception as e:
        logger.warning(f"LLM 任务拆解失败: {e}，回退为单任务")
        tasks_data = [{
            "title": f"[广场计划] {disc.topic[:50]}",
            "description": disc.summary,
            "priority": 2,
        }]

    # 批量提交任务
    from .task_engine import get_task_engine, AgentTask
    te = get_task_engine()
    created_tasks = []
    for i, td in enumerate(tasks_data[:10]):  # 最多 10 个任务
        task = AgentTask(
            team_id=req.team_id,
            title=str(td.get("title", f"任务 {i+1}"))[:120],
            description=str(td.get("description", ""))[:2000],
            priority=int(td.get("priority", 2)),
            metadata={
                "source": "plaza_dispatch",
                "discussion_id": disc.id,
                "plaza_id": plaza_id,
                "sequence": i,
            },
        )
        await te.submit_task(task)
        created_tasks.append(task.to_dict())

    disc.assigned_team_id = req.team_id
    engine._store.save_plaza(engine._plazas[plaza_id])

    return {
        "status": "dispatched",
        "team_id": req.team_id,
        "task_count": len(created_tasks),
        "tasks": created_tasks,
    }


# ── 启动讨论 + SSE 流 ──────────────────────────────────────

@router.post("/{plaza_id}/discussions/{disc_id}/start", summary="启动讨论")
async def start_discussion(plaza_id: str, disc_id: str) -> Dict[str, Any]:
    engine = get_plaza_engine()
    disc = engine.get_discussion(plaza_id, disc_id)
    if not disc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "讨论不存在")
    if disc.status == "closed":
        disc = engine.reset_discussion(plaza_id, disc_id)
    elif disc.status != "open":
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"讨论状态为 {disc.status}，无法启动")

    # 在后台运行讨论
    asyncio.create_task(engine.run_discussion(plaza_id, disc_id))
    return {"status": "started", "discussion_id": disc_id}


@router.get("/{plaza_id}/discussions/{disc_id}/stream", summary="SSE 实时消息流")
async def stream_discussion(plaza_id: str, disc_id: str):
    """Server-Sent Events 实时推送讨论消息.

    通过穹顶 Oculus 高速数据通道实时传输讨论流。
    """
    engine = get_plaza_engine()
    disc = engine.get_discussion(plaza_id, disc_id)
    if not disc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "讨论不存在")

    q = engine.subscribe(disc_id)

    async def event_stream():
        try:
            # 先推送已有消息（支持中途接入）
            for msg in disc.messages:
                yield f"data: {json.dumps({'type': 'message', 'message': msg.to_dict()}, ensure_ascii=False)}\n\n"

            # 推送当前状态
            yield f"data: {json.dumps({'type': 'status', 'status': disc.status.value}, ensure_ascii=False)}\n\n"

            # 实时推送新消息
            while True:
                try:
                    event = await asyncio.wait_for(q.get(), timeout=30.0)
                    yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
                    if event.get("type") == "discussion_end":
                        break
                except asyncio.TimeoutError:
                    yield f"data: {json.dumps({'type': 'heartbeat'}, ensure_ascii=False)}\n\n"
        finally:
            engine.unsubscribe(disc_id, q)

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


# ══════════════════════════════════════════════════════════════
# 监控与遥测 API
# ══════════════════════════════════════════════════════════════

# 全局监控 Channel 引用（在 main.py startup 时注入）
_plaza_monitor_channel = None


def set_plaza_monitor(channel):
    """注入 PlazaMonitorChannel 实例."""
    global _plaza_monitor_channel
    _plaza_monitor_channel = channel


@router.get("/monitoring/status", summary="获取监控状态")
async def monitoring_status() -> Dict[str, Any]:
    """获取广场监控 Channel 状态."""
    if not _plaza_monitor_channel:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "监控未初始化")
    return _plaza_monitor_channel.get_status()


@router.get("/monitoring/metrics", summary="获取监控指标")
async def monitoring_metrics() -> Dict[str, Any]:
    """获取采集器指标."""
    if not _plaza_monitor_channel:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "监控未初始化")
    return _plaza_monitor_channel.get_metrics()


@router.get("/monitoring/telemetry", summary="获取遥测记录")
async def monitoring_telemetry(limit: int = 100) -> List[Dict[str, Any]]:
    """获取遥测记录，用于 CI/CD 门禁校验."""
    if not _plaza_monitor_channel:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "监控未初始化")
    return _plaza_monitor_channel.get_telemetry(limit=limit)


@router.get("/monitoring/active-discussions", summary="获取活跃讨论")
async def monitoring_active_discussions() -> Dict[str, Any]:
    """获取当前活跃的讨论列表."""
    if not _plaza_monitor_channel:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "监控未初始化")
    return _plaza_monitor_channel.get_active_discussions()


@router.post("/monitoring/degradation", summary="切换降级模式")
async def monitoring_set_degradation(active: bool = True) -> Dict[str, str]:
    """激活或关闭降级模式（全量采集）. """
    if not _plaza_monitor_channel:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "监控未初始化")
    _plaza_monitor_channel.set_degradation_mode(active)
    return {"status": "degradation_activated" if active else "degradation_deactivated"}


@router.post("/monitoring/config", summary="热更新采样策略")
async def monitoring_update_config(config: Dict[str, Any]) -> Dict[str, str]:
    """热更新采样策略配置."""
    if not _plaza_monitor_channel:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "监控未初始化")
    _plaza_monitor_channel.update_sampling_config(config)
    return {"status": "config_updated"}


@router.get("/monitoring/sampler-stats", summary="获取采样器统计")
async def monitoring_sampler_stats() -> Dict[str, Any]:
    """获取自适应采样器统计."""
    if not _plaza_monitor_channel:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "监控未初始化")
    collector = _plaza_monitor_channel.get_collector()
    if not collector:
        return {"error": "collector_not_available"}
    return collector.get_sampler_stats()


@router.post("/monitoring/event", summary="手动上报事件")
async def monitoring_report_event(event: Dict[str, Any]) -> Dict[str, Any]:
    """手动上报一个监控事件."""
    if not _plaza_monitor_channel:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "监控未初始化")
    result = _plaza_monitor_channel.process_event(event)
    if result is None:
        return {"handled": False, "reason": f"未知事件类型: {event.get('type', '')}"}
    return result
